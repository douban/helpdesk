# coding: utf-8

import logging
import json
import datetime

from helpdesk.config import SPINCYCLE_RM_URL, SPINCYCLE_USERNAME, SPINCYCLE_PASSWORD, DEFAULT_EMAIL_DOMAIN
from helpdesk.libs.spincycle import SpinCycleClient
from helpdesk.models.provider import Provider
from helpdesk.models.providers.ldap import LdapProviderMixin

logger = logging.getLogger(__name__)


class SpinCycleProvider(LdapProviderMixin, Provider):
    provider_type = 'spincycle'
    spin_req_status = {
        0: "UNKNOWN",
        1: "PENDING",
        2: "RUNNING",
        3: "COMPLETE",
        4: "FAIL",
        5: "RESERVED",
        6: "STOPPED",
        7: "SUSPENDED"
    }

    spin_status_to_num = {v: k for k, v in spin_req_status.items()}

    status_to_emoji = {3: '✔️', 2: '🏃', 4: '❌', 6: '🛑', 5: '🔄', 7: '▶', 1: '👯', 0: '😿'}

    def __init__(self, token=None, user=None):
        super().__init__(token=token, user=user)
        self.spincycle_rm_url = SPINCYCLE_RM_URL
        if token:
            logger.warning("Spin cycle provider can not auth with token.")
        self.spin_client = SpinCycleClient(SPINCYCLE_USERNAME, SPINCYCLE_PASSWORD)

        # since spin cycle has no idea of pack so this is the only "pack" we have
        self.default_pack = "spincycle"

    def get_default_pack(self):
        return "spincycle"

    def get_user_email(self, user=None):
        user = user or self.user
        return self.get_user_email_from_ldap(user) or '%s@%s' % (user, DEFAULT_EMAIL_DOMAIN)

    @staticmethod
    def _spin_args_to_json_schema(spin_args):
        if spin_args:
            result = {}
            for arg in spin_args:
                param_schema = {k.lower(): v for k, v in arg.items()}
                if 'desc' in param_schema:
                    param_schema['description'] = param_schema['desc']
                    del param_schema['desc']
                param_type = param_schema.get('type')
                if param_type == 'optional':
                    param_schema['required'] = False
                if param_type == 'required':
                    param_schema['required'] = True
                if param_type == 'static':
                    param_schema['immutable'] = True
                result[arg['Name']] = param_schema
            return result
        return spin_args

    def _build_action_from_req(self, reqs, pack=None):
        """
        build action from requests schema and details info
        :param reqs: spincycle requests list
        :return:
        """
        req_list = []
        for req_info in reqs:
            args = req_info.get("Args")
            req_list.append({
                'name': req_info['Name'],
                'parameters': self._spin_args_to_json_schema(args),
                'tags': self.default_pack,
                'description': req_info["Name"],
                'enabled': True,
                'entry_point': None,
                'metadata_file': None,
                'output_schema': None,
                'uid': req_info['Name'],
                'pack': pack or self.default_pack,
                'ref': req_info['Name'],
                'id': req_info['Name'],
                'runner_type': 'spincycle'
            })
        return tuple(req_list)

    def get_actions(self, pack=None):
        """
        :param pack: In st2 pack -> spin cycle requests
        :return: a list of
        <Action name=view_organizations,pack=trello,enabled=True,runner_type=python-script>
        to dict
        """
        if pack != self.default_pack:
            logger.error(f"Spin cycle has no idea of pack so the only `pack` we support are {self.default_pack}")
        req_list = self.spin_client.get_req_list()
        return self._build_action_from_req(req_list, pack=self.default_pack)

    def get_action(self, ref):
        """
        return
        <Action name=view_organizations,pack=trello,enabled=True,runner_type=python-script>
        to dict
        :param ref: spin cycle req type
        :return: req dict
        """
        try:
            if '.' in ref:
                raise Exception(f"spincycle has no support on pack: {ref}")
            req = self.spin_client.get_req_by_type(ref)
            return self._build_action_from_req([req])[0]
        except Exception as e:
            logging.error('get req from spin cycle with id {} schema error: {}'.format(ref, str(e)))
            return None

    def get_result_url(self, execution_id):
        return self.spin_client.get_req_result_url(execution_id)

    def _build_execution_from_req(self, trigger_resp, req_type):
        return {
            'req_id': req_type,
            'execution_date': trigger_resp['createdAt'],
            'msg': json.dumps(trigger_resp),
            'id': trigger_resp["id"],
            'provider': self.provider_type,
            'web_url': self.get_result_url(trigger_resp["id"])
        }

    def run_action(self, ref, parameters):
        msg = ''
        try:
            trigger_result = self.spin_client.create_and_start_req(ref, parameters)
            return self._build_execution_from_req(trigger_result, ref) if trigger_result else None, msg
        except Exception as e:
            logger.error(f'run req {ref} error: {str(e)}')
            return None, str(e)

    def generate_annotation(self, execution):
        if not execution:
            return
        return {
            'provider': self.provider_type,
            'id': execution['id'],
            'result_url': self.get_result_url(execution['id'])
        }

    def _format_exec_status(self, status):
        if status not in self.status_to_emoji:
            return self.status_to_emoji[0]
        else:
            return self.status_to_emoji[status]

    def _build_graph_of_req(self, req_id):
        try:
            graph_ascii = self.spin_client.get_ascii_graph_of_req(req_id, self.spin_req_status)
            graph_gen_success = True
            graph_gen_status = 3
        except Exception as e:
            graph_ascii = str(e)
            graph_gen_success = False
            graph_gen_status = 4

        return {
            'execution_id': f"{req_id}_build_graph",
            'created_at': str(datetime.datetime.now()),
            'updated_at': str(datetime.datetime.now()),
            'state': 'succeeded' if graph_gen_success else 'failed',
            'result': {
                'build_graph': {
                    'failed': not graph_gen_success,
                    'stderr': '',
                    'stdout': graph_ascii,
                    'return_code': 0 if graph_gen_success else 1,
                    'succeeded': graph_gen_success
                }
            },
            "id": f"{req_id}_build_graph",
            "name": f'{self.status_to_emoji[graph_gen_status]} build-graph-for-{req_id}'
        }

    def _build_result_from_req_exec(self, execution, execution_id, filter_status=None):
        result = {
            'status': self.spin_req_status[execution['state']],
            'start_timestamp': execution['startedAt'],
            'web_url': self.get_result_url(execution_id),
            'result': {
                'tasks': [self._build_graph_of_req(execution_id)],
                'req_id': execution_id
            },
            'id': execution_id,
        }
        all_jobs_log = self.spin_client.get_all_job_logs_by_req(execution_id)
        filter_status_num = (self.spin_status_to_num[stat] for stat in filter_status) if filter_status else None
        for job in all_jobs_log:
            if filter_status_num and job['state'] in filter_status_num:
                logger.debug(f"job {job['name']} skipped for in filter status list.")
                continue

            result['result']['tasks'].append({
                'execution_id': f"{execution_id}_{job['jobId']}",
                'created_at': f'{job["startedAt"]}',
                'updated_at': f'{job["finishedAt"]}',
                'state': 'succeeded' if job['state'] == self.spin_status_to_num['COMPLETE'] else 'failed',
                'result': {
                    job['name']: {
                        'failed': job['state'] == self.spin_status_to_num['FAIL'],
                        'stderr': job['stderr'],
                        'stdout': job['stdout'],
                        'return_code': job['exit'],
                        'succeeded': job['state'] == self.spin_status_to_num['COMPLETE']
                    }
                },
                "id": job['name'],
                "name": f'{self.status_to_emoji[job["state"]]} {job["name"]}-{job["jobId"]}-{job["try"]}'
            })

        return result

    def get_execution(self, execution_id):
        try:
            execution = self.spin_client.get_req(execution_id)
            return self._build_result_from_req_exec(execution, execution_id) if execution else None, ''
        except Exception as e:
            logger.error(f'get spin cycle execution from {execution_id}, error: {str(e)}')
            return None, str(e)

    def authenticate(self, user, password=None):
        logger.warning("spin cycle token is not supported! This is a fake token")
        return {'token': 'fake_token', 'user': user, 'expiry': ''}, 'gen token from spin cycle is not supported!'

    def get_user_roles(self, user=None):
        '''return a list of roles,
            e.g. ["admin"]
        '''
        logger.warning(f"spincycle have no support with roles, all of the requests are made by {SPINCYCLE_USERNAME}")
        # set spincycle roles to [] prevent none authorize op (sorry for SA admin
        roles = []
        return roles
