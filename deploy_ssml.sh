#!/bin/bash

if [[ ! -z $(kubectl get ns rapidast) ]]; then 
    kubectl delete ns rapidast
fi
kubectl create ns rapidast

ls dast_tool

console_url=$( oc get routes console -n openshift-console -o jsonpath='{.spec.host}')

token=$(oc whoami -t)

curl -k "https://${console_url}/api/kubernetes/openapi/v2" -H "Cookie: openshift-session-token=${token}"  -H "Accept: application/json"  >> openapi.json


#edit rapidast config file
envsubst < values.template > helm/chart/value.yaml

helm install rapidast ./helm/chart

bash results.sh rapidast-pvc results