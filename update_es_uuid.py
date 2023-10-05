import os
import time
from utils import *
from optparse import OptionParser
from elasticsearch import Elasticsearch

# elasticsearch constants
ES_URL = 'search-ocp-qe-perf-scale-test-elk-hcm7wtsqpxy7xogbu72bor4uve.us-east-1.es.amazonaws.com'
ES_USERNAME = os.getenv('ES_USERNAME')
ES_PASSWORD = os.getenv('ES_PASSWORD')


def es_search(params, wildcard="", should="",must_not="", index='perfscale-jenkins-metadata',size=10, from_pos=0):
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
    
    # match a wildcard character
    must_not_list_data = []
    if wildcard != "": 
        for p, v in wildcard.items():
            wildcard_data= {}
            wildcard_data['wildcard'] = {}
            wildcard_data['wildcard'][p] = v
            filter_data.append(wildcard_data)
    # should exist
    if should != "": 
        bool_should = {}
        bool_should['bool'] = {}
        bool_should['bool']['should'] = []
        #print('should' + str(should))
        for p, v in should.items():
            should_data= {}
            should_data['should_phrase'] = {}
            should_data['should_phrase'][p] = v
            bool_should['bool']['should'].append(bool_should)

    # must not exist
    if must_not != "": 
        #print('must_not' + str(must_not))
        for p, v in must_not.items():
            must_not_data= {}
            must_not_data['exists'] = {}
            must_not_data['exists'][p] = v
            must_not_list_data.append(must_not_data)
        #print('must not' + str(must_not))
    #print("f ilter_data " + str(filter_data))
    search_result = es.search(index=index, body={"query": {"bool": {"filter": filter_data}},  "size": size, "from": from_pos})
    #print('serach resu.t' + str(search_result))
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

def update_data_to_elasticsearch(id, data_to_update, index = 'perfscale-jenkins-metadata'):
    ''' updates captured data in RESULTS dictionary to Elasticsearch
    '''

    # create Elasticsearch object and attempt index
    es = Elasticsearch(
        [f'https://{ES_USERNAME}:{ES_PASSWORD}@{ES_URL}:443']
    )

    start = time.time()
    
    doc = es.get(index=index, doc_type='_doc', id=id)
    ##print('doc '+ str(doc))
    for k,v in data_to_update.items(): 
        doc['_source'][k] = v
    response = es.update(index=index, doc_type='_doc', id=id, body={"doc": doc['_source']
    })
    ##print(f"Response back was {response}")
    end = time.time()
    elapsed_time = end - start

    # return elapsed time for upload if no issues
    return elapsed_time