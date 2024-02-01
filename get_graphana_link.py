#!/usr/bin/env python3

import os
from helpful_scripts.es_scripts import update_es_uuid


def find_workload_type( current_run_uuid):
    search_params = {
        "uuid": current_run_uuid
    }

    index = "perf_scale_ci*"
    
    hits = update_es_uuid.es_search(search_params, index=index)
    #print('hits ' + str(hits))
    if len(hits) > 0:
        workload_type = hits[0]['_source']['benchmark']
    else: 
        print('else')
        workload_type = find_workload_type_sub(current_run_uuid)
    return workload_type
    

def find_workload_type_sub( current_run_uuid):
    search_params = {
        "uuid": current_run_uuid
    }

    workload_index_map = { "kube-burner":"ripsaw-kube-burner" ,"ingress-perf":"ingress-perf*", "network-perf-v2":"k8s-netperf","router-perf":"router-test-results",
                          "network-perf":"ripsaw-uperf",}
    for k, v in workload_index_map.items(): 
        hits = update_es_uuid.es_search(search_params, index=v)
        #print('hits extra' + str(hits))
        if len(hits) > 0:
            return k
    return "Unknown"
    

def get_graphana(): 
    
    baseline_uuid = os.getenv("BASELINE_UUID")
    
    uuid = os.getenv("UUID")
    workload = find_workload_type( uuid)
    uuid_str = "&var-uuid=" + uuid
    if baseline_uuid != "" and baseline_uuid is not None:
        for baseline in baseline_uuid.split(","):
            uuid_str += "&var-uuid=" + baseline

    # might want to be able to loop through multiple baseline uuids if more than one is passed
    grafana_url_ending="&from=now-1y&to=now&var-platform=AWS&var-platform=Azure&var-platform=GCP&var-platform=IBMCloud&var-platform=AlibabaCloud&var-platform=VSphere&var-platform=rosa"
    if workload == "ingress-perf":
        print(f"grafana url https://grafana.rdu2.scalelab.redhat.com:3000/d/nlAhmRyVk/ingress-perf?orgId=1&var-datasource=QE%20Ingress-perf{uuid_str}&var-termination=edge&var-termination=http&var-termination=passthrough&var-termination=reencrypt&var-latency_metric=avg_lat_us&var-compare_by=uuid.keyword&var-clusterType=rosa&var-clusterType=self-managed{grafana_url_ending}")

    elif workload == "k8s-netperf" or workload == "network-perf-v2":
        print( "Need to find grafana url")
    else:
        print( f"grafana url https://grafana.rdu2.scalelab.redhat.com:3000/d/8wDGrVY4k/kube-burner-compare-update?orgId=1&var-Datasource=QE%20kube-burner&var-sdn=OVNKubernetes&var-workload={workload}&var-worker_nodes=&var-latencyPercentile=P99&var-condition=Ready&var-component=kube-apiserver{uuid_str}{grafana_url_ending}")

get_graphana()