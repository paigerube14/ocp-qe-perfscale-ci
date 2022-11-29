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

kubectl apply -f operator_configs/catalog_source.yaml
kubectl apply -f operator_configs/subscription.yaml
kubectl apply -f operator_configs/operatorgroup.yaml

#edit rapidast config file

kubectl apply -f dast_tool/operator/config/samples/research_v1alpha1_rapidast.yaml

mkdir results
bash dast_tool/operator/results.sh rapidast-pvc results