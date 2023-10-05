import subprocess
import yaml
from yaml.loader import SafeLoader
import os 
import update_es_uuid

def run(command):
    try:
        output = subprocess.check_output(command, shell=True, universal_newlines=True)
    except subprocess.CalledProcessError as exc:
        return exc.returncode, exc.output
    return 0, output.strip()

def get_node_type(node_type):

    return_code, node_name = run("oc get node -l " + str(node_type) +" -o name | awk 'NR==1{print $1}'")
    node_instance = '.metadata.labels."node.kubernetes.io/instance-type"'
    return_code, node_type = run(f"oc get {node_name} -o json | jq '{node_instance}'")
    if return_code == 0:
        return node_type
    else:
        return 0

def get_fips():

    return_code, fips_enabled = run("oc get cm cluster-config-v1 -n kube-system -o json | jq -r '.data' | grep 'fips'")
    if return_code == 0: 
        if fips_enabled != "":
            return str(True)
        else:
            return str(False)


def get_multi_az(node_type):
    zone_list = {}
    return_code, node_names = run("oc get node -l " + str(node_type) +" -o name | awk '{print $1}'")
    for node in node_names.split('\n'): 
        node_zone_label = '.metadata.labels."topology.kubernetes.io/zone"'
        return_code, node_zone = run(f"oc get {node} -o json | jq '{node_zone_label}'")
        if node_zone not in zone_list.keys():
            zone_list['node_zone'] = 1
    if len(zone_list.keys()) == 1:
        return True
    else:
        return False


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
    node_status, node_name=run("oc get node --no-headers | grep master| awk 'NR==1{print $1}'")
    node_name = node_name.strip()
    arch_type_status, architecture_type = run("oc get node " + str(node_name) + " --no-headers -ojsonpath='{.status.nodeInfo.architecture}'")
    return architecture_type

def get_worker_num():
    return_code, worker_count = run("oc get nodes | grep worker | wc -l | xargs")
    if return_code != 0:
        worker_count = "ERROR"
    worker_count = worker_count.strip()
    return worker_count


def find_cloud_name(launcher_vars):
    
    inds = [i for i,c in enumerate(launcher_vars) if c=='/']
    inds[-2]
    sub_profile = launcher_vars[inds[-2]+1:inds[-1]]
    print('sub profile ' + str(sub_profile))
    final_sub = sub_profile.split('-')[-1]
    print('fin sub profile ' + str(final_sub))
    return final_sub

def get_scale_profile_name(version, arch, net_type, worker_count):
    sub_version_split = version.split('.')
    sub_version = sub_version_split[0] + "." + sub_version_split[1]
    grep_string = ""
    if "arm" in arch.lower(): 
        grep_string += " | grep -i arm "
    else: 
        grep_string += " | grep -iv arm "
    if "ovn" in net_type.lower(): 
        grep_string += " | grep -i ovn"
    else: 
        grep_string += " | grep -iv ovn"
    launcher_vars = os.getenv('VARIABLES_LOCATION')
    cloud = find_cloud_name(launcher_vars)
    if cloud == "alicloud": 
        cloud = "alibaba"
    profiles = run(f"cd ci-profiles/scale-ci/{sub_version}; ls | grep -i {cloud} {grep_string}; cd ../../..")[1]
    profiles_list = profiles.split()
    worker_size = ""
    master_size = ""
    
    for p in profiles_list:
        # how to get around baremetal, reliability and sno profiles 
        profile_str = run(f"cat ci-profiles/scale-ci/{sub_version}/{p}")[1]
        profile_json = yaml.load(profile_str, Loader=SafeLoader)
        var_loc = profile_json['install']['flexy']['VARIABLES_LOCATION']
        if "scale" in profile_json.keys(): 
            for scale_size, scale_data in profile_json['scale'].items(): 
                
                if scale_size == "medium" and worker_count in [25, 65]: 
                    worker_size, master_size = get_node_sizing(scale_data)
                #need to get medium sizing for node-density-heavy and router-perf even though worker counts don't match
                if scale_data['SCALE_UP'] == worker_count:
                    worker_size, master_size = get_node_sizing(scale_data)

            if launcher_vars != "" and var_loc == launcher_vars:
                return p, worker_size, master_size, launcher_vars
    return "", "", "", var_loc

def get_node_sizing(scale_data): 
    worker_size = ""
    master_size = ""
    if "EXTRA_LAUNCHER_VARS" in scale_data.keys(): 
        print('type '+ str(type(scale_data['EXTRA_LAUNCHER_VARS'])))
        EXTRA_LAUNCHER_VARS = yaml.load(scale_data['EXTRA_LAUNCHER_VARS'], Loader=SafeLoader)
        if "vm_type_workers" in EXTRA_LAUNCHER_VARS.keys():
            worker_size = EXTRA_LAUNCHER_VARS['vm_type_workers']
        if "vm_type_masters" in EXTRA_LAUNCHER_VARS.keys():
            master_size = EXTRA_LAUNCHER_VARS['vm_type_masters']
    return worker_size, master_size

def find_uuid(workload, metric_name, uuid_data):

    
    search_params = {
        "metric_name": metric_name, 
        "workload": workload,
        "network_type": uuid_data['networkType'],
        "worker_count": int(uuid_data['workerNodesCount']),
        "platform": uuid_data['platform'],
        "worker_size": uuid_data['workerNodesType']

    }


    version = uuid_data['ocpVersion'][:4]
    search_wildcard = {
        "ocp_version": str(version) + "*"
    }
    hits = update_es_uuid.es_search(search_params, wildcard=search_wildcard)
    
    if len(hits) == 0: 
        return False
    else: 
        return hits[0]['_source']['uuid']