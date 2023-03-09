#!/bin/bash

if [[ ! -z $(kubectl get ns rapidast) ]]; then 
    kubectl delete ns rapidast
fi
kubectl create ns rapidast

ls dast_tool

console_url=$( oc get routes console -n openshift-console -o jsonpath='{.spec.host}')

token=$(oc whoami -t)

curl -k "https://${console_url}/api/kubernetes/openapi/v2" -H "Cookie: openshift-session-token=${token}"  -H "Accept: application/json"  >> openapi.json

ls -la

kubectl apply -f dast_tool/operator/olm/rapidast.yaml

#edit rapidast config file
envsubst < operator_configs/config.yaml.template > operator_configs/config/ssml_config.yaml

kubectl apply -f operator_configs/config/ssml_config.yaml

mkdir results
bash dast_tool/operator/results.sh rapidast-pvc results