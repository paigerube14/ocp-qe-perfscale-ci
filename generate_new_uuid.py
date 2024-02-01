import json
import helper_uuid
import os
import update_es_uuid
import yaml
from yaml.loader import SafeLoader
import help_write
import create_json_files

kb_workload_types_nd = [
    "cluster-density", 
    "pod-density", 
    "pod-density-heavy", 
    "node-density", 
    "max-namespaces",
    "node-density-heavy",
    "router-perf"
]


platforms = [
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

new_job_info = {}

def find_if_uuid_exists(workload, worker_count, var_loc):

    search_params = {
        "metric_name": "base_line_uuids", 
        "workload": workload,
        "worker_count": worker_count, 
        "LAUNCHER_VARS": var_loc
    }

    hits = update_es_uuid.es_search(search_params)
    if len(hits) == 0:
        return False
    return hits[0]['_source']['uuid']


def parse_json_file(cloud, workload, read_json): 

    for version, version_json in read_json.items(): 
        for worker_count, worker_json in version_json.items(): 
            for profile, job_info_json in worker_json.items():
                print('profile  ' + str(profile) + version + workload)
                var_loc = helper_uuid.find_launcher_vars_for_profile(profile,version)
                uuid = find_if_uuid_exists(workload, worker_count, var_loc)
                print('uuid ' + str(uuid))
                if uuid is False: 
                    global new_job_info
                    new_job_info[workload].append(job_info_json)
                if job_info_json['profile'] == "": 
                    print("PROFILE BLANK === UPDATING")
                    read_json[version][worker_count][profile]['profile'] = profile
                    help_write.write_new_json(workload + "/" + cloud + "flexy.json", read_json)


def gen_uuid_new_json(): 
    
    for workload in kb_workload_types_nd: 
        global new_job_info
        new_job_info[workload] = []
        for cloud in platforms: 
            read_json = help_write.read_json(workload, cloud, "flexy")
            parse_json_file(cloud, workload,read_json)
    
    help_write.write_new_json("new_uuid.json", new_job_info)

def update_entries_with_var_loc(): 

    for cloud in platforms: 
        hits = create_json_files.find_uuids(cloud)

        for hit in hits: 
            source_hit = hit['_source']
            if "LAUNCHER_VARS" not in source_hit.keys():
                print("updating!!!")
                id = hit['id']
                profile = source_hit['profile']
                version = source_hit['ocp_version']

                var_loc = helper_uuid.find_launcher_vars_for_profile(profile,version)
                data_to_update = {"LAUNCHER_VARS": var_loc}
                print('data ' + str(data_to_update))
                update_es_uuid.update_data_to_elasticsearch(id, data_to_update)

def update_entries_with_profile(): 

    for cloud in platforms: 

        for workload in kb_workload_types_nd: 
            hits = create_json_files.find_uuids(cloud)

            for hit in hits: 
                source_hit = hit['_source']
                if ".install.yaml" in source_hit['profile']:
                    print("updating!!!" + str(hit))
                    id = hit['_id']
                    profile = source_hit['profile'].replace('.install.yaml',"")

                    data_to_update = {"profile": profile}
                    print('data ' + str(data_to_update))
                    update_es_uuid.update_data_to_elasticsearch(id, data_to_update)

update_entries_with_profile()
