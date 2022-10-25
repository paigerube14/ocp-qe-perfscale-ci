from oauth2client.service_account import ServiceAccountCredentials
import gspread

from datetime import datetime
from pytz import timezone
import write_helper

def write_to_sheet(google_sheet_account, flexy_id, scale_ci_job, ran_jobs, failed_jobs, status, env_vars_file, nightly_type, profile, profile_sizing, user):
    scopes = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
    ]
    credentials = ServiceAccountCredentials.from_json_keyfile_name(google_sheet_account, scopes) #access the json key you downloaded earlier
    file = gspread.authorize(credentials) # authenticate the JSON key with gspread

    sheet = file.open_by_url("https://docs.google.com/spreadsheets/d/1Zp116e0goej2Q8TOF6o9AwsXbWd-WqCsmwhFA1SFdIk/edit?usp=sharing")

    index = 2
    flexy_url = f"https://mastern-jenkins-csb-openshift-qe.apps.ocp-c1.prod.psi.redhat.com/job/ocp-common/job/Flexy-install/{flexy_id}"
    cloud_type, install_type, network_type = write_helper.flexy_install_type(flexy_url)
    flexy_cell = f'=HYPERLINK("{flexy_url}","{flexy_id}")'

    ci_cell = f'=HYPERLINK("{scale_ci_job}","{ran_jobs}")'

    worker_count = write_helper.get_worker_num()

    return_code, worker_master = write_helper.run("oc get nodes | grep worker | grep master|  wc -l | xargs")
    worker_master = worker_master.strip()
    if return_code != 0:
        worker_master = "ERROR"
    sno = "no"
    if worker_master == "1":
        sno = "yes"

    cluster_version = write_helper.get_oc_version()
    tz = timezone('EST')
    row = [flexy_cell, cluster_version, profile, profile_sizing, worker_count, ci_cell, failed_jobs, str(write_helper.get_local_time()), status, write_helper.get_env_vars_from_file(env_vars_file), user]

    latest_version = cluster_version.split('.')
    print('cluster verison list ' + str(latest_version))
    if nightly_type == "nightly-scale":
        ws = sheet.worksheet(str(latest_version[0]) + "." + str(latest_version[1]))
    elif nightly_type == "nightly-longrun":
        ws = sheet.worksheet(str(latest_version[0]) + "." + str(latest_version[1]) + "longrun")
    ws.insert_row(row, index, "USER_ENTERED")
#write_to_sheet("/Users/prubenda/.secrets/perf_sheet_service_account.json", "124927", "https://mastern-jenkins-csb-openshift-qe.apps.ocp-c1.prod.psi.redhat.com/job/scale-ci/job/scale-nightly-regression/198/console", "['cluster-denstity'.'pod-density']", "['pod-density']", "TEST","env.out")