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

# prometheus query constants
START_TIME = None
END_TIME = None

# jenkins env constants
JENKINS_URL = 'https://mastern-jenkins-csb-openshift-qe.apps.ocp-c1.prod.psi.redhat.com/'
JENKINS_JOB = None
flexy_build = None
JENKINS_SERVER = None
UUID = None

# elasticsearch constants
ES_URL = 'search-ocp-qe-perf-scale-test-elk-hcm7wtsqpxy7xogbu72bor4uve.us-east-1.es.amazonaws.com'
ES_USERNAME = os.getenv('ES_USERNAME')
ES_PASSWORD = os.getenv('ES_PASSWORD')
DUMP = False
UPLOAD_FILE = ''


def run(command):
    try:
        output = subprocess.check_output(command, shell=True, universal_newlines=True)
    except subprocess.CalledProcessError as exc:
        print("Status : ", command, exc.output)
        return exc.returncode, exc.output
    return 0, output.strip()

def get_jenkins_env_info():
    ''' gathers information about Jenkins env
        if build parameter data cannot be collected, only command line data will be included
    '''

    # intialize info object
    iso_timestamp = datetime.datetime.utcfromtimestamp(int(START_TIME)).isoformat() + 'Z'
    info = {
        "uuid": UUID,
        "metric_name": "jenkinsEnv",
        "data_type": "metadata",
        "iso_timestamp": iso_timestamp,
        "jenkins_job_name": JENKINS_JOB,
        "flexy_build_num": flexy_build,
        "profile": find_profile_name(),
        "ocp_version": get_oc_version(),
        "user": USER,
        "network_type": get_net_type(),
        "arch_type": get_arch_type(),
        "worker_count": get_node_count("node-role.kubernetes.io/worker="),
        "master_size": get_node_type("node-role.kubernetes.io/master="),
        "worker_size": get_node_type("node-role.kubernetes.io/worker="),
        "infra_node_count": get_node_count("node-role.kubernetes.io/infra="), 
        "workload_node_count": get_node_count("node-role.kubernetes.io/workload=")
    }

    # collect data from Jenkins server
    try:
        info= {}
        build_info = JENKINS_SERVER.get_build_info(JENKINS_JOB, flexy_build)
        logging.debug(f"Jenkins Build Info: {build_info}")
        build_actions = build_info['actions']
        build_parameters = None
        for action in build_actions:
            if action.get('_class') == 'hudson.model.ParametersAction':
                build_parameters = action['parameters']
                break
        if build_parameters is None:
            raise Exception("No build parameters could be found.")
        for param in build_parameters:
            del param['_class']
            if param.get('name') == 'WORKLOAD':
                info['workload'] = str(param.get('value'))
            if param.get('name') == 'VARIABLE':
                info['variable'] = int(param.get('value'))
    except Exception as e:
        logging.error(f"Failed to collect Jenkins build parameter info: {e}")
    return info


def get_node_type(node_type):

    return_code, node_name = run(f"oc get node -l {node_type} -o name | HEAD -n1")
    node_instance = '.metadata.labels."node.kubernetes.io/instance-type"'
    return_code, node_type = run(f"oc get {node_name} -o json | jq '{node_instance}'")
    if return_code == 0:
        return node_type
    else:
        return 0

def get_node_count(label):
    return_code, node_count = run(f"oc get node -l {label} -o name | wc -l")
    if return_code == 0:
        return node_count
    else:
        return 0

def get_oc_version():
    return_code, cluster_version_str = run("oc get clusterversion --no-headers | awk '{print $2}'")
    if return_code == 0:
        return cluster_version_str
    else:
        print("Error getting clusterversion")

def get_net_type(): 
    net_status, network_type_string = run("oc get network cluster -o jsonpath='{.status.networkType}'")

    return network_type_string

def get_arch_type():
    node_status, node_name=run("oc get node --no-headers | grep master| head -1| awk '{print $1}'")
    node_name = node_name.strip()
    arch_type_status, architecture_type = run("oc get node " + str(node_name) + " --no-headers -ojsonpath='{.status.nodeInfo.architecture}'")
    return architecture_type

def get_worker_num():
    return_code, worker_count = run("oc get nodes | grep worker | wc -l | xargs")
    if return_code != 0:
        worker_count = "ERROR"
    if scale == "true":
        worker_count = str(int(worker_count.strip()) - 1)
    else:
        worker_count = worker_count.strip()
    return worker_count


def find_profile_name():
    profile_var_loc = os.getenv('VARIABLES_LOCATION')
    inds = [i for i,c in enumerate(profile_var_loc) if c=='/']
    sub_profile = profile_var_loc[inds[-2] +1:]
    print('sub profile ' + str(sub_profile))
    return sub_profile


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
        metric_name = item.get('metric_name')
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

def main():

    # get jenkins env data if applicable
    if JENKINS_SERVER is not None:
        RESULTS["data"].append(get_jenkins_env_info())

    # log success if no issues
    logging.info(f"Data captured successfully")

    # either dump data locally or upload it to Elasticsearch
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    if DUMP:
        dump_data_locally(timestamp)
        logging.info(f"Data written to {DATA_DIR}/data_{timestamp}.json")
    else:
        try:
            #elapsed_time = upload_data_to_elasticsearch()
            dump_data_locally(timestamp)
            #logging.info(f"Elasticsearch upload completed in {elapsed_time} seconds")
           
        except Exception as e:
            logging.error(f"Error uploading to Elasticsearch server: {e}\nA local dump to {DATA_DIR}/data_{timestamp}.json will be done instead")
            dump_data_locally(timestamp)
            # using exit code of 2 here so that Jenkins pipeline can unqiuely identify this error
            sys.exit(2)

    # exit if no issues
    sys.exit(0)


if __name__ == '__main__':

    # initialize argument parser
    parser = argparse.ArgumentParser(description='PerfScale Post to Elasticsearch tool')

    # set logging flags
    parser.add_argument("--debug", default=False, action='store_true', help='Flag for additional debug messaging')

    # set standard mode flags
    standard = parser.add_argument_group("Standard Mode", "Connect to an OCP cluster and gather data")
    standard.add_argument("--user-workloads", default=False, action='store_true', help='Flag to query userWorkload metrics. Ensure FLP service and service-monitor are enabled and some network traffic exists.')
    standard.add_argument("--starttime", type=str, help='Start time for range query')
    standard.add_argument("--endtime", type=str, help='End time for range query')
    standard.add_argument("--jenkins-job", type=str, help='Jenkins job name to associate with run')
    standard.add_argument("--flexy-build", type=str, help='Jenkins build number to associate with run')
    standard.add_argument("--uuid", type=str, help='UUID to associate with run - if none is provided one will be generated')
    standard.add_argument("--dump", default=False, action='store_true', help='Flag to dump data locally instead of uploading it to Elasticsearch')
    standard.add_argument("--user",type=str,help="User who ran specified job")
    # set upload mode flags
    upload = parser.add_argument_group("Upload Mode", "Directly upload data from a previously generated JSON file to Elasticsearch")
    upload.add_argument("--upload-file", type=str, default='', help='JSON file to upload to Elasticsearch. Must be in the "data" directory. Note this flag runs the NOPE tool in Upload mode and causes all flags other than --debug to be IGNORED.')

    # parse arguments
    args = parser.parse_args()

    # set logging config
    DEBUG = args.debug
    if DEBUG:
        logging.basicConfig(level=logging.DEBUG)
        coloredlogs.install(level='DEBUG', isatty=True)
    else:
        logging.basicConfig(level=logging.INFO)
        coloredlogs.install(level='INFO', isatty=True)
    

    USER = args.user
    # if running in upload mode - immediately load JSON, upload, and exit
    UPLOAD_FILE = args.upload_file
    if UPLOAD_FILE != '':
        upload_file_path = DATA_DIR + '/' + UPLOAD_FILE
        logging.info(f"Running NOPE tool in Upload mode - data from {upload_file_path} will be uploaded to Elasticsearch")

        # read data json file
        with open(upload_file_path) as json_file:
            RESULTS = json.load(json_file)

        # upload data to elasticsearch
        try:
           # elapsed_time = upload_data_to_elasticsearch()
            logging.info(f"Elasticsearch upload completed in {elapsed_time} seconds")
            sys.exit(0)
        except Exception as e:
            logging.error(f"Error uploading to Elasticsearch server: {e}")
            sys.exit(1)

    # sanity check that kubeconfig is set
    result = subprocess.run(['oc', 'whoami'], capture_output=True, text=True)
    if result.returncode != 0:
        logging.error("Could not connect to cluster - ensure all the Prerequisite steps in the README were followed")
        sys.exit(1)

    # log prometheus range query constants
    START_TIME = args.starttime
    END_TIME = args.endtime
    if START_TIME == '' or END_TIME == '':
        logging.error("START_TIME and END_TIME are needed to proceed")
        sys.exit(1)
    else:
        logging.info("Parsed Start Time: " + datetime.datetime.utcfromtimestamp(int(START_TIME)).strftime('%I:%M%p%Z UTC on %m/%d/%Y'))
        logging.info("Parsed End Time:   " + datetime.datetime.utcfromtimestamp(int(END_TIME)).strftime('%I:%M%p%Z UTC on %m/%d/%Y'))

    # check if Jenkins arguments are valid and if so set constants
    raw_jenkins_job = args.jenkins_job
    raw_flexy_build = args.flexy_build
    if all(v is None for v in [raw_jenkins_job, raw_flexy_build]):
        JENKINS_SERVER = None
    elif any(v is None for v in [raw_jenkins_job, raw_flexy_build]):
        logging.error("JENKINS_JOB and flexy_build must all be used together or not at all")
        sys.exit(1)
    else:
        JENKINS_JOB = raw_jenkins_job
        flexy_build = int(raw_flexy_build)
        logging.info(f"Associating run with Jenkins job {JENKINS_JOB} build number {flexy_build}")
        try:
            JENKINS_SERVER = jenkins.Jenkins(JENKINS_URL)
        except Exception as e:
            logging.error("Error connecting to Jenkins server: ", e)
            sys.exit(1)

    # determine UUID
    UUID = args.uuid
    logging.info(f"UUID: {UUID}")

    # get token from cluster
    user_workloads = args.user_workloads

    # determine if data will be dumped locally or uploaded to Elasticsearch
    DUMP = args.dump
    if DUMP:
        logging.info(f"Data will be dumped locally to {DATA_DIR}")
    else:
        if (ES_USERNAME is None) or (ES_PASSWORD is None):
            logging.error("Credentials need to be set to upload data to Elasticsearch")
            sys.exit(1)
        logging.info(f"Data will be uploaded to Elasticsearch")

    # begin main program execution
    main()
