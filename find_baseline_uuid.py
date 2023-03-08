#!/usr/bin/env python
import json
import helper_uuid
import update_es_uuid

import subprocess, json, os, yaml, sys
from utils import *
from optparse import OptionParser

cliparser = OptionParser()

cliparser.add_option("-w", "--workload", dest="workload",
                     help="This is the workload type that was run. See kube-burner-job label in created namespace for help")


(options, args) = cliparser.parse_args()


globalvars = {}
globalvars["workload"] = options.workload

def find_uuid(workload):
    
    network_type= helper_uuid.get_net_type()

    worker_count = helper_uuid.get_node_count("node-role.kubernetes.io/worker=")
    var_loc = os.getenv('VARIABLES_LOCATION')
    search_params = {
        "metric_name": "base_line_uuids", 
        "workload": workload,
        "LAUNCHER_VARS": os.getenv('VARIABLES_LOCATION'),
        "network_type": network_type,
        "worker_count": worker_count
    }

    hits = update_es_uuid.es_search(search_params)
    if len(hits) == 0: 
        search_params["LAUNCHER_VARS"] = var_loc.replace("-ci","")

        hits = update_es_uuid.es_search(search_params)
        print("hits " + str(hits))
    print(hits['_source']['uuid'])

find_uuid(globalvars["workload"])

