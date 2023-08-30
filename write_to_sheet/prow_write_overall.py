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
import update_es_uuid
creation_time = ""
data_source = "QE%20kube-burner"
uuid = ""


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

    task_id=os.getenv("BUILD_ID")
    job_id=os.getenv("JOB_NAME")
    prow_base_url = "https://prow.ci.openshift.org/view/gs/origin-ci-test/logs"
    build_url=prow_base_url + "/" + job_id+ "/"+ task_id
    #open sheet
    index = 2
    job_url_cell = f'=HYPERLINK("{build_url}","PROW")'
    tz = timezone('EST')
    row = [job_url_cell, str(datetime.now(tz))]
    
    ws = sheet.worksheet("4.14")
    ws.insert_row(row, index, "USER_ENTERED")

write_prow_results_to_sheet()