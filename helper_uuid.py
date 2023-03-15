import subprocess
import os
from utils import *
from elasticsearch import Elasticsearch

# elasticsearch constants
ES_URL = 'search-ocp-qe-perf-scale-test-elk-hcm7wtsqpxy7xogbu72bor4uve.us-east-1.es.amazonaws.com'
ES_USERNAME = os.getenv('ES_USERNAME')
ES_PASSWORD = os.getenv('ES_PASSWORD')

def run(command):
    try:
        output = subprocess.check_output(command, shell=True, universal_newlines=True)
    except subprocess.CalledProcessError as exc:
        return exc.returncode, exc.output
    return 0, output.strip()

def get_node_type(node_type):

    return_code, node_name = run("oc get node -l " + str(node_type) +" -o name | awk 'NR==1{print $1}'")
    node_instance = '.metadata.labels."node.kubernetes.io/instance-type"'
    return_code, node_type = run(f"oc get {node_name} -o json | jq '{node_instance}'")
    if return_code == 0:
        return node_type
    else:
        return 0

def get_node_count(label):
    return_code, node_count = run(f"oc get node -l {label} -o name | wc -l")
    if return_code == 0:
        return node_count
    else:
        return 0

def get_oc_version():
    return_code, cluster_version_str = run("oc get clusterversion --no-headers | awk '{print $2}'")
    if return_code == 0:
        return cluster_version_str
    else:
        print("Error getting clusterversion")

def get_net_type(): 
    net_status, network_type_string = run("oc get network cluster -o jsonpath='{.status.networkType}'")

    return network_type_string

def get_arch_type():
    node_status, node_name=run("oc get node --no-headers | grep master| awk 'NR==1{print $1}'")
    node_name = node_name.strip()
    arch_type_status, architecture_type = run("oc get node " + str(node_name) + " --no-headers -ojsonpath='{.status.nodeInfo.architecture}'")
    return architecture_type

def get_worker_num():
    return_code, worker_count = run("oc get nodes | grep worker | wc -l | xargs")
    if return_code != 0:
        worker_count = "ERROR"
    worker_count = worker_count.strip()
    return worker_count


def find_uuid(read_json, ocp_version, cluster_worker_count, network_type_string, cluster_arch_type):

    for json_versions, sub_vers_json in read_json.items(): 
        if str(json_versions) == str(ocp_version):
            for worker_count, sub_worker_json in sub_vers_json.items():
                if str(cluster_worker_count) == str(worker_count):
                    if "ovn" in network_type_string.lower():
                        network_type = "OVN"
                    else:
                        network_type = "SDN"
                    return sub_worker_json[network_type][cluster_arch_type]


def es_search(params):
     # create Elasticsearch object and attempt index
    es = Elasticsearch(
        [f'https://{ES_USERNAME}:{ES_PASSWORD}@{ES_URL}:443']
    )
    index = 'perfscale-jenkins-metadata'
    filter_data = []
    filter_data.append({
          "match_all": {}
        })
    for p, v in params.items():
        match_data= {}
        match_data['match_phrase'] = {}
        match_data['match_phrase'][p] = v
        filter_data.append(match_data)
    search_result = es.search(index=index, body={"query": {"bool": {"filter": filter_data}}})
    hits = []
    if "hits" in search_result.keys() and "hits" in search_result['hits'].keys():
        return search_result['hits']['hits']
    return hits