import json
import helper_uuid

from utils import *
from optparse import OptionParser

cliparser = OptionParser()

cliparser.add_option("-f", "--flexy_template", dest="flexy_template",
                     help="This is the template type of what built the cluster.",
                     )
cliparser.add_option("-w", "--workload", dest="workload",
                     help="This is the workload type that was run. See kube-burner-job label in created namespace for help")
cliparser.add_option("-u", "--uuid", dest="uuid",
                     help="This is the workload type that was run. See kube-burner-job label in created namespace for help")

(options, args) = cliparser.parse_args()


globalvars = {}
globalvars["flexy_template"] = options.flexy_template
globalvars["workload"] = options.workload
globalvars["uuid"] = options.uuid

def update_with_current_uuid(uuid, workload, flexy_template ): 
    split_temp =helper_uuid.split_flexy_temp(flexy_template)
    
    platform = split_temp[1]
    # use helper functions from write to get data of interst
    with open(workload + "/" + platform + ".json", "r") as fr:
        read_str =fr.read()
        read_json = json.loads(read_str)

    ocp_version = split_temp[0]
    cluster_worker_count = helper_uuid.get_worker_num() 
    cluster_arch_type = helper_uuid.get_arch_type()
    network_type = split_temp[2]
    found_uuid = helper_uuid.find_uuid(read_json, ocp_version, cluster_worker_count, network_type, cluster_arch_type)
    
    if found_uuid == "":
        network_type = network_type[-3:].upper()
        read_json[ocp_version][cluster_worker_count][network_type][cluster_arch_type] = uuid
    
    with open(workload + "/" + platform + ".json", "w") as f:
        f.write(json.dumps(read_json))

    with open(workload + "/update.json", "w") as f:
        f.write(json.dumps(read_json))

update_with_current_uuid(globalvars["uuid"],globalvars["workload"],globalvars["flexy_template"])