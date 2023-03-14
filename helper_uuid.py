import subprocess
import yaml
from yaml.loader import SafeLoader
import os 

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

def find_uuid(read_json, ocp_version, cluster_worker_count, network_type_string, cluster_arch_type):

    for json_versions, sub_vers_json in read_json.items(): 
        if str(json_versions) == str(ocp_version):
            for worker_count, sub_worker_json in sub_vers_json.items():
                if str(cluster_worker_count) == str(worker_count):
                    if "ovn" in network_type_string.lower():
                        network_type = "OVN"
                    else:
                        network_type = "SDN"
                    return sub_worker_json[network_type][cluster_arch_type]

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

            print("var_loc_split" + str(var_loc))
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