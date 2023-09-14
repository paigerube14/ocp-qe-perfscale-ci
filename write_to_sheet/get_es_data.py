import yaml
import json
import subprocess
import datetime
from pytz import timezone
import update_es_uuid

es_url = ""

def run(command):
    try:
        output = subprocess.check_output(command, shell=True, universal_newlines=True)
    except subprocess.CalledProcessError as exc:
        print("Status : FAIL", exc.returncode, exc.output)
        return exc.returncode, exc.output
    return 0, output

def get_metadata_es(index, search_params={}): 
    hits = update_es_uuid.es_search(search_params, index=index)
    print("hits[0]['_source']" + str(hits))
    return hits


def get_data_from_json(json_data):
    return [json_data['quantileName'], json_data['avg'], json_data['P99']]


def get_pod_latency_data(uuid):
        
    search_params = {
        "uuid": uuid,
        "metricName": "podLatencyQuantilesMeasurement"

    }

    list_response = get_metadata_es("ripsaw-kube-burner", search_params)
    data_info = []
    for hits in list_response:
        data_info.append(get_data_from_json(hits['_source']))
    if len(data_info) > 0:
        data_info = sorted(data_info, key=lambda kv:(kv[0], kv[1], kv[2]), reverse=True)
    return data_info


def get_es_url(username, password):
    global es_url
    es_url = f"https://{username}:{password}@search-ocp-qe-perf-scale-test-elk-hcm7wtsqpxy7xogbu72bor4uve.us-east-1.es.amazonaws.com"

def get_uuid_uperf(cluster_name):
    file_name = "uperf_find_uuid.json"

    #start time to be when benchmark-operator was created

    match_phrase = {
        "cluster_name": cluster_name
    }
    list_response = get_metadata_es("ripsaw-uperf-results", match_phrase)

    # want to find most recent, list should already be ordered
    for hits in list_response:
        if "_source" not in hits and "uuid" not in hits['_source']:
            return ""
        return hits['_source']['uuid']
    return ""
