from oauth2client.service_account import ServiceAccountCredentials
import gspread
import json
import subprocess
from datetime import datetime
import calendar
import os
from pytz import timezone
import get_es_data
import write_helper
import get_scale_output
import os
import write_scale_results_sheet
import yaml 
creation_time = ""
data_source = "QE%20kube-burner"
uuid = ""

def install_type():

    cloud_type = get_platform()
    net_status, network_type_string = write_helper.run("oc get network cluster -o jsonpath='{.status.networkType}'")
    node_status, node_name=write_helper.run("oc get node --no-headers | grep master| head -1| awk '{print $1}'")
    node_name = node_name.strip()
    arch_type_status, architecture_type = write_helper.run("oc get node " + str(node_name) + " --no-headers -ojsonpath='{.status.nodeInfo.architecture}'")

    architecture_type = architecture_type.strip()
    if "ovn" in network_type_string.lower():
        network_type = "OVN"
    else:
        network_type = "SDN"
    fips_enabled = get_fips()
    return cloud_type, architecture_type, network_type, fips_enabled


def get_platform():
    
    try: 
        return_code, cluster_config_str = write_helper.run("oc get cm cluster-config-v1 -n kube-system -o jsonpath='{.data.install-config}'")
        print('config str' + str(type(cluster_config_str)))
        cluster_config = yaml.load(cluster_config_str, Loader=yaml.SafeLoader)
        print('loads' + str(cluster_config))
        platform = list(cluster_config['platform'].keys())[0]
        print('plat' + str(platform))
    except: 
        platform = "unknown"
    return platform
        
def get_fips():

    return_code, fips_enabled = write_helper.run("oc get cm cluster-config-v1 -n kube-system -o json | jq -r '.data' | grep 'fips'")
    print('return code' + str(return_code))
    if return_code == 0: 
        if fips_enabled != "":
            return str(True)

    return str(False)

def write_prow_results_to_sheet():
    scopes = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
    ]
    google_sheet_account = os.getenv("GSHEET_KEY_LOCATION")
    credentials = ServiceAccountCredentials.from_json_keyfile_name(google_sheet_account, scopes) #access the json key you downloaded earlier
    file = gspread.authorize(credentials) # authenticate the JSON key with gspread
    sheet = file.open_by_url("https://docs.google.com/spreadsheets/d/1cciTazgmvoD0YBdMuIQBRxyJnblVuczgbBL5xC8uGuI/edit?usp=sharing")
    #open sheet
    index = 2

    job_parameters = os.getenv("ITERATIONS")
    job_type = os.getenv("WORKLOAD_TYPE")
    es_username = os.getenv("ES_USERNAME")
    es_password = os.getenv("ES_PASSWORD")

    global uuid
    uuid = write_scale_results_sheet.get_uuid()
    if job_type == "network-perf-v2":
        grafana_cell = write_scale_results_sheet.find_k8s_perf_uuid_url()
    elif job_type == "router-perf":
        uuid, metadata = write_scale_results_sheet.get_router_perf_uuid()
        grafana_cell = uuid
    elif job_type == "ingress-perf":
        grafana_cell = uuid
    else:
        print('call metadata')
        grafana_cell = write_scale_results_sheet.get_metadata_uuid()
    cloud_type, architecture_type, network_type, fips_enabled = install_type()
    
    version = write_helper.get_oc_version()
    tz = timezone('EST')

    worker_count = write_helper.get_worker_num()
    row = [version, grafana_cell, cloud_type, architecture_type, network_type, fips_enabled, worker_count]

    if job_type not in ["network-perf-v2", "router-perf", "ingress-perf"]:
        workload_args = write_scale_results_sheet.get_workload_params(job_type)
        if workload_args != 0:
            row.append(workload_args)
    elif job_type == "router-perf":
        row.append(str(metadata))

    if job_parameters:
        parameter_list = job_parameters.split(',')
        for param in parameter_list:
            if param:
                row.append(param)

    if job_type not in ["network-perf-v2","router-perf" ,"ingress-perf"]:
        creation_time = os.getenv("STARTTIME_STRING").replace(' ', "T") + ".000Z"
        print('get latency params ' + str(uuid) )
        print('get latency params ' + str(creation_time) )
        print('get latency params ' + str(es_username) )
        print('get latency params ' + str(es_password) )
        row.extend(write_helper.get_pod_latencies(uuid, creation_time, es_username,es_password))

    row.append(str(datetime.now(tz)))
    ws = sheet.worksheet(job_type)
    ws.insert_row(row, index, "USER_ENTERED")

#write_prow_results_to_sheet()

fips = get_fips()
print('fips ' + str(fips))