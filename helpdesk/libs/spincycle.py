# -*- coding: utf-8 -*-

import logging
import json
import tempfile
import subprocess
import os

import requests

from helpdesk.config import SPINCYCLE_RM_URL
from helpdesk.libs.decorators import timed_cache

logger = logging.getLogger(__name__)


class SpinClientException(Exception):
    pass


class SpinClientCreateReqException(SpinClientException):
    pass


class SpinClientGetReqException(SpinClientException):
    pass


class SpinClientStopReqException(SpinClientException):
    pass


class SpinClientGetJobLogsException(SpinClientException):
    pass


class SpinClientGetJobLogFromReqException(SpinClientException):
    pass


class SpinClientGetRunningException(SpinClientException):
    pass


class SpinClientFindReqException(SpinClientException):
    pass


class SpinClientGetReqListException(SpinClientException):
    pass


class SpinCycleClient:
    """
    spincycle thin wrapper:
    ref: https://square.github.io/spincycle/v1.0/api/endpoints.html#find-requests-that-match-certain-conditions
    """
    def __init__(self, username, password, spin_rm_url=SPINCYCLE_RM_URL):
        self._username = username
        self._password = password
        self._auth = (self._username, self._password)
        self.spin_rm_url = spin_rm_url
        self.api_prefix = f"{self.spin_rm_url}/api/v1"

    def create_and_start_req(self, req_type, args):
        result = requests.post(
            url=f"{self.api_prefix}/requests",
            auth=self._auth,
            data=json.dumps({
                "type": req_type,
                "args": args
            }),
            headers={'Content-Type': 'application/json'},
    )
        return self._check_resp(result, SpinClientCreateReqException, msg='create and start request error: {}')

    @staticmethod
    def _check_resp(resp, exception=SpinClientException, msg='request error: {}'):
        try:
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"during spin client req error occurred: {str(e)}")
            raise exception(msg.format(resp.text))

    def get_req(self, req_id):
        result = requests.get(url=f"{self.api_prefix}/requests/{req_id}", auth=self._auth)
        return self._check_resp(result, SpinClientGetReqException)

    def stop_req(self, req_id):
        result = requests.put(url=f"{self.api_prefix}/requests/{req_id}/stop", auth=self._auth)
        return self._check_resp(result, SpinClientException)

    def get_all_job_logs_by_req(self, req_id):
        result = requests.get(url=f"{self.api_prefix}/requests/{req_id}/log", auth=self._auth)
        return self._check_resp(result, SpinClientGetJobLogsException)

    def get_req_result_url(self, req_id):
        return f"{self.api_prefix}/requests/{req_id}/log"

    def get_job_log_by_req(self, req_id, job_id):
        result = requests.get(
            url=f"{self.api_prefix}/requests/{req_id}/log/{job_id}", auth=self._auth)
        return self._check_resp(result, SpinClientGetJobLogFromReqException)

    def get_running_jobs_and_req(self):
        result = requests.get(url=f"{self.api_prefix}/status/running", auth=self._auth)
        return self._check_resp(result, SpinClientGetRunningException)

    def get_req_by_filter(self, filter_dict):
        result = requests.get(
            url=f"{self.api_prefix}/requests", params=filter_dict, auth=self._auth)
        return self._check_resp(result, SpinClientFindReqException)

    @timed_cache(minutes=10)
    def get_req_list(self):
        result = requests.get(url=f"{self.api_prefix}/request-list", auth=self._auth)
        return self._check_resp(result, SpinClientGetReqListException)

    def get_req_by_type(self, type):
        req_lists = self.get_req_list()
        for req in req_lists:
            if req["Name"] == type:
                return req
        else:
            raise SpinClientFindReqException("can not find req by type: {}".format(type))

    def get_job_chain_by_req_id(self, req_id):
        result = requests.get(url=f"{self.api_prefix}/requests/{req_id}/job-chain", auth=self._auth)
        return self._check_resp(result, SpinClientException)

    def get_ascii_graph_of_req(self, req_id, state_number_to_note=None):
        job_chains = self.get_job_chain_by_req_id(req_id)
        graph = job_chains["adjacencyList"]
        jobs = job_chains["jobs"]

        def node_format(node_id, jobs):
            return "{}_{}_{}".format(jobs[node_id]["name"], node_id, jobs[node_id]["state"])

        # make dot file
        _, tmp_file = tempfile.mkstemp()
        with open(tmp_file, 'w') as f:
            f.write(f"digraph {req_id} {{\n")
            for node in graph:
                for end_node in graph[node]:
                    f.write("    {} -> {{{}}};\n".format(node_format(node, jobs), node_format(end_node, jobs)))
            f.write("}\n")

        # use Graph::Easy generate ascii graph
        try:
            graph_ascii = subprocess.check_output("cat {} | graph-easy --from=dot".format(tmp_file), shell=True)
            graph_ascii = graph_ascii.decode('utf-8')
            if state_number_to_note:
                return "{}\n{}".format(' '.join((f'{k}: {v}' for k, v in state_number_to_note.items())), graph_ascii)
            return graph_ascii
        except subprocess.CalledProcessError as e:
            logger.error("Generate graph from Graph::Easy error: {}".format(e.output))
            raise e
        finally:
            os.remove(tmp_file)


if __name__ == '__main__':
    username = os.getenv("SPIN_USERNAME")
    password = os.getenv("SPIN_PASSWORD")

    assert username, "Username get from env error!"
    assert password, "Password get from env error!"

    client = SpinCycleClient(username, password)
    print(client.get_req_list())
    print(
        client.get_ascii_graph_of_req(
            "bq21siehlksg00eht6ng",
            state_number_to_note={
                0: "UNKNOWN",
                1: "PENDING",
                2: "RUNNING",
                3: "COMPLETE",
                4: "FAIL",
                5: "RESERVED",
                6: "STOPPED",
                7: "SUSPENDED"
            }))
