#!/usr/bin/env python
from helpful_scripts.es_scripts import help_find_es


import os
from utils import *
from optparse import OptionParser

cliparser = OptionParser()

cliparser.add_option("-w", "--workload", dest="workload",
                     help="This is the workload type that was run. See kube-burner-job label in created namespace for help")


(options, args) = cliparser.parse_args()


globalvars = {}
globalvars["workload"] = options.workload

def find_uuid( workload, uuid_hit_data):
    uuid_hit = help_find_es.find_uuid(workload,"base_line_uuids", uuid_hit_data)

    print(uuid_hit)

def find_uuid_metadata(workload): 

    try: 
        uuid = os.getenv("UUID")
        hits = help_find_es.find_uuid_data(workload,uuid)
        find_uuid( workload, hits)

        #will need to add clusterType for self-managed in future
    except Exception as e:
        return ""


find_uuid_metadata(globalvars["workload"])