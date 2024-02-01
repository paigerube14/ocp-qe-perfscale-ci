import json
import os

def write_new_json(file_name, read_json): 
    with open(file_name, "w") as f:
        f.write(json.dumps(read_json))

def read_json(workload, platform, extension=""):
    read_file_path = workload +"/" + platform + extension + '.json'
    if not os.path.exists(read_file_path):
        return {}
    with open(read_file_path, "r") as fr:
        read_str =fr.read()
        read_json = json.loads(read_str)
    return read_json