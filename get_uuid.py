from oauth2client.service_account import ServiceAccountCredentials
import gspread
import pandas as pd
import json
import helper_uuid
import os 

router_perf = {
    # extra-small, small, upgrade, medium
        "aws": [3, 20, 65],
        "azure": [3, 20, 50, 65],
        "gcp": [3, 20, 50, 65],
        "alicloud": [3, 20, 50, 65],
        "ibmcloud": [3, 20, 40],
        "vsphere": [3, 10, 20], 
        "nutanix": [3, 10, 27], 
        "baremetal": [3, 10, 20],
        "osp": [3, 20, 50]
        }

node_density_heavy = {
        "aws": [25],
        "azure": [25],
        "gcp": [25],
        "alicloud": [25],
        "ibmcloud": [25],
        "vsphere": [25], 
        "nutanix": [25], 
        "baremetal": [25],
        "osp": [25]
        }

kb_workload_types = {
    "cluster-density": 
    {
        "parameter": 4, "no_scale": False
    }, 
    "pod-density": 
    {
        "parameter": 200, "no_scale": False
    }, 
    "pod-density-heavy": 
    {
        "parameter": 200, "no_scale": False
    }, 
    "node-density": 
    {
        "parameter": 200, "no_scale": True
    }, 
    "max-namespaces": {
        "parameter": 30, "no_scale": False
    }
}

kb_workload_types_nd = {
    "cluster-density": 
    {
        "parameter": 4, "no_scale": False
    }, 
    "pod-density": 
    {
        "parameter": 200, "no_scale": False
    }, 
    "pod-density-heavy": 
    {
        "parameter": 200, "no_scale": False
    }, 
    "node-density": 
    {
        "parameter": 200, "no_scale": True
    }, 
    "max-namespaces": {
        "parameter": 30, "no_scale": False
    }
}

platforms = {
    # extra-small, small, upgrade, medium
        "aws": [3, 20, 50, 120],
        "azure": [3, 20, 50, 120],
        "gcp": [3, 20, 50, 120],
        "alicloud": [3, 20, 50, 120],
        "ibmcloud": [3, 20, 40],
        "vsphere": [3, 10, 20], 
        "nutanix": [3, 10, 20], 
        "baremetal": [3, 10, 20],
        "osp": [3, 20, 50],
        "osp": [3, 20, 50]
     }

network_types = ["OVN", "SDN"]
arch_types = ['arm64','amd64']

network_types = ["OVN","SDN"]
arch_types = ['amd64',"arm64"]
versions = ['4.9','4.10','4.11', '4.12','4.13']

google_sheet_account="/Users/prubenda/.secrets/perf_sheet_service_account.json"


def print_data_frame(data_frame): 

    print(data_frame[['Grafana URL', "OCP Version", "Network Type", "Cloud", "Worker Count"]])

def get_kube_burner_data_from_sheet( platforms, workload, parameter="", no_scale="" ):
    scopes = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
    ]

    credentials = ServiceAccountCredentials.from_json_keyfile_name(google_sheet_account, scopes) #access the json key you downloaded earlier
    file = gspread.authorize(credentials) # authenticate the JSON key with gspread

    sheet = file.open_by_url("https://docs.google.com/spreadsheets/d/1uiKGYQyZ7jxchZRU77lsINpa23HhrFWjphsqGjTD-u4/edit?usp=sharing")
    print('file open')
    ws = sheet.worksheet(workload)
    print('worksheet open')

    base_dataframe = pd.DataFrame(ws.get_all_records())

    print('dataframe open' + str(base_dataframe))
    if workload == 'router-perf':
        get_workload_router_yaml(platforms, base_dataframe, workload)
    else: 
        get_workload_yaml(platforms, base_dataframe, workload, parameter, no_scale)


def get_workload_router_yaml(platforms, base_dataframe, workload):
    for platform, node_counts in router_perf.items(): 
        dataframe = base_dataframe.copy(deep=True)
        
        platform_dataframe = dataframe.loc[dataframe['Cloud'] == platform,:]
        print('platform ' + str(platform))
        print('version count ' + str(platform_dataframe.shape[0]))
        workload_yaml = {}
        for version in versions:
            workload_yaml[version] = {}
            dataframe_version = platform_dataframe.loc[platform_dataframe["OCP Version"].str.contains(version),:]
            print('versioin ' + str(version))
            print('version count ' + str(dataframe_version.shape[0]))
            for node_count in node_counts:
                workload_yaml[version][str(node_count)] = {}
      
                node_count_df = dataframe_version.loc[dataframe_version["Worker Count"] == node_count]
                for network_type in network_types:
                    network_df = node_count_df.query("`Network Type` == @network_type")
                    for arch_type in arch_types:
                        profile, worker_size, master_size, var_loc = helper_uuid.get_scale_profile_name(version, platform, arch_type, network_type, node_count, "")
                        arch_df = network_df.query("`Arch Type` == @arch_type")
                        if not arch_df.empty:
                            grafana_url = arch_df.iloc[0]['UUID']
                            workload_yaml[version][str(node_count)][profile] = grafana_url
                        else: 
                            workload_yaml[version][str(node_count)][profile] = ""
   
        with open(workload + "/" + platform + ".json", "w") as f:
            f.write(json.dumps(workload_yaml))

def get_workload_yaml(platforms, base_dataframe, workload, parameter, no_scale):
    for platform, node_counts in platforms.items(): 
        dataframe = base_dataframe.copy(deep=True)
        platform_dataframe = dataframe.loc[dataframe['Cloud'] == platform,:]

        print("data frame " + str(len(platform_dataframe)))
        workload_yaml = {}
        for version in versions:
            workload_yaml[version] = {}
            dataframe_version = platform_dataframe.loc[platform_dataframe["OCP Version"].str.contains(version),:]
            print("data frame vs" + str(version) + str(len(dataframe_version)))
            for node_count in node_counts:
                workload_yaml[version][str(node_count)] = {}
      
                node_count_df = dataframe_version.loc[dataframe_version["Worker Count"] == node_count]
                if no_scale: 
                    nodes_info_df = node_count_df.loc[node_count_df["PODS_PER_NODE"] >= node_count_df["Worker Count"],:]
                else: 
                    nodes_info_df = node_count_df.loc[node_count_df["Params"] >= parameter * node_count_df["Worker Count"],:]

                
                for network_type in network_types:
                    network_df = nodes_info_df.query("`Network Type` == @network_type")
                    for arch_type in arch_types:
                        profile, worker_size, master_size, var_loc = helper_uuid.get_scale_profile_name(version, platform, arch_type, network_type, node_count, "")
                        if profile != "": 
                            workload_yaml[version][str(node_count)][profile] = {}
                            arch_df = network_df.query("`Arch Type` == @arch_type")
                            if not arch_df.empty:
                                grafana_url = arch_df.iloc[0]['Grafana URL']
                                workload_yaml[version][str(node_count)][profile] = grafana_url
                            else: 
                                workload_yaml[version][str(node_count)][profile] = ""
   
        with open(workload + "/" + platform + ".json", "w") as f:
            f.write(json.dumps(workload_yaml))


# for workload, param_dict in kb_workload_types.items():
#     isExist = os.path.exists(workload)
#     if not isExist:
#         helper_uuid.run('mkdir ' + str(workload))
#     get_kube_burner_data_from_sheet(platforms, workload, param_dict['parameter'], param_dict['no_scale'])

# workload = "node-density-heavy"
# isExist = os.path.exists(workload)
# if not isExist:
#     helper_uuid.run('mkdir ' + str(workload))
# get_kube_burner_data_from_sheet(node_density_heavy, workload, 245, True)


workload = "router-perf"
isExist = os.path.exists(workload)
if not isExist:
    helper_uuid.run('mkdir ' + str(workload))
get_kube_burner_data_from_sheet(router_perf,workload)

# workload = "network-perf"
# isExist = os.path.exists(workload)
# if not isExist:
#     helper_uuid.run('mkdir ' + str(workload))
# get_kube_burner_data_from_sheet(workload)