# coding: utf-8

import logging
import json

from helpdesk.config import (
    AIRFLOW_SERVER_URL,
    AIRFLOW_USERNAME,
    AIRFLOW_PASSWORD,
    AIRFLOW_DEFAULT_DAG_TAG,
    DEFAULT_EMAIL_DOMAIN,
)
from helpdesk.libs.airflow import AirflowClient
from helpdesk.models.provider import Provider
from helpdesk.models.providers.ldap import LdapProviderMixin

logger = logging.getLogger(__name__)


class AirflowProvider(LdapProviderMixin, Provider):
    provider_type = 'airflow'

    def __init__(self, token=None, user=None):
        super().__init__(token=token, user=user)
        self.airflow_url = AIRFLOW_SERVER_URL
        if token:
            self.airflow_client = AirflowClient(refresh_token=token)
        else:
            self.airflow_client = AirflowClient(username=AIRFLOW_USERNAME, passwd=AIRFLOW_PASSWORD)
        self.default_tag = AIRFLOW_DEFAULT_DAG_TAG

    def get_default_pack(self):
        return self.default_tag

    def get_user_email(self, user=None):
        user = user or self.user
        return self.get_user_email_from_ldap(user) or '%s@%s' % (user, DEFAULT_EMAIL_DOMAIN)

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
            dags_list.append({
                'name': schema['name'],
                'parameters': schema.get('params'),
                'tags': schema.get('tags', self.default_tag),
                'description': schema['desc'],
                'enabled': schema.get('enabled', True),  # TODO: update helpdesk airflow plugin to get dag pause status
                'entry_point': schema.get('entry_point'),
                'metadata_file': details['filepath'],
                'output_schema': schema.get('output_schema'),
                'uid': schema['dag_id'],
                'pack': pack or self.default_tag,
                'ref': schema['dag_id'],
                'id': schema['dag_id'],
                'runner_type': schema.get('runner_type')
            })
        return tuple(dags_list)

    def get_actions(self, pack=None):
        """
        :param pack: In st2 pack -> airflow dag tag
        :return: a list of
        <Action name=view_organizations,pack=trello,enabled=True,runner_type=python-script>
        to dict
        """
        dags = self.airflow_client.get_dags(tags=(self.default_tag if not pack else pack,))

        return self._build_action_from_dag(dags, pack=pack)

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
        dag_id, execution_date = execution_id.split('|')
        return self.airflow_client.build_graph_url(dag_id, execution_date)

    def _build_execution_from_dag(self, trigger_resp, dag_id):
        return {
            'dag_id': dag_id,
            'execution_date': trigger_resp['execution_date'],
            'msg': trigger_resp['message'],
            'id': f'{dag_id}|{trigger_resp["execution_date"]}',
            'provider': self.provider_type,
            'web_url': self.get_result_url(f'{dag_id}|{trigger_resp["execution_date"]}')
        }

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

    def _build_result_from_dag_exec(self, execution, execution_id, filter_status=None):
        dag_id, execution_date = execution_id.split('|')
        result = {
            'status': execution['status'],
            'start_timestamp': execution_date,
            'web_url': self.get_result_url(execution_id),
            'result': {
                'tasks': [],
                'dag_id': dag_id
            },  # frontend only render subtab when len(result) == 2
            'id': execution_id,
        }

        for task_id in execution['dag_info']['details']['task_ids']:
            task_instance = execution['task_instances'].get(task_id)
            if not task_instance:
                # if new dag def update node in the dag, old result will not contain this node
                logger.warning(f"task_id {task_id} can not be found in task_instance")
                continue
            if filter_status and task_instance['state'] in filter_status:
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
                        'stdout': msg if is_success_try else ''
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
        dag_id, execution_date = execution_id.split('|')
        try:
            execution = self.airflow_client.get_dag_result(dag_id, execution_date)
            return self._build_result_from_dag_exec(
                execution, execution_id, filter_status=('skipped',)) if execution else None, ''
        except Exception as e:
            logger.error(f'get execution from {execution_id}, error: {str(e)}')
            return None, str(e)

    def authenticate(self, user, password=None):
        try:
            if password:
                token = self.airflow_client.generate_token(user, password)
            else:
                token = self.airflow_client.generate_token(AIRFLOW_USERNAME, AIRFLOW_PASSWORD)
            if token:
                return {'token': token['refresh_token'], 'user': user, 'expiry': token['expire_time']}, ''
            return None, ''
        except Exception as e:
            logger.error('auth with airflow error: {}'.format(str(e)))
            return None, str(e)

    def get_user_roles(self, user=None):
        '''return a list of roles,
            e.g. ["admin"]
        '''
        roles = []
        try:
            roles = self.airflow_client.get_user_roles(username=user or 'sysadmin')
            logger.debug('Get user roles: %s.get_user_roles(): %s', self, roles)
            return roles['role_from_jwt'] if not user else roles
        except Exception as e:
            logger.error('Get user role error: {}'.format(str(e)))
        return roles

    def get_execution_output(self, execution_output_id):
        dag_id, execution_date, task_id, try_number = execution_output_id.split('|')
        std_out = self.airflow_client.get_task_result(dag_id, execution_date, task_id, try_number)
        # check log result return
        if 'message' not in std_out['result'][task_id]:
            msg = std_out['result'][task_id].get('message') or (json.dumps(std_out),)
            return msg, 'get execution output error'
        else:
            return std_out['result'][task_id]['message'], ''
