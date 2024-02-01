#!/usr/bin/env python
import helper_uuid
import update_es_uuid


to_update = {
    
    "cloud": "azure",
    "platform": "Azure"
    }

# to_update = {
#     "clusterType": "self-managed"
# }
versions = ["9","10","11"]

versions = ["12", "13","14"]
must_not= { "field": "platform"}
# wildcard = {
#     "cloud": "*GCP*"
# }
#for version in versions: 
print('version' + str(versions))
search_params = {
    "metric_name": "base_line_uuids",

    "cloud": "azure"

}

size=20 
pos=0
while True:

    hits = update_es_uuid.es_search(search_params,must_not=must_not,size=size,from_pos=pos)
    pos +=size
    print('hits ' + str(len(hits)))
    #update_data_to_elasticsearch(id, data_to_update, index = 'perfscale-jenkins-metadata'):
    for hit in hits:
        print('hit')
        #print("hit" + str(hit))
        update_es_uuid.update_data_to_elasticsearch(hit['_id'], to_update, index = 'perfscale-jenkins-metadata')
    if size >= len(hits): 
        break
