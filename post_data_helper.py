#!/usr/bin/env python3

import os
import sys
import json
import yaml
import uuid
import time
import urllib3
import pathlib
import jenkins
import logging
import argparse
import requests
import datetime
import subprocess
import coloredlogs
from elasticsearch import Elasticsearch


# disable SSL and warnings
os.environ['PYTHONHTTPSVERIFY'] = '0'
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# directory constants 
ROOT_DIR = str(pathlib.Path(__file__).parent.parent)
SCRIPT_DIR = ROOT_DIR + '/scripts'
DATA_DIR = ROOT_DIR + '/data'

USER = None
DEBUG = False
RESULTS ={}

# prometheus query constants
START_TIME = None
END_TIME = None


# elasticsearch constants
ES_URL = 'search-ocp-qe-perf-scale-test-elk-hcm7wtsqpxy7xogbu72bor4uve.us-east-1.es.amazonaws.com'
ES_USERNAME = os.getenv('ES_USERNAME')
ES_PASSWORD = os.getenv('ES_PASSWORD')

kb_workload_types_nd = [
  # "cluster-density", 
   #  "pod-density", 
#     "pod-density-heavy", 
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
    "osp"
]

def run(command):
    try:
        output = subprocess.check_output(command, shell=True, universal_newlines=True)
    except subprocess.CalledProcessError as exc:
        print("Status : ", command, exc.output)
        return exc.returncode, exc.output
    return 0, output.strip()

def post_current_es(workload, json_data):
    ''' gathers information about Jenkins env
        if build parameter data cannot be collected, only command line data will be included
    '''

    # intialize info object
    iso_timestamp = datetime.datetime.utcfromtimestamp(time.time()).isoformat() + 'Z'
    info = {
        "metric_name": "base_line_uuids",
        "data_type": "metadata",
        "iso_timestamp": iso_timestamp,
        "user": USER,
        "workload": workload
    }
    for k,v in json_data.items():
        info[k] = v
    return info

def dump_data_locally(timestamp, partial=False):
    ''' writes captured data in RESULTS dictionary to a JSON file
        file is saved to 'data_{timestamp}.json' in DATA_DIR system path if data is complete
        file is saved to 'partial_data_{timestamp}.json' in DATA_DIR system path if data is incomplete
    '''

    # ensure data directory exists (create if not)
    pathlib.Path(DATA_DIR).mkdir(parents=True, exist_ok=True)

    # write prometheus data to data directory
    if not partial:
        with open(DATA_DIR + f'/data_{timestamp}.json', 'w') as data_file:
            json.dump(RESULTS, data_file)
    else:
        with open(DATA_DIR + f'/partial_data_{timestamp}.json', 'w') as data_file:
            json.dump(RESULTS, data_file)

    # return if no issues
    return None

def upload_data_to_elasticsearch():
    ''' uploads captured data in RESULTS dictionary to Elasticsearch
    '''

    # create Elasticsearch object and attempt index
    es = Elasticsearch(
        [f'https://{ES_USERNAME}:{ES_PASSWORD}@{ES_URL}:443']
    )

    start = time.time()
    for item in RESULTS['data']:
        index = 'perfscale-jenkins-metadata'
        logging.debug(f"Uploading item {item} to index {index} in Elasticsearch")
        response = es.index(
            index=index,
            body=item
        )
        logging.debug(f"Response back was {response}")
    end = time.time()
    elapsed_time = end - start

    # return elapsed time for upload if no issues
    return elapsed_time

def add_to_result_data(workload, read_json): 
    RESULTS['data'].append(post_current_es(workload, read_json))

def add_to_result(workload, read_json): 
    for v_items in read_json.values():
        for w_items in v_items.values():
            for net_items in w_items.values(): 
                for final_json in net_items.values():
                    if len(final_json.keys()) > 1: 
                        RESULTS['data'].append(post_current_es(workload, final_json))

if __name__ == '__main__':

    # initialize argument parser
    parser = argparse.ArgumentParser(description='PerfScale Post to Elasticsearch tool')

    # set standard mode flags
    standard = parser.add_argument_group("Standard Mode", "Connect to an OCP cluster and gather data")
    standard.add_argument("--user",type=str,help="User who ran specified job")

    # parse arguments
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    coloredlogs.install(level='INFO', isatty=True)
    USER = args.user
    with open("new_uuid.json") as json_file:
        json_data = json.load(json_file)
    RESULTS['data'] = []
    for workload, workload_data in json_data.items(): 
        for info_data in workload_data: 
            # read data json file
            
            add_to_result_data(workload, info_data)
    # upload data to elasticsearch
    try:
        if len(RESULTS['data']) > 0:
            elapsed_time = upload_data_to_elasticsearch()
            print('result data to post '  + str(RESULTS['data']))
            logging.info(f"Elasticsearch upload completed in {elapsed_time} seconds")
    except Exception as e:
        logging.error(f"Error uploading to Elasticsearch server: {e}")
        sys.exit(1)
    sys.exit(0)
