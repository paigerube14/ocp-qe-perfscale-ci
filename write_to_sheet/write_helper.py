import json
import subprocess
import datetime
import get_es_data
import os 

def run(command):
    try:
        print("command " + str(command))
        output = subprocess.check_output(command, shell=True, universal_newlines=True)
    except subprocess.CalledProcessError as exc:
        print("Status : ", command, exc.output)
        return exc.returncode, exc.output
    return 0, output.strip()


def transform_time_to_int(time):
    return int(datetime.datetime.strptime(time, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=datetime.timezone.utc).timestamp())
        

def get_env_vars_from_file(file_name): 
    with open(file_name, encoding='utf8', mode="r") as f:
        env_vars_string = f.read()
    return env_vars_string

def get_upgrade_duration():
    return_code, version_str = run("oc get clusterversion -o json")
    all_versions = []
    if return_code == 0:
        version_json = json.loads(version_str)
        earliesetStartingTime = datetime.max
        latestCompletiontime = datetime.min
        for item in version_json['items']:
            lastVersion = True
            counter = 0
            for hist in item['status']['history']:
                if (counter != 0) and ((len(item['status']['history']) - 1) == counter):
                    lastVersion = False
                counter += 1
                all_versions.append(hist['version'])
                start_time = hist['startedTime']
                if not hist['completionTime']:
                    latestCompletiontime = datetime.datetime.now()

                else:
                    end_time = hist['completionTime']
                    end_date_time = datetime.datetime.strptime(end_time[:-1], "%Y-%m-%dT%H:%M:%S")
                    if end_date_time > latestCompletiontime:

                        latestCompletiontime = end_date_time

                start_date_time = datetime.datetime.strptime(start_time[:-1], "%Y-%m-%dT%H:%M:%S")
                if (start_date_time < earliesetStartingTime) and lastVersion:
                    earliesetStartingTime = start_date_time

        time_elapsed = latestCompletiontime - earliesetStartingTime
        all_versions.reverse()
        return str(time_elapsed), all_versions
    return get_oc_version(), ""

def get_pod_latencies(uuid=""):
    if uuid != "":
        # In the form of [[json_data['quantileName'], json_data['avg'], json_data['P99']...]
        pod_latencies_list = get_es_data.get_pod_latency_data(uuid)
        if len(pod_latencies_list) != 0:
            avg_list = []
            p99_list = []
            for pod_info in pod_latencies_list:
                if len(pod_info) > 0:
                    avg_list.append(pod_info[1])
                    p99_list.append(pod_info[2])
            return avg_list
    return ["", "", "", ""]

def get_oc_version():
    return_code, cluster_version_str = run("oc get clusterversion --no-headers | awk '{print $2}'")
    if return_code == 0:
        return cluster_version_str
    else:
        print("Error getting clusterversion")


def get_fips():

    return_code, fips_enabled = run("oc get cm cluster-config-v1 -n kube-system -o json | jq -r '.data' | grep 'fips'")
    if return_code == 0: 
        if fips_enabled != "":
            return str(True)

    return str(False)

def get_arch_type():
    node_status, node_name=run("oc get node --no-headers | grep master| head -1| awk '{print $1}'")
    node_name = node_name.strip()
    arch_type_status, architecture_type = run("oc get node " + str(node_name) + " --no-headers -ojsonpath='{.status.nodeInfo.architecture}'")
    return architecture_type


def flexy_install_type(flexy_url):
    return_code, version_type_string = run('curl --noproxy "*" -s {}/consoleFull | grep "run_installer template -c private-templates/functionality-testing/aos-"'.format(flexy_url))
    if return_code == 0:
        version_lists = version_type_string.split("-on-")
        cloud_type = version_lists[1].split('/')[0]
        net_status, network_type_string = run("oc get network cluster -o jsonpath='{.status.networkType}'")
        node_status, node_name=run("oc get node --no-headers | grep master| head -1| awk '{print $1}'")
        node_name = node_name.strip()
        arch_type_status, architecture_type = run("oc get node " + str(node_name) + " --no-headers -ojsonpath='{.status.nodeInfo.architecture}'")

        architecture_type = architecture_type.strip()
        if "ovn" in network_type_string.lower():
            network_type = "OVN"
        else:
            network_type = "SDN"

        return cloud_type, architecture_type, network_type
    else:
        print("Error getting flexy installtion")
        return "", "", ""

def get_fips():

    return_code, fips_enabled = run("oc get cm cluster-config-v1 -n kube-system -o json | jq -r '.data' | grep 'fips'")
    if return_code == 0: 
        if fips_enabled != "":
            return str(True)

    return str(False)

def install_type():

    cloud_type = os.getenv("PLATFORM")
    cluster_type = os.getenv("CLUSTERTYPE")
    network_type = os.getenv("NETWORKTYPE")

    node_status, node_name=run("oc get node --no-headers | grep master| head -1| awk '{print $1}'")
    node_name = node_name.strip()
    arch_type_status, architecture_type = run("oc get node " + str(node_name) + " --no-headers -ojsonpath='{.status.nodeInfo.architecture}'")

    architecture_type = architecture_type.strip()

    fips_enabled = get_fips()
    return cloud_type, cluster_type, architecture_type, network_type, fips_enabled

def get_worker_num(scale="false"):
    return_code, worker_count = run("oc get nodes | grep worker | wc -l | xargs")
    if return_code != 0:
        worker_count = "ERROR"
    print("scale " + str(scale))
    if scale == "true":
        worker_count = str(int(worker_count.strip()) - 1)
    else:
        worker_count = worker_count.strip()
    return worker_count
#flexy_install_type("https://mastern-jenkins-csb-openshift-qe.apps.ocp-c1.prod.psi.redhat.com/job/ocp-common/job/Flexy-install/54597")