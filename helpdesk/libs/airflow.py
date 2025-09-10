import time
import json
import logging
from urllib.parse import quote

import requests
from airflow_client.client import ApiClient, Configuration
from airflow_client.client.api import DAGApi, DagRunApi, TaskInstanceApi
from airflow_client.client.models.trigger_dag_run_post_body import TriggerDAGRunPostBody

from pydantic import BaseModel

from helpdesk.config import AIRFLOW_SERVER_URL, AIRFLOW_JWT_EXPIRATION_TIME
from helpdesk.libs.decorators import timed_cache

logger = logging.getLogger(__name__)


# What we expect back from auth/token
class AirflowAccessTokenResponse(BaseModel):
    access_token: str
    expire_at_ts: float


class AirflowClientException(Exception):
    pass


class AirflowClientDagsException(AirflowClientException):
    pass


class AirflowClientDagSchemaException(AirflowClientException):
    pass


class AirflowClientTriggerDagException(AirflowClientException):
    pass


class AirflowClientTaskResultException(AirflowClientException):
    pass


class AirflowClientDagResultException(AirflowClientException):
    pass


class AirflowClientGetUserRolesException(AirflowClientException):
    pass


class AirflowClient:
    def __init__(
            self, username=None, passwd=None,
            server_url=AIRFLOW_SERVER_URL,
            jwt_expire_seconds=AIRFLOW_JWT_EXPIRATION_TIME):
        self.server_url = server_url
        self.airflow_jwt_expire_seconds = jwt_expire_seconds
        self.expire_at_ts = self._gen_expire_at_ts(self.airflow_jwt_expire_seconds)
        self.username = username
        self.password = passwd
        self.api_client = None

    def get_api_client(self):
        if self.api_client is None or time.time() > self.expire_at_ts:
            self.expire_at_ts = self._gen_expire_at_ts(self.airflow_jwt_expire_seconds)
            token = self.generate_token()
            conf = Configuration(
                host=self.server_url,
                access_token=token.access_token
            )

            if self.api_client is not None:
                self.api_client.__exit__(None, None, None)

            self.api_client = ApiClient(configuration=conf)
            self.expire_at_ts = token.expire_at_ts

        return self.api_client

    def generate_token(self):
        expire_at_ts = self._gen_expire_at_ts(self.airflow_jwt_expire_seconds)
        resp = requests.post(
            '{}/auth/token'.format(self.server_url),
            json={
                "username": self.username,
                "password": self.password
            }
        )
        resp.raise_for_status()
        if resp.status_code == 201:
            result = resp.json()
            result['expire_at_ts'] = expire_at_ts
            return AirflowAccessTokenResponse(**result)
        raise Exception('get token by username/passwd error: {}'.format(resp.json()))

    @staticmethod
    def _gen_expire_at_ts(seconds=86400):
        return time.time() + seconds

    def get_dags(self, tags=('helpdesk',)):
        dag_api = DAGApi(self.get_api_client())
        return dag_api.get_dags(tags=list(tags), tags_match_mode='all')

    def get_schema_by_dag_id(self, dag_id):
        dag_api = DAGApi(self.get_api_client())
        return dag_api.get_dag_details(dag_id)

    def trigger_dag(self, dag_id, conf=None, extra_info=None):
        dag_run_api = DagRunApi(self.get_api_client())
        return dag_run_api.trigger_dag_run(dag_id, TriggerDAGRunPostBody(conf=conf, note=extra_info))

    def get_dag_result(self, dag_id: str, dag_run_id: str):
        dag_run_api = DagRunApi(self.get_api_client())
        dag_run_status = dag_run_api.get_dag_run(
            dag_id, dag_run_id
        )

        task_instance_api = TaskInstanceApi(self.get_api_client())
        dag_instances = task_instance_api.get_task_instances(dag_id, dag_run_id)

        return dag_run_status, dag_instances

    def get_task_log(self, dag_id, dag_run_id, task_id, try_number):
        task_instance_api = TaskInstanceApi(self.get_api_client())
        return task_instance_api.get_log_without_preload_content(
            dag_id, dag_run_id, task_id, try_number
        )

    def get_dag_graph(self, dag_id: str, version: int = 1):
        api_client = self.get_api_client()
        graph_def_resp = api_client.call_api(
            "GET",
            f"{api_client.configuration.host}/ui/structure/structure_data?dag_id={dag_id}&external_dependencies=false&version_number={version}",
            header_params={"Authorization": f"Bearer {api_client.configuration.access_token}"}
        )
        if graph_def_resp.status != 200:
            logger.error("get dag_id %s graph info version %d err: %s", dag_id, version, graph_def_resp.read())
            return {}
        else:
            return json.loads(graph_def_resp.read())

    def build_graph_url(self, dag_id, dag_run_id):
        return f'{self.server_url}/dags/{dag_id}/runs/{dag_run_id}'
