#!/bin/bash

if [[ ! -z $(kubectl get ns rapidast) ]]; then 
    kubectl delete ns rapidast
fi
kubectl create ns rapidast

cp dast_git_lab/ocp-openapi-v2-1.23.5%2B3afdacb.json /dast_tool/config/

ls /dast_tool/config/openapi
cp dast_git_lab/config.yaml /dast_tool/config/config.yaml

console_url=$( oc get routes console -n openshift-console -o jsonpath='{.spec.host}')

token=$(oc whoami -t)
echo $token

curl -k "https://${console_url}/api/kubernetes/openapi/v2" -H "Cookie: openshift-session-token=${token}"  -H "Accept: application/json"  >> openapi.json

kubectl apply -f operator_configs/catalog_source.yaml
kubectl apply -f operator_configs/subscription.yaml
kubectl apply -f operator_configs/operatorgroup.yaml

kubectl apply -f dast_tool/operator/config/samples/research_v1alpha1_rapidast.yaml

mkdir results
bash results.sh rapidast-pvc results