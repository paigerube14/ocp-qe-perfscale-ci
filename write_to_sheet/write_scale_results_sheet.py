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

creation_time = ""
data_source = "QE%20kube-burner"
uuid = ""
    
def get_grafana_url(uuid, start_time, end_time):
    start_time = start_time + "000"
    end_time = end_time + "000"
    grafana_url = "https://grafana.rdu2.scalelab.redhat.com:3000/d/FwPsenw7z/kube-burner-report?orgId=1&from={}&to={}&var-Datasource={}&var-sdn=OpenShiftSDN&var-job=All&var-uuid={}&var-namespace=All".format(str(start_time), str(end_time), data_source, uuid)
    print('grafana url ' + str(grafana_url))
    grafana_cell = f'=HYPERLINK("{grafana_url}","{uuid}")'
    return grafana_cell

def get_net_perf_grafana_url(uuid, start_time, end_time):
    start_time = start_time + "000"
    end_time = end_time + "000"
    data_source="QE+K8s+netperf"
    grafana_url = "https://grafana.rdu2.scalelab.redhat.com:3000/d/wINGhybVz/k8s-netperf?orgId=1&from={}&to={}&var-datasource={}&var-uuid={}&var-hostNetwork=true&var-service=All&var-parallelism=All&var-profile=All&var-messageSize=All".format(str(start_time), str(end_time), data_source, uuid)
    print('grafana url ' + str(grafana_url))
    grafana_cell = f'=HYPERLINK("{grafana_url}","{uuid}")'
    return grafana_cell

def get_ingress_perf_grafana_url(uuid, start_time, end_time):
    start_time = start_time + "000"
    end_time = end_time + "000"
    data_source="QE%20Ingress-perf"
    grafana_url = "https://grafana.rdu2.scalelab.redhat.com:3000/d/nlAhmRyVk/ingress-perf?orgId=1&from={}&to={}&var-datasource={}&var-uuid={}&var-termination=edge&var-termination=http&var-termination=passthrough&var-termination=reencrypt&var-latency_metric=avg_lat_us&var-compare_by=uuid.keyword&var-concurrency=18".format(str(start_time), str(end_time), data_source, uuid)
    print('grafana url ' + str(grafana_url))
    grafana_cell = f'=HYPERLINK("{grafana_url}","{uuid}")'
    return grafana_cell

def get_metadata_uuid():
    start_time = parse_output_for_starttime()
    to_time = os.getenv("ENDTIME_TIMESTAMP")

    global uuid
    uuid = get_uuid()
    print ("uuid " +str(uuid))
    return get_grafana_url(uuid, start_time, to_time)

def find_k8s_perf_uuid_url():
    start_time = parse_output_for_starttime()
    to_time = os.getenv("ENDTIME_TIMESTAMP")

    uuid = get_uuid()
    print ("uuid " +str(uuid))
    return get_net_perf_grafana_url(uuid, start_time, to_time)

def get_ingress_perf_grafana_url(uuid, start_time, end_time):
    start_time = start_time + "000"
    end_time = end_time + "000"
    data_source="QE%20Ingress-perf"
    grafana_url = "https://grafana.rdu2.scalelab.redhat.com:3000/d/nlAhmRyVk/ingress-perf?orgId=1&from={}&to={}&var-datasource={}&var-uuid={}&var-termination=edge&var-termination=http&var-termination=passthrough&var-termination=reencrypt&var-latency_metric=avg_lat_us&var-compare_by=uuid.keyword&var-concurrency=18".format(str(start_time), str(end_time), data_source, uuid)
    print('grafana url ' + str(grafana_url))
    grafana_cell = f'=HYPERLINK("{grafana_url}","{uuid}")'
    return grafana_cell

def find_uperf_uuid_url(cluster_name):

    uuid = get_es_data.get_uuid_uperf(cluster_name)
    if uuid != "":
        return uuid
    return ""

def parse_output_for_starttime():
    global creation_time
    creation_time = os.getenv("STARTTIME_TIMESTAMP")
    return creation_time

def get_workload_params(job_type):
    workload_args = get_scale_output.get_output(job_type)
    return workload_args


def get_nodes():
    return_code, cluster_version_str = write_helper.run("oc get nodes -o json")
    if return_code == 0:
        cluster_version_json = json.loads(cluster_version_str)
        for item in cluster_version_json['items']:
            for status in item['status']['conditions']:
                if "Progressing" == status['type']:
                    version = status['message'].split(" ")[-1]
                    return version
    else:
        print("Error getting nodes")
        return "ERROR"

def get_url_out(url_sub_string):

    url = url_sub_string.split("-> ")[-1].split("\n")[0]
    url = url.rstrip(" *")
    return url

def parse_output_file_name(job_output): 
    start_split = job_output.split('*')
    first_index = job_output.index('*')

    directory = write_helper.run("ls " + job_output[:first_index])[1].strip()
    job_output = job_output[:first_index]+ directory
    print('job outptu with dire' + str(job_output))
    file_title = write_helper.run("ls " + job_output)[1].strip()
    file_output_string = job_output[:first_index]+ directory + "/" + file_title
    print('final output string ' + str(file_output_string))
    with open(file_output_string, "r") as f:
        job_output_string = f.read()
    return job_output_string

def parse_output_for_sheet(job_output):

    job_output_string = parse_output_file_name(job_output)

    split_output = job_output_string.split('Google Spreadsheet link')

    #need to get not first one
    if job_output_string == split_output[-1]:
        print('didnt find google sheet link ')
        return ""
    else:
        return get_url_out(split_output[-1])

def get_uuid():
    global uuid
    uuid = os.getenv("UUID")
    return uuid

def get_router_perf_uuid(job_output=""):
    
    if job_output != "":
        job_output_string = parse_output_file_name(job_output)
        
        metadata = job_output_string.split("Workload finished, results:")[-1].split("}")
    else: 
        metadata = ""
    return get_uuid(), metadata


def get_ingress_perf_uuid():
    start_time = parse_output_for_starttime()
    to_time = os.getenv("ENDTIME_TIMESTAMP")

    uuid = get_uuid()
    print ("uuid " +str(uuid))
    
    return get_ingress_perf_grafana_url(uuid, start_time, to_time)

def write_to_sheet(google_sheet_account, flexy_id, ci_job, job_type, job_url, status, job_parameters, job_output, env_vars_file, user, es_username, es_password):
    scopes = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
    ]
    credentials = ServiceAccountCredentials.from_json_keyfile_name(google_sheet_account, scopes) #access the json key you downloaded earlier
    file = gspread.authorize(credentials) # authenticate the JSON key with gspread

    sheet = file.open_by_url("https://docs.google.com/spreadsheets/d/1uiKGYQyZ7jxchZRU77lsINpa23HhrFWjphsqGjTD-u4/edit?usp=sharing")

    #open sheet
    print("job type" + str(job_type))
    ws = sheet.worksheet(job_type)

    index = 2
    flexy_url = 'https://mastern-jenkins-csb-openshift-qe.apps.ocp-c1.prod.psi.redhat.com/job/ocp-common/job/Flexy-install/' +str(flexy_id)
    flexy_cell='=HYPERLINK("'+flexy_url+'","'+str(flexy_id)+'")'

    if job_type == "network-perf-v2":
        grafana_cell = find_k8s_perf_uuid_url()
    elif job_type == "ingress-perf":
        grafana_cell = get_ingress_perf_uuid()
    elif job_type == "network-perf":
        return_code, CLUSTER_NAME=write_helper.run("oc get machineset -n openshift-machine-api -o=go-template='{{(index (index .items 0).metadata.labels \"machine.openshift.io/cluster-api-cluster\" )}}'")
        if job_output:
            global uuid
            uuid, metadata = find_uperf_uuid_url(CLUSTER_NAME)
            grafana_cell = uuid
        else:
            grafana_cell = ""
    elif job_type == "router-perf":
        if job_output:
            uuid, metadata = get_router_perf_uuid(job_output)
            grafana_cell = uuid
        else:
            grafana_cell = ""
    else:
        print('call metadata')
        grafana_cell = get_metadata_uuid()

    ci_cell = f'=HYPERLINK("{job_url}","{ci_job}")'
    version = write_helper.get_oc_version()
    tz = timezone('EST')
    cloud_type, architecture_type, network_type = write_helper.flexy_install_type(flexy_url)

    worker_count = write_helper.get_worker_num()
    row = [version, flexy_cell, ci_cell, grafana_cell, status, cloud_type, architecture_type, network_type, worker_count]

    if job_type not in ["network-perf","network-perf-v2", "router-perf","ingress-perf"]:
        workload_args = get_workload_params(job_type)
        print('work')
        if workload_args != 0:
            row.append(workload_args)
    elif job_type == "router-perf":
        row.append(str(metadata))

    if job_parameters:
        parameter_list = job_parameters.split(',')
        for param in parameter_list:
            if param:
                row.append(param)

    if job_type not in ["etcd-perf", "network-perf", "network-perf-v2","router-perf","ingress-perf"]:
        row.extend(write_helper.get_pod_latencies(uuid))

    if job_output:

        google_sheet_url = parse_output_for_sheet(job_output)
        row.append(google_sheet_url)

    row.append(str(datetime.now(tz)))
    row.append(str(write_helper.get_env_vars_from_file(env_vars_file)))
    row.append(user)
    ws.insert_row(row, index, "USER_ENTERED")
