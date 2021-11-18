# coding: utf-8

import logging
import json
import traceback

from helpdesk.config import (
    AIRFLOW_SERVER_URL,
    AIRFLOW_USERNAME,
    AIRFLOW_PASSWORD,
    AIRFLOW_DEFAULT_DAG_TAG,
)
from helpdesk.libs.airflow import AirflowClient
from helpdesk.models.provider.errors import ResolvePackageError

from .base import BaseProvider

logger = logging.getLogger(__name__)


class FakeTaskInstance:
    """ Fake task instance for
    if new dag def update node in the dag, old result will not contain this node
    """
    def __init__(self):
        self.state = 'no_status'
        self.try_number = 0

    def __getitem__(self, item):
        return getattr(self, item, None)


class AirflowExecId:
    def __init__(self, dag_id, exec_date, run_id=None):
        self.dag_id = dag_id
        self.exec_date = exec_date
        self.run_id = run_id


AIRFLOW_FAKE_TI = FakeTaskInstance()


class AirflowProvider(BaseProvider):
    provider_type = 'airflow'

    def __init__(self, token=None, **kwargs):
        super().__init__(**kwargs)
        self.airflow_url = AIRFLOW_SERVER_URL
        if token:
            self.airflow_client = AirflowClient(refresh_token=token)
        else:
            self.airflow_client = AirflowClient(username=AIRFLOW_USERNAME, passwd=AIRFLOW_PASSWORD)
        self.default_tag = AIRFLOW_DEFAULT_DAG_TAG
        self.default_status_filter = ('skipped',)

    def get_default_pack(self):
        return self.default_tag

    def _build_action_from_dag(self, dags, pack=None):
        """
        build action from dag schema and details info
        :param dags: airflow client get_dags
        :return:
        """
        dags_schema = dags['dags_schema']
        dags_list = []
        for dag_info in dags_schema:
            schema = dag_info['schema']
            details = dag_info['details']
            json_schema = schema.get('params_json_schema')
            dags_list.append({
                'name': schema['name'],
                'parameters': schema.get('params'),
                'tags': schema.get('tags', self.default_tag),
                'description': schema['desc'],
                'enabled': schema.get('enabled', True),  # TODO: update helpdesk airflow plugin to get dag pause status
                'entry_point': schema.get('entry_point'),
                'metadata_file': details['filepath'],
                'output_schema': schema.get('output_schema'),
                'params_json_schema': json_schema,
                'uid': schema['dag_id'],
                'pack': pack or self.default_tag,
                'ref': schema['dag_id'],
                'id': schema['dag_id'],
                'runner_type': schema.get('runner_type'),
                'highlight_queries': schema.get('highlight_queries') or [r'\[.+_operator.py.+}} '],
                'pretty_log_formatter': schema.get('pretty_task_log_formatter', {}),
                'status_filter': schema.get('status_filter', self.default_status_filter)
            })
        return tuple(dags_list)

    def get_actions(self, pack=None):
        """
        :param pack: In st2 pack -> airflow dag tag
        :return: a list of
        <Action name=view_organizations,pack=trello,enabled=True,runner_type=python-script>
        to dict
        """
        try:
            dags = self.airflow_client.get_dags(tags=(self.default_tag if not pack else pack,))
            return self._build_action_from_dag(dags, pack=pack)
        except Exception as e:
            if pack:
                raise ResolvePackageError(e, traceback.format_exc(), f"Resolve pack {pack} error")
            raise e

    def get_action(self, ref):
        """
        return
        <Action name=view_organizations,pack=trello,enabled=True,runner_type=python-script>
        to dict
        :param ref: dag_id
        :return: dag dict
        """
        try:
            if '.' in ref:
                ref = ref.split('.')[-1]
            dag = self.airflow_client.get_schema_by_dag_id(ref)
            return self._build_action_from_dag({'dags_schema': [dag]})[0]
        except Exception as e:
            logging.error('get dag id {} schema error: {}'.format(ref, str(e)))
            return None

    def get_result_url(self, execution_id):
        exec_id = self._parse_execution_id(execution_id)
        return self.airflow_client.build_graph_url(exec_id.dag_id, exec_id.exec_date)

    def _build_execution_from_dag(self, trigger_resp, dag_id):
        return {
            'dag_id': dag_id,
            'execution_date': trigger_resp['execution_date'],
            'msg': trigger_resp['state'],
            'id': f'{dag_id}|{trigger_resp["execution_date"]}|{trigger_resp["dag_run_id"]}',
            'provider': self.provider_type,
            'web_url': self.get_result_url(f'{dag_id}|{trigger_resp["execution_date"]}')
        }

    @staticmethod
    def _parse_execution_id(execution_id: str) -> AirflowExecId:
        assert "|" in execution_id, "execution_id in helpdesk airflow provider must contains | separator"
        if execution_id.count("|") == 2:
            # compatible airflow v1.x
            dag_id, execution_date = execution_id.split('|')
            return AirflowExecId(dag_id, execution_date)
        else:
            dag_id, execution_date, run_id = execution_id.split('|', 2)
            return AirflowExecId(dag_id, execution_date, run_id)

    def run_action(self, ref, parameters):
        msg = ''
        try:
            trigger_result = self.airflow_client.trigger_dag(ref, conf=parameters)
            return self._build_execution_from_dag(trigger_result, ref) if trigger_result else None, msg
        except Exception as e:
            logger.error(f'run dag {ref} error: {str(e)}')
            return None, str(e)

    def generate_annotation(self, execution):
        if not execution:
            return
        return {
            'provider': self.provider_type,
            'id': execution['id'],
            'result_url': self.get_result_url(execution['id'])
        }

    @staticmethod
    def _format_exec_status(status):
        status_to_emoji = {
            'success': '✔️',
            'running': '🏃',
            'failed': '❌',
            'skipped': '⏭️',
            'upstream_failed': '⬆️❌',
            'up_for_reschedule': '🔄',
            'up_for_retry': '♻️',
            'queued': '👯',
            'no_status': '😿'
        }
        if status not in status_to_emoji:
            return status_to_emoji['no_status']
        else:
            return status_to_emoji[status]

    @staticmethod
    def _status_to_color(status):
        status_to_color = {
            'success': 'green',
            'running': '#00ff00',
            'failed': '#ff0000',
            'skipped': '#fecfd7',
            'upstream_failed': '#feba3f',
            'up_for_reschedule': '#6fe7db',
            'up_for_retry': '#fee03f',
            'queued': '#808080',
            'no_status': '#fafafa'
        }
        if status not in status_to_color:
            return status_to_color['no_status']
        else:
            return status_to_color[status]

    def _dag_graph_to_gojs_flow(self, dag_id, execution):
        airflow_graph = self.airflow_client.get_dag_graph(dag_id)
        schema = self.get_action(dag_id)
        status_filter = schema['status_filter']
        result = {
            'class': 'GraphLinksModel',
            'nodeDataArray': [],
            'linkDataArray': []
        }
        if airflow_graph:
            for node in airflow_graph['nodes']:
                ti = execution['task_instances'].get(node['id'])
                if not ti:
                    # if new dag def update node in the dag, old result will not contain this node
                    logger.warning(f"task_id {node['id']} can not be found in task_instance")
                    state = 'no_status'
                else:
                    state = ti['state']
                    if state in status_filter:
                        continue
                result['nodeDataArray'].append({
                    'key': node['id'],
                    'text': f'{self._format_exec_status(state)} {node["value"]["label"]}',
                    'color': node['value']['style'][5:-1],
                    'stroke': self._status_to_color(state)
                })

            for edge in airflow_graph['edges']:
                ti_v = execution['task_instances'].get(edge['v'])
                ti_u = execution['task_instances'].get(edge['u'])
                if not ti_v or not ti_u:
                    # if new dag def update node in the dag, old result will not contain this node
                    logger.warning(f"task instance can not be found in task_instance")
                else:
                    if any((ti_u['state'] in status_filter, ti_v['state'] in status_filter)):
                        continue
                result['linkDataArray'].append({
                    'to': edge['v'],
                    'from': edge['u']
                })
        return result

    def _get_result_highlight_queries(self, dag_id):
        schema = self.get_action(dag_id)
        return schema['highlight_queries']

    def _build_result_from_dag_exec(self, execution, execution_id):
        airflow_exec_id = self._parse_execution_id(execution_id)
        dag_id, execution_date, _ = airflow_exec_id.dag_id, airflow_exec_id.exec_date, airflow_exec_id.run_id
        schema = self.get_action(dag_id)
        highlight_queries = schema['highlight_queries']
        status_filter = schema['status_filter']
        result = {
            'status': execution['status'],
            'start_timestamp': execution_date,
            'web_url': self.get_result_url(execution_id),
            'result': {
                'tasks': [],
                'dag_id': dag_id
            },  # frontend only render subtab when len(result) == 2
            'id': execution_id,
            'graph': self._dag_graph_to_gojs_flow(dag_id, execution),
        }

        for task_id in execution['dag_info']['details']['task_ids']:
            task_instance = execution['task_instances'].get(task_id)
            if not task_instance:
                # if new dag def update node in the dag, old result will not contain this node
                logger.warning(f"task_id {task_id} can not be found in task_instance")
                # fake task instance
                task_instance = AIRFLOW_FAKE_TI
            # do not show specific status node
            if status_filter and task_instance['state'] in status_filter:
                continue
            is_task_success = task_instance['state'] == 'success'
            tasks_result = {}
            task_tried_times = task_instance['try_number'] - 1

            # check log result return
            if task_tried_times <= 0:
                tasks_result = {
                    task_id: {
                        'failed': True,
                        'stderr': task_instance['state'],
                        'return_code': 1,
                        'succeeded': False,
                        'stdout': ''
                    }
                }
            else:
                for tries_time in range(task_tried_times):
                    output_execution_date = self.airflow_client.get_out_put_id_date(execution_date)
                    msg = {
                        'output_load': True,
                        'query_string': f'?exec_output_id={dag_id}|{output_execution_date}|{task_id}|{tries_time+1}'
                    }
                    is_success_try = tries_time + 1 == task_tried_times and is_task_success
                    tasks_result[f'{task_id} -> [{tries_time+1}/{task_tried_times}]'] = {
                        'failed': tries_time + 1 != task_tried_times or not is_task_success,
                        'stderr': msg if not is_success_try else '',
                        'return_code': int(not is_success_try),
                        'succeeded': is_success_try,
                        'stdout': msg if is_success_try else '',
                        'highlight_queries': highlight_queries,
                    }

            result['result']['tasks'].append({
                'execution_id': f'{execution_id}|{task_id}',
                'created_at': task_instance['start_date'],
                'updated_at': task_instance['end_date'],
                'state': 'succeeded' if is_task_success else 'failed',
                'result': tasks_result,
                'id': task_id,
                'name': f'{self._format_exec_status(task_instance["state"])} {task_id}'
            })
        return result

    def get_execution(self, execution_id):
        exec_id = self._parse_execution_id(execution_id)
        try:
            execution = self.airflow_client.get_dag_result(exec_id.dag_id, exec_id.exec_date, exec_id.run_id)
            return self._build_result_from_dag_exec(
                execution, execution_id) if execution else None, ''
        except Exception as e:
            logger.error(f'get execution from {execution_id}, error: {traceback.format_exc()}')
            return None, str(e)

    def get_execution_output(self, execution_output_id):
        dag_id, execution_date, task_id, try_number = execution_output_id.split('|')
        std_out = self.airflow_client.get_task_result(dag_id, execution_date, task_id, try_number)
        # check log result return
        if 'message' not in std_out['result'][task_id]:
            msg = std_out['result'][task_id].get('message') or (json.dumps(std_out),)
            return msg, 'get execution output error'
        else:
            return {'message': std_out['result'][task_id]['message'],
                    'pretty_log': std_out['result'][task_id].get('pretty_log', {})}, ''
