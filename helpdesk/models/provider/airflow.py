# coding: utf-8

import logging
import json
import traceback
import re
import datetime

from airflow_client.client.models.dag_run_response import DAGRunResponse
from airflow_client.client.models.task_instance_collection_response import TaskInstanceCollectionResponse
from airflow_client.client.models.task_instance_state import TaskInstanceState
from pydantic import BaseModel
from typing import List, Dict, Optional, Any, Tuple, Self

from helpdesk.config import (
    AIRFLOW_SERVER_URL,
    AIRFLOW_USERNAME,
    AIRFLOW_PASSWORD,
    AIRFLOW_DEFAULT_DAG_TAG,
)
from helpdesk.libs.airflow import AirflowClient
from helpdesk.libs.types import TicketExecResultInfo, ActionInfo, \
    ActionSchema, TicketExecInfo, TicketTaskLog, TicketExecStatus, \
    TicketExecTaskInfo, TicketExecTaskDetails, Param, ParamType, \
    TicketGraphNode, TicketGraphLink, TicketGraph, TicketExecTaskStatus, \
    TicketExecTasksResult, RunnerType
from helpdesk.models.provider.errors import ResolvePackageError
from helpdesk.models.provider.base import BaseProvider

logger = logging.getLogger(__name__)


class AirflowExecAnnotation(BaseModel):
    dag_id: str = ""
    dag_run_id: str = ""
    result_url: str = ""

    def __repr__(self) -> str:
        return f"<dag {self.dag_id} with dag run {self.dag_run_id}>"

    def from_annotation(self, annotation: Dict[str, str]) -> Self:
        if "id" in annotation:
            _id = annotation["id"]
            if _id.count("|") == 1:
                self.dag_id, self.dag_run_id = _id.split("|")
            else:
                self.dag_id, _, self.dag_run_id = _id.split("|")
        else:
            self.dag_id = annotation["dag_id"]
            self.dag_run_id = annotation["dag_run_id"]
        self.result_url = annotation["result_url"]
        return self


class AirflowProvider(BaseProvider):
    provider_type = 'airflow'
    EXTRA_INFO_RE = re.compile(r'.*```helpdesk(.+)```.*', re.DOTALL)
    MAX_LOG_LINES = 100000

    def __init__(self, token=None, **kwargs):
        super().__init__(**kwargs)
        self.airflow_url = AIRFLOW_SERVER_URL
        if token:
            self.airflow_client = AirflowClient(refresh_token=token)
        else:
            self.airflow_client = AirflowClient(username=AIRFLOW_USERNAME, passwd=AIRFLOW_PASSWORD)
        self.default_tag = AIRFLOW_DEFAULT_DAG_TAG
        self.default_status_filter = ()

    def get_default_pack(self):
        return self.default_tag

    @staticmethod
    def airflow_schema_to_helpdesk(airflow_param: Dict[str, Any]) -> Tuple[Any]:
        """
        因为airflow的dag现在支持param声明，所以我们把原来的param_schema和json_schema
        分别放在param的定义内，不支持的就放在`description_md`这个字段里使用 ```helpdesk```来标识

        json_schema的部分放在`helpdesk_ticket_callback_url`这个参数的`description_md`内

        这里需要把这些拼成原来的格式
        """
        params_schema, json_schema = {}, {"type": "object", "properties": {}}
        extra_attrs = {}

        for param_name, schema_def in airflow_param.items():
            field_schema = schema_def["schema"]
            extra_json_info = AirflowProvider.EXTRA_INFO_RE.match(field_schema.get("description_md", ""))

            immutable = False
            if extra_json_info:
                extra_info = json.loads(extra_json_info.groups()[0])
                immutable = extra_info.get("immutable", False)
                json_schema["properties"][param_name] = {
                    "type": field_schema["type"]
                }.update(extra_info.get("json_schema", {}))

                if "schema" in extra_info:
                    json_schema.update(extra_info["schema"])

                if "pretty_task_log_formatter" in extra_info:
                    extra_attrs['pretty_task_log_formatter'] = extra_info["pretty_task_log_formatter"]

            ftype = field_schema["type"]
            helpdesk_param_type = ParamType.STRING
            airflow_param_type = ftype if not isinstance(ftype, list) else ftype[-1]
            if airflow_param_type != 'array':
                helpdesk_param_type = ParamType(airflow_param_type)

            param_desc = schema_def.get("description")
            if param_desc is None:
                param_desc = field_schema.get("description_md", "").split('```helpdesk')[0].strip()

            params_schema[param_name] = Param(
                description=param_desc,
                type=helpdesk_param_type,
                required=not isinstance(ftype, list),
                enum=field_schema.get("enum"),
                immutable=immutable,
                default=field_schema.get("value")
            )
        return params_schema, json_schema, extra_attrs

    def _build_action_from_dag_details(self, dag_details, tag=None):
        """
        build action from dag schema and details info
        :param dags: airflow client get_dags
        :return:
        """
        params_schema, json_schema, extra_attrs = self.airflow_schema_to_helpdesk(dag_details.params)
        return ActionSchema(
            id=dag_details.dag_id,
            name=dag_details.dag_display_name,
            parameters=params_schema,
            tags=[self.default_tag] if tag is None else [self.default_tag, tag],
            description=dag_details.description or dag_details.dag_display_name,
            params_json_schema=json_schema,
            pack=tag,
            runner_type=self.provider_type,
            highlight_queries=extra_attrs.get("highlight_queries"),
            pretty_log_formatter=extra_attrs.get("pretty_task_log_formatter"),
            status_filter=extra_attrs.get("status_filter")
        )

    def get_actions_info(self, pack: Optional[str] = None) -> List[ActionInfo]:
        """
        获取所有pack tag的dag的简单信息
        """
        try:
            dags = self.airflow_client.get_dags(tags=(self.default_tag if not pack else pack,)).dags
            return [
                ActionInfo(
                    name=d.dag_display_name,
                    description=d.description if d.description else d.dag_display_name,
                    action_id=d.dag_id
                ) for d in dags
            ]
        except Exception as e:
            if pack:
                raise ResolvePackageError(e, traceback.format_exc(), f"Resolve pack {pack} error")
            raise e

    def get_action_schema(self, dag_id: str) -> Optional[ActionSchema]:
        try:
            return self._build_action_from_dag_details(
                self.airflow_client.get_schema_by_dag_id(dag_id),
                dag_id
            )
        except Exception as e:
            logger.error('get dag(id or tag) %s schema failed', dag_id)
            logger.exception(e)
            return None

    def get_actions_schema_by_pack(self, ref: str) -> List[ActionSchema]:
        """
        根据dag tag获取dags schema list
        """
        try:
            dag_ids = [ref]
            # 如果是.结尾表示是tag查询
            if '.' in ref:
                ref = ref.split('.')[-1]
                ref_to_dags = self.airflow_client.get_dags(tags=[ref, self.default_tag])
                dag_ids = [d.dag_id for d in ref_to_dags]

            hform_schemas = []
            for d in dag_ids:
                hform_schemas.append(
                    self._build_action_from_dag_details(
                        self.airflow_client.get_schema_by_dag_id(d.dag_id),
                        ref
                    )
                )
            return hform_schemas
        except Exception as e:
            logging.error('get dag(id or tag) %s schema error: %s', ref, str(e))
            return []

    def get_result_url(self, ticket_name, dag_run_id):
        return self.airflow_client.build_graph_url(ticket_name, dag_run_id)

    def _build_execution_from_dag(self, trigger_resp, dag_id):
        return TicketExecInfo(
            exec_id=trigger_resp.dag_run_id,
            execution_date=trigger_resp.start_date,
            msg=str(trigger_resp.state),
            ticket_name=trigger_resp.dag_id,
            runner_type=RunnerType.AIRFLOW,
            web_url=self.get_result_url(trigger_resp.dag_run_id)
        )

    def exec_ticket(self, ticket_name: str, parameters: Dict[str, Any], extra_info: str=None) -> TicketExecInfo:
        trigger_result = self.airflow_client.trigger_dag(ticket_name, conf=parameters, extra_info=extra_info)
        return self._build_execution_from_dag(trigger_result, ticket_name) if trigger_result else None

    def get_exec_annotation(self, execution: TicketExecInfo) -> Dict[str, str]:
        return AirflowExecAnnotation(
            exec_id=execution.exec_id,
            result_url=execution.result_url,
            provider=self.provider_type
        ).dict()

    def _dag_graph_to_gojs_flow(self, dag_id, execution):
        dag_version = execution.version()
        airflow_graph = self.airflow_client.get_dag_graph(dag_id, dag_version)
        result = TicketGraph()
        if airflow_graph:
            result.nodes = []
            result.edges = []

            for node in airflow_graph['nodes']:
                result.nodes.append(
                    TicketGraphNode(
                        key=node["id"],
                        text=node["label"],
                    )
                )

            for edge in airflow_graph['edges']:
                result.edges.append(
                    TicketGraphLink(
                        to=edge["target_id"],
                        from_=edge["source_id"]
                    )
                )
        return result

    def _build_result_from_dag_exec(self, dag_run: DAGRunResponse, tis: TaskInstanceCollectionResponse) -> TicketExecResultInfo:
        # 准备任务信息列表
        tasks_info: List[TicketExecTaskInfo] = []

        # 把执行结果按task_id分类（里面会包含多次retry）的结果
        task_result_ins = {}
        for task_instance in tis.task_instances:
            task_id = task_instance.task_id
            if task_id in task_result_ins:
                task_result_ins[task_id].append(task_instance)
            else:
                task_result_ins[task_id] = [task_instance]

        for task_id, task_instance_list in task_result_ins.items():
            task_info_results: Dict[str, TicketExecTaskDetails] = {}
            task_info = TicketExecTaskInfo(
                name=task_id,
                execution_id=dag_run.dag_run_id,
                task_id=task_id,
                created_at=None,
                updated_at=None,
                state=None,
                result=None
            )

            for task_instance in task_instance_list:
                task_status = TicketExecTaskStatus(str(task_instance.state))
                if task_info.created_at is None or task_info.created_at > task_instance.start_date:
                    task_info.created_at = task_instance.start_date

                if task_info.updated_at is None or task_info.updated_at < task_instance.end_date:
                    task_info.created_at = task_instance.end_date

                is_final_try = task_instance.try_number + 1 == task_instance.max_tries
                if is_final_try:
                    task_info.state = task_status

                task_uniq_id = f"{dag_run.dag_id}|{dag_run.dag_run_id}|{task_id}|{task_instance.try_number+1}"

                task_details = TicketExecTaskDetails(
                    status=task_status,
                    failed=task_instance.state == TaskInstanceState.FAILED,
                    stderr=str(task_instance.state),
                    return_code=1,
                    succeeded=False,
                    stdout="",
                    highlight_queries=""  # TODO: extract hq from dag schema info
                )

                if task_instance.try_number > 0:
                    is_task_succ = task_instance.state == TaskInstanceState.SUCCESS
                    is_success_try = is_task_succ and is_final_try
                    log_query_info = {
                        'output_load': True,
                        'query_string': f'?exec_output_id={task_uniq_id}'
                    }
                    task_details.stderr = log_query_info if not is_success_try else ''
                    task_details.return_code = int(not is_success_try)
                    task_details.succeeded = is_success_try
                    task_details.stdout = log_query_info if not is_success_try else ''

                task_info_results[f"{task_id} [{task_instance.try_number+1}/{task_instance.max_tries}]"] = task_details

            task_info.result = task_info_results

        tasks_info.append(task_info)

        return TicketExecTasksResult(
            tasks=tasks_info,
            id=dag_run.dag_run_id
        )

    def get_exec_result(self, annotation: Dict[str, str]):
        exec_annotation = AirflowExecAnnotation().from_annotation(annotation)
        try:
            dag_run, dag_instances = self.airflow_client.get_dag_result(
                exec_annotation.dag_id, exec_annotation.dag_run_id
            )
            result = self._build_result_from_dag_exec(dag_run, dag_instances)
            graph = self._dag_graph_to_gojs_flow(exec_annotation.dag_id, dag_run)
            web_url = self.get_result_url(exec_annotation.dag_id, dag_run.dag_run_id)
            return TicketExecResultInfo(
                ticket_id=exec_annotation.dag_id,
                status=TicketExecStatus(str(dag_run.state)),
                start_timestamp=dag_run.start_date,
                web_url=web_url,
                result=result,
                graph=graph
            ), ''
        except Exception as e:
            logger.error(f'get execution result from {exec_annotation}, error: {traceback.format_exc()}')
            return None, str(e)

    def get_exec_log(self, execution_output_id: str) -> TicketTaskLog:
        dag_id, dag_run_id, task_id, try_number = execution_output_id.split('|')
        std_out = self.airflow_client.get_task_result(dag_id, dag_run_id, task_id, try_number)

        try:
            data = json.loads(std_out)
            if 'content' not in data:
                return TicketTaskLog(
                    message="Load log from airflow failed, no content found"
                )
            else:
                m = []
                for e in data['content']:
                    if 'level' not in e or 'timestamp' not in e or 'event' not in e:
                        continue
                    else:
                        m.append(f"level={e['level']} time={e['timestamp']} msg=\"{e['event']}\"")
                        if len(m) > self.MAX_LOG_LINES:
                            m.append(
                                f"level=fatal, time={datetime.datetime.now()},"
                                f" msg=\"MAX LOG LINES({self.MAX_LOG_LINES}), please go to airflow see more logs, \""
                                "or contact sa for help"
                            )
                            break
                return TicketTaskLog(message="\n".join(m), load_success=True)
        except Exception as e:
            return TicketTaskLog(messge=f"Load log from airflow failed: {str(e)}")
