from oauth2client.service_account import ServiceAccountCredentials
import gspread
import json
import subprocess
from datetime import datetime, timezone
import calendar
import os
import get_es_data
import write_helper
import get_scale_output
import os
import write_scale_results_sheet
import yaml 
import update_es_uuid
creation_time = ""
data_source = "QE%20kube-burner"
uuid = ""
        


def get_metadata_es(uuid, index="perf_scale_ci"): 
    search_params = {
        "uuid": uuid
    }
    
    hits = update_es_uuid.es_search(search_params, index=index)
    print("hits[0]['_source']" + str(hits[0]['_source']))
    return hits[0]['_source']


def transform_to_int(date_str):

    starttime_timestamp = int(datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc).timestamp())
    return str(starttime_timestamp)

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

    es_username = os.getenv("ES_USERNAME")
    es_password = os.getenv("ES_PASSWORD")
    job_type = os.getenv("WORKLOAD")
    job_parameters = os.getenv("ITERATIONS")

    global uuid
    uuid = write_scale_results_sheet.get_uuid()

    if job_type == "router-perf":

        metadata_uuid = get_metadata_es(uuid, index="router-test-results")

        worker_count = write_helper.get_worker_num()
        grafana_cell = uuid
        cluster_type = "self-managed"
        network_type = metadata_uuid['cluster.sdn']
        version = metadata_uuid['cluster.ocp_version']
        cloud_type = metadata_uuid['cluster.platform']
        job_url_cell= ""
    else: 
        metadata_uuid = get_metadata_es(uuid)

        startTime = metadata_uuid['startDate']
        creation_time = transform_to_int(startTime)
        
        endTime = metadata_uuid['endDate']
        finish_time = transform_to_int(endTime)
        job_type = metadata_uuid['benchmark']
        if job_type == "network-perf-v2" or job_type == "k8s-netperf":
            job_type= "network-perf-v2" 
            grafana_cell = write_scale_results_sheet.get_net_perf_grafana_url(uuid, creation_time, finish_time)

        elif job_type == "ingress-perf":
            uuid, metadata = write_scale_results_sheet.get_ingress_perf_grafana_url(uuid, creation_time, finish_time)
            grafana_cell = uuid
        else:
            print('call metadata')
            grafana_cell = write_scale_results_sheet.get_grafana_url(uuid, creation_time, finish_time)
            job_url = metadata_uuid['buildUrl']
        upstream_job_name = metadata_uuid['upstreamJob']
        job_url_cell = f'=HYPERLINK("{job_url}","{upstream_job_name}")'
        cloud_type = metadata_uuid['platform']
        network_type = metadata_uuid['networkType']
        cluster_type = metadata_uuid['clusterType']
        version = metadata_uuid['ocpVersion']   
        worker_count = metadata_uuid['workerNodesCount']

    architecture_type = write_helper.get_arch_type()
    fips_enabled = write_helper.get_fips()
    

    row = [version, grafana_cell, cluster_type, cloud_type, architecture_type, network_type, fips_enabled, worker_count]

    if job_url_cell: 
        row.extend(job_url_cell)

    if job_type not in ["network-perf-v2","router-perf","ingress-perf"]:
       
        print('get latency params ' + str(uuid) + str(startTime) )
        row.extend(write_helper.get_pod_latencies(uuid))

    row.append(str(datetime.now(timezone.utc)))
    ws = sheet.worksheet(job_type)
    ws.insert_row(row, index, "USER_ENTERED")

write_prow_results_to_sheet()