from oauth2client.service_account import ServiceAccountCredentials
import gspread
from datetime import datetime
import os
from pytz import timezone
import write_helper
import os
creation_time = ""
data_source = "QE%20kube-burner"
uuid = ""


# vars here: https://gcsweb-ci.apps.ci.l2s4.p1.openshiftapps.com/gcs/origin-ci-test/pr-logs/pull/openshift_release/42837/rehearse-42837-periodic-ci-openshift-qe-ocp-qe-perfscale-ci-main-aws-4.14-ocp-qe-perfscale-aws-ci-tests-write/1697269049693573120/artifacts/ocp-qe-perfscale-aws-ci-tests-write/openshift-qe-write-perfscale-results-all/build-log.txt

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

    task_id=os.getenv("BUILD_ID")
    job_id=os.getenv("JOB_NAME")
    cluster_type = os.getenv("CLUSTER_TYPE")

    prow_base_url = "https://prow.ci.openshift.org/view/gs/origin-ci-test/logs"
    build_url=prow_base_url + "/" + job_id+ "/"+ task_id
    #open sheet

    cluster_profile_dir = os.getenv("CLUSTER_PROFILE_DIR")
    write_helper.run("ls " + cluster_profile_dir)

    write_helper.run(f"cat {cluster_profile_dir}/*")
    # with open(cluster_profile_dir, "r") as r: 
    #     profile_str = r.read()
    # print('profile str ' + str(profile_str))
    
    
    # read through ran tests file
    # do oc commands to see if clsuter is up 

    # 


    find_version = "4." + job_id.split("4.")[-1].split("-")[0]
    index = 2
    job_url_cell = f'=HYPERLINK("{build_url}","PROW")'
    tz = timezone('EST')
    row = [job_url_cell, str(datetime.now(tz))]
    
    ws = sheet.worksheet(find_version)
    ws.insert_row(row, index, "USER_ENTERED")

write_prow_results_to_sheet()