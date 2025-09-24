# coding: utf-8

import logging
import json
import traceback
import re
import datetime
from urllib.parse import quote

from airflow_client.client.models.dag_run_response import DAGRunResponse
from airflow_client.client.models.task_instance_collection_response import (
    TaskInstanceCollectionResponse,
)
from airflow_client.client.models.task_instance_state import TaskInstanceState
from pydantic import BaseModel
from typing import List, Dict, Optional, Any, Tuple, Self

from helpdesk.config import (
    AIRFLOW_SERVER_URL,
    AIRFLOW_JWT_EXPIRATION_SECONDS,
    AIRFLOW_USERNAME,
    AIRFLOW_PASSWORD,
    AIRFLOW_DEFAULT_DAG_TAG,
)
from helpdesk.libs.airflow import AirflowClient
from helpdesk.libs.types import (
    StatusColor,
    TicketExecResultInfo,
    ActionInfo,
    ActionSchema,
    TicketExecInfo,
    TicketTaskLog,
    TicketExecStatus,
    TicketExecTaskInfo,
    TicketExecTaskDetails,
    Param,
    ParamType,
    TicketGraphNode,
    TicketGraphLink,
    TicketGraph,
    TicketExecTaskStatus,
    TicketExecTasksResult,
    RunnerType,
    StatusEmoji,
)
from helpdesk.models.provider.errors import ResolvePackageError
from helpdesk.models.provider.base import BaseProvider

logger = logging.getLogger(__name__)


class AirflowExecAnnotation(BaseModel):
    dag_id: str = ""
    dag_run_id: str = ""
    dag_version: int = 1
    result_url: str = ""

    def __repr__(self) -> str:
        return f"<dag {self.dag_id} with dag run {self.dag_run_id}>"

    def from_annotation(self, annotation: Dict[str, Any]) -> Self:
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
        self.dag_version = annotation["dag_version"]
        return self


class AirflowProvider(BaseProvider):
    provider_type = "airflow"
    EXTRA_INFO_RE = re.compile(r".*```helpdesk(.+)```.*", re.DOTALL)
    MAX_LOG_LINES = 100000

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.airflow_url = AIRFLOW_SERVER_URL
        self.airflow_client = AirflowClient(
            username=AIRFLOW_USERNAME,
            passwd=AIRFLOW_PASSWORD,
            server_url=AIRFLOW_SERVER_URL,
            jwt_expire_seconds=AIRFLOW_JWT_EXPIRATION_SECONDS,
        )
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

        关于多选:
        - array + example = 多选 = helpdesk array
        - array + enum = 单选 = helpdesk string
        """
        params_schema, json_schema = {}, {"type": "object", "properties": {}}
        extra_attrs = {}

        for param_name, schema_def in airflow_param.items():
            field_schema = schema_def["schema"]
            logger.debug("field %s schema: %s", param_name, schema_def)
            extra_json_info = AirflowProvider.EXTRA_INFO_RE.match(
                field_schema.get("description_md", "")
            )

            immutable = False
            ftype = field_schema["type"]

            airflow_param_type = ftype if not isinstance(ftype, list) else ftype[-1]
            helpdesk_param_type = ParamType(airflow_param_type)

            # 这是helpdesk的单选，helpdesk只关心是否有enum类型, 有就是选择，如果array那就是多选，string那就单选
            if (
                helpdesk_param_type == ParamType.ARRAY
                and field_schema.get("enum")
                and not field_schema.get("examples")
            ):
                helpdesk_param_type = ParamType.STRING

            if extra_json_info:
                extra_info = json.loads(extra_json_info.groups()[0])
                logger.debug("extra info %s", extra_info)
                immutable = extra_info.get("immutable", False)
                json_schema["properties"][param_name] = {"type": airflow_param_type}
                json_schema["properties"][param_name].update(
                    extra_info.get("json_schema", {})
                )
                logger.debug(
                    "json schema after merge: %s", json.dumps(json_schema, indent=2)
                )
                if "schema" in extra_info:
                    json_schema.update(extra_info["schema"])
                    logger.debug(
                        "json schema after merge with schema: %s",
                        json.dumps(json_schema, indent=2),
                    )

                if "pretty_task_log_formatter" in extra_info:
                    extra_attrs["pretty_task_log_formatter"] = extra_info[
                        "pretty_task_log_formatter"
                    ]

            param_desc = schema_def.get("description")
            if param_desc is None:
                param_desc = (
                    field_schema.get("description_md", "")
                    .split("```helpdesk")[0]
                    .strip()
                )

            params_schema[param_name] = Param(
                description=param_desc,
                type=helpdesk_param_type,
                required=not isinstance(ftype, list),
                enum=field_schema.get("enum", field_schema.get("examples")),
                immutable=immutable,
                default=field_schema.get("value"),
            )
        return params_schema, json_schema, extra_attrs

    def _build_action_from_dag_details(self, dag_details, tag=None):
        """
        build action from dag schema and details info
        :param dags: airflow client get_dags
        :return:
        """
        params_schema, json_schema, extra_attrs = self.airflow_schema_to_helpdesk(
            dag_details.params
        )
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
            status_filter=extra_attrs.get("status_filter"),
        )

    def get_actions_info(self, pack: Optional[str] = None) -> List[ActionInfo]:
        """
        获取所有pack tag的dag的简单信息
        """
        try:
            dags = self.airflow_client.get_dags(
                tags=(self.default_tag if not pack else pack,)
            ).dags
            return [
                ActionInfo(
                    name=d.dag_display_name,
                    description=d.description if d.description else d.dag_display_name,
                    action_id=d.dag_id,
                )
                for d in dags
            ]
        except Exception as e:
            if pack:
                raise ResolvePackageError(
                    e, traceback.format_exc(), f"Resolve pack {pack} error"
                )
            raise e

    def get_action_schema(self, dag_id: str) -> Optional[ActionSchema]:
        try:
            return self._build_action_from_dag_details(
                self.airflow_client.get_schema_by_dag_id(dag_id), dag_id
            )
        except Exception as e:
            logger.error("get dag(id or tag) %s schema failed", dag_id)
            logger.exception(e)
            return None

    def get_actions_schema_by_pack(self, ref: str) -> List[ActionSchema]:
        """
        根据dag tag获取dags schema list
        """
        try:
            dag_ids = [ref]
            # 如果是.结尾表示是tag查询
            if "." in ref:
                ref = ref.split(".")[-1]
                ref_to_dags = self.airflow_client.get_dags(tags=[ref, self.default_tag])
                dag_ids = [d.dag_id for d in ref_to_dags]

            hform_schemas = []
            for d in dag_ids:
                hform_schemas.append(
                    self._build_action_from_dag_details(
                        self.airflow_client.get_schema_by_dag_id(d.dag_id), ref
                    )
                )
            return hform_schemas
        except Exception as e:
            logging.error("get dag(id or tag) %s schema error: %s", ref, str(e))
            return []

    def get_result_url(self, ticket_name, dag_run_id):
        return self.airflow_client.build_graph_url(ticket_name, dag_run_id)

    def _build_execution_from_dag(self, trigger_resp, dag_id):
        return TicketExecInfo(
            exec_id=trigger_resp.dag_run_id,
            execution_date=trigger_resp.start_date or datetime.datetime.now(),
            msg=trigger_resp.state.value,
            ticket_name=trigger_resp.dag_id,
            runner=RunnerType.AIRFLOW,
            result_url=self.get_result_url(
                trigger_resp.dag_id, trigger_resp.dag_run_id
            ),
            annotation={"dag_version": trigger_resp.dag_versions[-1].version_number},
        )

    def exec_ticket(
        self, ticket_name: str, parameters: Dict[str, Any], extra_info: str = None
    ) -> Tuple[TicketExecInfo, str]:
        logger.info("exec airflow dag %s with conf: %s", ticket_name, parameters)
        try:
            trigger_result = self.airflow_client.trigger_dag(
                ticket_name, conf=parameters, extra_info=extra_info
            )
            if trigger_result:
                return self._build_execution_from_dag(trigger_result, ticket_name), ""
            raise Exception(f"trigger dag {ticket_name} failed")
        except Exception as e:
            logger.exception(e)
            return None, f"exec ticket {ticket_name} failed, error: {str(e)}"

    def get_exec_annotation(self, execution: TicketExecInfo) -> Dict[str, Any]:
        return AirflowExecAnnotation(
            dag_id=execution.ticket_name,
            dag_run_id=execution.exec_id,
            result_url=execution.result_url,
            dag_version=execution.annotation["dag_version"],
        ).dict()

    def _dag_graph_to_gojs_flow(
        self, dag_id: str, dag_version: int, task_result: TicketExecResultInfo
    ) -> TicketGraph:
        airflow_graph = self.airflow_client.get_dag_graph(dag_id, dag_version)
        result = TicketGraph()
        tasks_status: Dict[str, TicketExecTaskStatus] = {
            t.task_id: (
                TicketExecTaskStatus[t.state.value.upper()]
                if t.state
                else TicketExecTaskStatus.NO_STATUS
            )
            for t in task_result.tasks
        }
        if airflow_graph:
            result.nodes = []
            result.edges = []

            for node in airflow_graph["nodes"]:
                nid = node["id"]
                tstats = tasks_status[nid]

                # fill stroke color and text by status of task
                try:
                    status_emoji = StatusEmoji[tstats.value.upper()].value
                    status_stroke = StatusColor[tstats.value.upper()]
                except Exception as e:
                    logger.error(
                        "unknown task status %s for node %s, set to NO_STATUS",
                        tstats,
                        nid,
                    )
                    logger.exception(e)
                    status_emoji = StatusEmoji.NO_STATUS.value
                    status_stroke = StatusColor.NO_STATUS

                result.nodes.append(
                    TicketGraphNode(
                        key=nid,
                        text=f"{status_emoji} {node['label']}",
                        stroke=status_stroke,
                    )
                )

            for edge in airflow_graph["edges"]:
                result.edges.append(
                    TicketGraphLink(to=edge["target_id"], from_=edge["source_id"])
                )
        return result

    def _build_result_from_dag_exec(
        self, dag_run: DAGRunResponse, tis: TaskInstanceCollectionResponse
    ) -> TicketExecResultInfo:
        # 准备任务信息列表
        tasks_info: List[TicketExecTaskInfo] = []

        # 把执行结果按task_id分类（里面会包含多次retry）的结果
        task_ins = {}
        for task_instance in tis.task_instances:
            task_id = task_instance.task_id
            if task_id in task_ins:
                task_ins[task_id].append(task_instance)
            else:
                task_ins[task_id] = [task_instance]

        for task_id, task_instance_list in task_ins.items():
            task_info = TicketExecTaskInfo(
                name=task_id,
                exec_id=dag_run.dag_run_id,
                task_id=task_id,
                created_at=None,
                updated_at=None,
                result=None,
            )

            task_info_results: Dict[str, TicketExecTaskDetails] = {}
            for task_instance in task_instance_list:
                logger.debug(task_instance)
                task_status = (
                    TicketExecTaskStatus(task_instance.state.value)
                    if task_instance.state
                    else TicketExecTaskStatus.NO_STATUS
                )
                if (
                    task_info.created_at is None
                    or task_info.created_at > task_instance.start_date
                ):
                    task_info.created_at = task_instance.start_date

                if (
                    task_info.updated_at is None
                    or task_info.updated_at < task_instance.end_date
                ):
                    task_info.updated_at = task_instance.end_date

                task_info.state = task_status
                task_uniq_id = quote(
                    f"{dag_run.dag_id}|{dag_run.dag_run_id}|{task_id}|{task_instance.try_number}"
                )
                task_details = TicketExecTaskDetails(
                    status=task_status,
                    failed=task_instance.state == TaskInstanceState.FAILED,
                    stderr=task_status.value,
                    return_code=1,
                    succeeded=False,
                    stdout="",
                    highlight_queries="",  # TODO: extract hq from dag schema info
                )

                if task_instance.try_number > 0:
                    log_query_info = {
                        "output_load": True,
                        "query_string": f"?exec_output_id={task_uniq_id}",
                    }
                    is_task_succ = task_status == TicketExecTaskStatus.SUCCESS
                    task_details.stderr = ""
                    task_details.return_code = 0 if is_task_succ else 1
                    task_details.succeeded = is_task_succ
                    task_details.stdout = log_query_info

                task_info_results[f"{task_id} [{task_instance.try_number}]"] = (
                    task_details
                )

            task_info.result = task_info_results
            tasks_info.append(task_info)

        return TicketExecTasksResult(tasks=tasks_info, id=dag_run.dag_run_id)

    def get_exec_result(self, annotation: Dict[str, Any]):
        exec_annotation = AirflowExecAnnotation().from_annotation(annotation)
        try:
            dag_run, dag_instances = self.airflow_client.get_dag_result(
                exec_annotation.dag_id, exec_annotation.dag_run_id
            )
            logger.debug("dag_run: %s\n dag_ins: %s", dag_run, dag_instances)
            result = self._build_result_from_dag_exec(dag_run, dag_instances)
            graph = self._dag_graph_to_gojs_flow(
                exec_annotation.dag_id, exec_annotation.dag_version, result
            )
            return (
                TicketExecResultInfo(
                    ticket_id=exec_annotation.dag_id,
                    status=TicketExecStatus(dag_run.state.value),
                    start_timestamp=dag_run.start_date,
                    result_url=exec_annotation.result_url,
                    result=result,
                    graph=graph,
                ),
                "",
            )
        except Exception as e:
            logger.error(
                f"get execution result from {exec_annotation}, error: {traceback.format_exc()}"
            )
            return None, str(e)

    def get_exec_log(self, execution_output_id: str) -> TicketTaskLog:
        try:
            dag_id, dag_run_id, task_id, try_number = execution_output_id.split("|")
            std_out = self.airflow_client.get_task_log(
                dag_id, dag_run_id, task_id, int(try_number)
            )
            data = json.loads(std_out.read())
            logger.debug("log for %s: %s", execution_output_id, data)
            if "content" not in data:
                return TicketTaskLog(
                    message="Load log from airflow failed, no content found, maybe rotated",
                    is_rotated=True
                )
            else:
                m = []
                content = data["content"]
                is_truncated = len(content) > self.MAX_LOG_LINES

                for e in content[-1 * self.MAX_LOG_LINES :]:
                    if "level" not in e or "timestamp" not in e or "event" not in e:
                        continue
                    else:
                        m.append(
                            f"level={e['level']} time={e['timestamp']} msg=\"{e['event']}\""
                        )

                if is_truncated:
                    m.append(
                        f"level=fatal, time={datetime.datetime.now()}, "
                        f'msg="MAX LOG LINES({self.MAX_LOG_LINES}) reached, log truncated from head, like `tail -n`"'
                    )

                return TicketTaskLog(message="\n".join(m), load_success=True)
        except Exception as e:
            logger.exception(e)
            return TicketTaskLog(
                message="Load log from airflow failed, contact admin for help",
                load_success=False,
            )
