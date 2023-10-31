from oauth2client.service_account import ServiceAccountCredentials
import gspread
from datetime import datetime
import os
from pytz import timezone
import write_helper
import sys
import os
import json
import sys
creation_time = ""
data_source = "QE%20kube-burner"
uuid = ""


# vars here: https://gcsweb-ci.apps.ci.l2s4.p1.openshiftapps.com/gcs/origin-ci-test/pr-logs/pull/openshift_release/42837/rehearse-42837-periodic-ci-openshift-qe-ocp-qe-perfscale-ci-main-aws-4.14-ocp-qe-perfscale-aws-ci-tests-write/1697269049693573120/artifacts/ocp-qe-perfscale-aws-ci-tests-write/openshift-qe-write-perfscale-results-all/build-log.txt

def write_prow_results_to_sheet(results_file):
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

    task_id=os.getenv("BUILD_ID")
    job_id=os.getenv("JOB_NAME")

    # version 

    cluster_output, cluster_version=write_helper.run("oc get clusterversion -o jsonpath='{.items[0].status.desired.version}'")
    if cluster_output!= 0: 
        cluster_version = "Cluster Install Failed"


    worker_output, workers_count =write_helper.run("oc get nodes --ignore-not-found -l node-role.kubernetes.io/worker --no-headers=true | wc -l")
    if worker_output != 0: 
        workers_count = "Cluster Install Failed"
    print('cluster version ' + str(cluster_version) + ", "+ str(workers_count))

    cluster_type = os.getenv("CLUSTER_TYPE")
    job_type = os.getenv("JOB_TYPE")

    prow_base_url = "https://prow.ci.openshift.org/view/gs/origin-ci-test/"
    if job_type == "presubmit": 
        prow_base_url +="pr-logs/pull/openshift_release/" + os.getenv("PULL_NUMBER")
    else: 
        prow_base_url += "/logs"
    build_url=prow_base_url + "/" + job_id+ "/"+ task_id
    #open sheet

    find_version = "4." + job_id.split("4.")[-1].split("-")[0]
    index = 2
    job_url_cell = f'=HYPERLINK("{build_url}","{job_type}")'
    tz = timezone('EST')
    row = [job_url_cell,cluster_version, cluster_type, workers_count]
    # read through ran tests file
    # do oc commands to see if clsuter is up 
    with open(results_file, "r+") as f:
        result_str = f.read()
    result_json = json.loads(result_str)
    if len(result_json.keys()) == 0: 
        row.append("Cluster failed to run tests")
    else: 
        for k,v in result_json.items(): 
            row.append(k + ": " + v)
    
    row.append(str(datetime.now(tz)))
    ws = sheet.worksheet(find_version)
    ws.insert_row(row, index, "USER_ENTERED")


if __name__ == "__main__":
    print(f"Arguments count: {len(sys.argv)}")
    write_prow_results_to_sheet(sys.argv[1])