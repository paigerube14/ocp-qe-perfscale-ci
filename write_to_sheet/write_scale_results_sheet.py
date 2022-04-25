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
import re

data_source = "Development-AWS-ES_ripsaw-kube-burner"
uuid = ""
def get_benchmark_uuid():
    return_code, benchmark_str = write_helper.run("oc get benchmark -n benchmark-operator -o json")
    if return_code == 0:
        benchmark_json = json.loads(benchmark_str)
        for item in benchmark_json['items']:
            if "uuid" in item['status']:
                global uuid
                uuid = item['status']['uuid']
                #if mutliple not sure what to do
                creation_time = item['metadata']['creationTimestamp']
                # "2021-08-10T13:53:20Z"
                d = datetime.strptime(creation_time[:-1], "%Y-%m-%dT%H:%M:%S")
                from_time = calendar.timegm(d.timetuple()) * 1000

                n_time = datetime.utcnow()
                to_time = calendar.timegm(n_time.timetuple()) * 1000

                if "Dog8code!@search-ocp-qe-perf-scale-test" in item['spec']['elasticsearch']['url']:
                    data_source = "SVTQE-kube-burner"
                return get_grafana_url(uuid, from_time, to_time)
            return ""
    return ""

def get_grafana_url(uuid, start_time, end_time):

    grafana_url = "http://grafana.rdu2.scalelab.redhat.com:3000/d/hIBqKNvMz/kube-burner-report?orgId=1&from={}&to={}&var-Datasource={}&var-sdn=openshift-sdn&var-sdn=openshift-ovn-kubernetes&var-job=All&var-uuid={}&var-namespace=All&var-verb=All&var-resource=All&var-flowschema=All&var-priority_level=All".format(str(start_time), str(end_time), data_source, uuid)
    grafana_cell = f'=HYPERLINK("{grafana_url}","{uuid}")'
    return grafana_cell

def get_metadata_uuid(job_output):
    start_time = get_es_data.get_project_creation_time()
    end_time = n_time = datetime.utcnow()
    to_time = calendar.timegm(n_time.timetuple()) * 1000

    with open(job_output, encoding='utf-8', mode="r") as f:
        job_output_string = f.read()
    metadata = job_output_string.split("Run Metadata:")[-1].split("}")[0]
    global uuid
    uuid, md_json = get_uuid_from_json(metadata)
    if uuid == "":
        uuid = job_output_string.split('"Finished execution with UUID: ')[-1].split('"')[0]
        if uuid == "":
            return ""
    return get_grafana_url(uuid, start_time, to_time)

def find_uperf_uuid_url(cluster_name):
    uuid = get_es_data.get_uuid_uperf(cluster_name)
    if uuid != "":
        return uuid
    return ""

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
    return url

def parse_output_for_sheet(job_output):

    with open(job_output, encoding='utf8', mode="r") as f:
        job_output_string = f.read()

    split_output = job_output_string.split('Google Spreadsheet link')

    #need to get not first one
    if job_output_string == split_output[-1]:
        print('didnt find google sheet link ')
    else:
        return get_url_out(split_output[-1])


def get_uuid_from_json(metadata):
    md_json = {}
    for md in metadata.split("\n"):
        md2 = md.replace('"', '').replace(',', '')
        md_split = md2.split(':')
        if len(md_split) >= 2:
            md_json[md_split[0].strip(" ")] = md_split[1].strip(' ')

    if "uuid" in md_json:
        return md_json['uuid'], md_json
    elif "UUID" in md_json:
        return md_json['UUID'], md_json
    else:
        return "", md_json

def get_router_perf_uuid(job_output):
    with open(job_output, encoding='utf-8', mode="r") as f:
        job_output_string = f.read()
    metadata = job_output_string.split("Workload finished, results:")[-1].split("}")[0]

    return get_uuid_from_json(metadata)


def write_to_sheet(google_sheet_account, flexy_id, ci_job, job_type, job_url, status, job_parameters, job_output):
    scopes = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
    ]
    credentials = ServiceAccountCredentials.from_json_keyfile_name(google_sheet_account, scopes) #access the json key you downloaded earlier
    file = gspread.authorize(credentials) # authenticate the JSON key with gspread
    #sheet = file.open("Test") #.Outputs
    sheet = file.open_by_url("https://docs.google.com/spreadsheets/d/1uiKGYQyZ7jxchZRU77lsINpa23HhrFWjphsqGjTD-u4/edit?usp=sharing")
    #open sheet

    ws = sheet.worksheet(job_type)

    index = 2

    flexy_cell='=HYPERLINK("https://mastern-jenkins-csb-openshift-qe.apps.ocp-c1.prod.psi.redhat.com/job/ocp-common/job/Flexy-install/'+str(flexy_id)+'","'+str(flexy_id)+'")'

    if job_type == "network-perf":
        return_code, CLUSTER_NAME=write_helper.run("oc get machineset -n openshift-machine-api -o=go-template='{{(index (index .items 0).metadata.labels \"machine.openshift.io/cluster-api-cluster\" )}}'")
        if return_code == 0:
            grafana_cell = find_uperf_uuid_url(CLUSTER_NAME)
        else:
            grafana_cell = ""
    elif job_type == "router-perf":
        if job_output:
            global uuid
            uuid, metadata = get_router_perf_uuid(job_output)
            grafana_cell = uuid
        else:
            grafana_cell = ""
    else:
        grafana_cell = get_benchmark_uuid()
        if not grafana_cell:
            grafana_cell = get_metadata_uuid(job_output)

    ci_cell = f'=HYPERLINK("{job_url}","{ci_job}")'
    version = write_helper.get_oc_version()
    tz = timezone('EST')

    row = [version, flexy_cell, ci_cell, grafana_cell, status]
    if job_type not in ["network-perf", "router-perf"]:
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

    if job_type not in ["etcd-perf", "network-perf", "router-perf"]:
        row.extend(write_helper.get_pod_latencies(uuid))

    if job_output:
        google_sheet_url = parse_output_for_sheet(job_output)
        if google_sheet_url:
            row.append(google_sheet_url)

    row.append(str(datetime.now(tz)))
    ws.insert_row(row, index, "USER_ENTERED")

#write_to_sheet("/Users/prubenda/.secrets/perf_sheet_service_account.json", 97141, 70, 'etcd-perf', "https://mastern-jenkins-csb-openshift-qe.apps.ocp-c1.prod.psi.redhat.com/job/scale-ci/job/e2e-benchmarking-multibranch-pipeline/job/etcd-perf/70/", "FAIL","", "")