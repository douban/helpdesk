import time
import datetime
import json
import logging
import uuid
from functools import wraps
from urllib.parse import quote

import requests

from app.config import AIRFLOW_SERVER_URL
from app.libs.decorators import timed_cache

logger = logging.getLogger(__name__)


def auto_refresh_token(func):
    @wraps(func)
    def refresh_token(*args, **kwargs):
        cls_self = args[0]
        assert isinstance(cls_self, AirflowClient), \
            'This wrapper can only be apply to AirflowClient method, got: {}'.format(type(cls_self))
        if time.time() > cls_self.expire_time:
            cls_self.refresh_access_token()
        return func(*args, **kwargs)

    return refresh_token


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
    def __init__(self, refresh_token=None, username=None, passwd=None, server_url=AIRFLOW_SERVER_URL):
        self.server_url = server_url
        self.expire_time = self._gen_expire_time()
        if refresh_token:
            self._refresh_token = refresh_token
            self._access_token = self.refresh_access_token()
        elif username and passwd:
            resp = self.generate_token(username, passwd)
            self._refresh_token = resp['refresh_token']
            self._access_token = resp['access_token']
        else:
            raise AirflowClientException('Need one of refresh_token or (username/passwd) as init params at least!')

    def refresh_access_token(self):
        expire_time = self._gen_expire_time()
        access_token_refresh = requests.post(
            url='{}/api/v1/security/refresh'.format(self.server_url),
            headers={'Authorization': 'Bearer {}'.format(self._refresh_token)})
        access_token_refresh.raise_for_status()
        if access_token_refresh.status_code == 200:
            access_token = access_token_refresh.json()['access_token']
            self._access_token = access_token
            self.expire_time = expire_time
            return access_token
        raise Exception('refresh token error: {}'.format(access_token_refresh.json()))

    def generate_token(self, username, passwd):
        now = datetime.datetime.now()
        expire_time = now + datetime.timedelta(days=30)
        resp = requests.post(
            '{}/api/v1/security/login'.format(self.server_url),
            json={
                "username": username,
                "password": passwd,
                "refresh": True,
                "provider": "ldap"
            })
        resp.raise_for_status()
        if resp.status_code == 200:
            result = resp.json()
            result['expire_time'] = expire_time.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
            return result
        raise Exception('get token by username/passwd error: {}'.format(resp.json()))

    @staticmethod
    def _gen_expire_time(mins=12):
        return time.time() + mins * 60

    @staticmethod
    def _check_resp(resp, exception=AirflowClientException, msg='request error: {}'):
        resp.raise_for_status()
        resp_json = resp.json()
        if resp_json.get('success', 1):
            return resp_json
        raise exception(msg.format(resp_json))

    @auto_refresh_token
    def get_dags(self, tags=('helpdesk',)):
        resp = requests.get(
            url=f'{self.server_url}/admin/helpdesk/api/tags/schemas',
            params={'tag': tags},
            headers={
                'Authorization': 'Bearer {}'.format(self._access_token),
                'Cache-Control': 'no-cache',
                'Content-Type': 'application/json'
            })
        return self._check_resp(resp, AirflowClientDagsException, msg='Get dags schema by tag error: {}')

    @auto_refresh_token
    def get_schema_by_dag_id(self, dag_id):
        resp = requests.get(
            url=f'{self.server_url}/admin/helpdesk/api/dags/{dag_id}/schema',
            headers={
                'Authorization': 'Bearer {}'.format(self._access_token),
                'Cache-Control': 'no-cache',
                'Content-Type': 'application/json'
            })
        return self._check_resp(
            resp, AirflowClientDagSchemaException, msg='Get dag schema by dag id [{}] error: {{}}'.format(dag_id))

    @auto_refresh_token
    def trigger_dag(self, dag_id, conf=None, run_id=None, execution_date=None):
        data = {}
        if conf:
            data['conf'] = conf
        if run_id:
            data['run_id'] = run_id
        else:
            data['run_id'] = f'helpdesk_{dag_id}_{str(uuid.uuid4())}'
        if execution_date:
            data['execution_date'] = execution_date

        resp = requests.post(
            url=f'{self.server_url}/api/experimental/dags/{dag_id}/dag_runs',
            headers={
                'Authorization': 'Bearer {}'.format(self._access_token),
                'Cache-Control': 'no-cache',
                'Content-Type': 'application/json'
            },
            data=json.dumps(data) if data else None)
        return self._check_resp(resp, AirflowClientTriggerDagException, msg=f'Trigger dag {dag_id} error: {{}}')

    @auto_refresh_token
    def get_dag_result(self, dag_id, execution_date, state=None):
        api_headers = {
            'Authorization': 'Bearer {}'.format(self._access_token),
            'Cache-Control': 'no-cache',
            'Content-Type': 'application/json'
        }
        # get dags info
        dag_info = self.get_schema_by_dag_id(dag_id)

        # get dag run result
        dag_run = requests.get(
            url=f'{self.server_url}/api/experimental/dags/{dag_id}/dag_runs/{execution_date}', headers=api_headers)
        dag_run = self._check_resp(
            dag_run, AirflowClientDagResultException, f'Get dag {dag_id}-{execution_date} result error: {{}}')

        # get task status
        task_instances = requests.get(
            url=f'{self.server_url}/admin/helpdesk/api/task_instances',
            headers=api_headers,
            params={
                'dag_id': dag_id,
                'execution_date': execution_date,
                'state': state
            })
        task_instances = self._check_resp(
            task_instances, AirflowClientException, f'Get dag {dag_id}-{execution_date} result error: {{}}')
        return {'dag_info': dag_info, 'status': dag_run['state'], 'task_instances': task_instances['task_instances']}

    @auto_refresh_token
    def get_task_result(self, dag_id, execution_date, task_id, try_number=None):
        api_headers = {
            'Authorization': 'Bearer {}'.format(self._access_token),
            'Cache-Control': 'no-cache',
            'Content-Type': 'application/json'
        }
        all_task_result = {}
        task_result = requests.get(
            url=f'{self.server_url}/admin/helpdesk/api/dags/{dag_id}/dag_runs/{execution_date}/tasks/{task_id}',
            headers=api_headers,
            params={'try_number': try_number})
        try:
            all_task_result[task_id] = self._check_resp(
                task_result, AirflowClientTaskResultException, 'Get task result {} error: {{}}'.format(task_id))
            if try_number:
                all_task_result[task_id]['message'] = [all_task_result[task_id]['message']]
        except AirflowClientTaskResultException as e:
            logger.error(f'Get {task_id} @ {execution_date} of {dag_id} error: {str(e)}')
            all_task_result[task_id] = {'message': [str(e)], 'metadata': {'end_of_log': True}, 'success': 1}
        return {'dag_id': dag_id, 'execution_date': execution_date, 'task_id': task_id, 'result': all_task_result}

    @timed_cache(minutes=15)
    @auto_refresh_token
    def get_user_roles(self, username):
        api_headers = {
            'Authorization': 'Bearer {}'.format(self._access_token),
            'Cache-Control': 'no-cache',
            'Content-Type': 'application/json'
        }
        resp = requests.get(
            url=f'{self.server_url}/admin/helpdesk/api/user/roles', headers=api_headers, params={'username': username})
        result = self._check_resp(resp, AirflowClientGetUserRolesException, f"Get user {username}'s roles error: {{}}")
        return result

    def build_graph_url(self, dag_id, execution_date):
        execution_date = quote(execution_date).replace('T', '+')
        return f'{self.server_url}/graph?dag_id={dag_id}&execution_date={execution_date}'

    @staticmethod
    def get_out_put_id_date(execution_date):
        return quote(execution_date).replace('T', '+')


if __name__ == '__main__':
    client = AirflowClient(refresh_token='token')
    print(client.get_schema_by_dag_id('view_user_ssh_key'))
