#!/usr/bin/env python
import json
import helper_uuid
import update_es_uuid
import help_write
import subprocess, json, os, yaml, sys
from utils import *

clouds = [
    "aws",
    "azure",
    "gcp",
    "alicloud",
    "ibmcloud",
    "vsphere", 
    "nutanix", 
    "baremetal",
    "osp"
]

def find_uuids(cloud_type):

    search_params = {
        "metric_name": "base_line_uuids",
        "cloud": cloud_type
    }

    res_hits = update_es_uuid.es_search(search_params)
    hits = res_hits
    while len(res_hits) >= 10:
        res_hits = update_es_uuid.es_search(search_params, from_pos=len(hits))
        hits.extend(res_hits)
    return hits

def find_print_all_es_uuids():
    for cloud in clouds: 
        hits = find_uuids(cloud)

        for hit in hits: 
            source_hit = hit['_source']
            workload = source_hit['workload']
            isExist = os.path.exists(workload)
            if not isExist:
                helper_uuid.run('mkdir ' + str(workload))
            read_json = help_write.read_json(workload, cloud)
            ocp_version = source_hit['ocp_version']
            split_version = ocp_version.split('.')
            sub_ocp_version = split_version[0] + "." + split_version[1]
            cluster_worker_count = str(source_hit['worker_count'])

            profile = source_hit['profile'].replace(".install.yaml", "")
            full_profile = profile + '.install.yaml'
            read_json = help_write.read_json(workload, cloud)
            if sub_ocp_version not in read_json.keys(): 
                read_json[sub_ocp_version] = {}
            if cluster_worker_count not in read_json[sub_ocp_version].keys(): 
                read_json[sub_ocp_version][cluster_worker_count] = {}
            if profile not in read_json[sub_ocp_version][cluster_worker_count].keys(): 
                read_json[sub_ocp_version][cluster_worker_count][profile] = {}
            read_json[sub_ocp_version][cluster_worker_count][profile] = source_hit
            if full_profile in read_json[sub_ocp_version][cluster_worker_count].keys(): 
                read_json[sub_ocp_version][cluster_worker_count].pop(full_profile)
            if len(read_json[sub_ocp_version][cluster_worker_count].keys()) == 0: 
                read_json[sub_ocp_version].pop(cluster_worker_count)

            if len(read_json[sub_ocp_version].keys()) == 0: 
                read_json.pop(sub_ocp_version)
            help_write.write_new_json(workload+ "/"+cloud + ".json", read_json)
