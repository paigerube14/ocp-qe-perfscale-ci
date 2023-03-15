#!/usr/bin/env python
import helper_uuid

import os
from utils import *
from optparse import OptionParser

cliparser = OptionParser()

cliparser.add_option("-p", "--parameters", dest="parameter",
                     help="This is the number of iterations ran for a workload")
cliparser.add_option("-w", "--workload", dest="workload",
                     help="This is the workload type that was run. See kube-burner-job label in created namespace for help")


(options, args) = cliparser.parse_args()


globalvars = {}
globalvars["workload"] = options.workload
globalvars["parameter"] = options.parameter

def find_uuid(workload, parameter):
    
    # might want to add parameter count here
    network_type= helper_uuid.get_net_type()

    worker_count = helper_uuid.get_node_count("node-role.kubernetes.io/worker=")
    var_loc = os.getenv('VARIABLES_LOCATION')
    search_params = {
        "metric_name": "base_line_uuids", 
        "workload": workload,
        "LAUNCHER_VARS": var_loc,
        "network_type": network_type,
        "worker_count": int(worker_count), 
        "parameters": parameter
    }

    hits = helper_uuid.es_search(search_params)
    
    if len(hits) == 0: 
        search_params["LAUNCHER_VARS"] = var_loc.replace("-ci","")
        hits = helper_uuid.es_search(search_params)
        if len(hits) == 0: 
            print("")
        else: 
            print(hits[0]['_source']['uuid'])
    else: 
        print(hits[0]['_source']['uuid'])

find_uuid(globalvars["workload"])

