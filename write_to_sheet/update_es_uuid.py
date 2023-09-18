import os
import time
from utils import *
from optparse import OptionParser
from elasticsearch import Elasticsearch

# elasticsearch constants
ES_URL = 'search-ocp-qe-perf-scale-test-elk-hcm7wtsqpxy7xogbu72bor4uve.us-east-1.es.amazonaws.com'
ES_USERNAME = os.getenv('ES_USERNAME')
ES_PASSWORD = os.getenv('ES_PASSWORD')


def es_search(params, index='perfscale-jenkins-metadata', size=10, from_pos=0):
     # create Elasticsearch object and attempt index
    es = Elasticsearch(
        [f'https://{ES_USERNAME}:{ES_PASSWORD}@{ES_URL}:443']
    )
    filter_data = []
    filter_data.append({
          "match_all": {}
        })
    for p, v in params.items():
        match_data= {}
        match_data['match_phrase'] = {}
        match_data['match_phrase'][p] = v
        filter_data.append(match_data)
    search_result = es.search(index=index, body={"query": {"bool": {"filter": filter_data}},  "size": size, "from": from_pos})
    hits = []
    if "hits" in search_result.keys() and "hits" in search_result['hits'].keys():
        return search_result['hits']['hits']
    return hits

def delete_es_entry(id):
    # create Elasticsearch object and attempt index
    es = Elasticsearch(
        [f'https://{ES_USERNAME}:{ES_PASSWORD}@{ES_URL}:443']
    )

    index = 'perfscale-jenkins-metadata'
    es.delete(index=index, doc_type='_doc', id=id)

def update_data_to_elasticsearch(id, data_to_update):
    ''' updates captured data in RESULTS dictionary to Elasticsearch
    '''

    # create Elasticsearch object and attempt index
    es = Elasticsearch(
        [f'https://{ES_USERNAME}:{ES_PASSWORD}@{ES_URL}:443']
    )

    start = time.time()

    index = 'perfscale-jenkins-metadata'
    doc = es.get(index=index, doc_type='_doc', id=id)
    #print('doc '+ str(doc))
    for k,v in data_to_update.items(): 
        doc['_source'][k] = v
    response = es.update(index=index, doc_type='_doc', id=id, body={"doc": doc['_source']
    })
    #print(f"Response back was {response}")
    end = time.time()
    elapsed_time = end - start

    # return elapsed time for upload if no issues
    return elapsed_time

# to_update = {"profile": "IPI-on-AWS.install.yaml"}
# update_data_to_elasticsearch("2l41vYYBRpj_T8Zagru2", to_update)
# update_data_to_elasticsearch("4F41vYYBRpj_T8ZahLvF", to_update)
# update_data_to_elasticsearch("7F41vYYBRpj_T8ZairsN", to_update)
# update_data_to_elasticsearch("5F41vYYBRpj_T8Zahrtk", to_update)

#delete_es_entry("5F41vYYBRpj_T8Zahrtk")