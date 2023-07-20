#!/bin/bash
helm_dir=${1}

oc label ns default security.openshift.io/scc.podSecurityLabelSync=false pod-security.kubernetes.io/enforce=privileged pod-security.kubernetes.io/audit=privileged pod-security.kubernetes.io/warn=privileged --overwrite

export CONSOLE_URL=$(oc get routes console -n openshift-console -o jsonpath='{.spec.host}')

export TOKEN=$(oc whoami -t)

# path for local testing
#dast_tool_path=../rapidast/
dast_tool_path=./dast_tool
echo "$CONSOLE_URL"
#curl -k "https://${CONSOLE_URL}/api/kubernetes/openapi/v2" -H "Cookie: openshift-session-token=${TOKEN}"  -H "Accept: application/json"  >> openapi.json
mkdir results 
api_doc="open-api"
#for api_doc in $(ls ./apidocs); do 
echo "api doc $api_doc"
#  API_URL="https://raw.githubusercontent.com/paigerube14/ocp-qe-perfscale-ci/ssml/apidocs/$api_doc"
  #edit rapidast config file
  envsubst < values.yaml.template > $dast_tool_path/helm/chart/value_test.yaml

  ${helm_dir}/helm install rapidast $dast_tool_path/helm/chart -f $dast_tool_path/helm/chart/value_test.yaml

  # wait for pod to be completed or error
  rapidast_pod=$(oc get pods -n default -l job-name=rapidast-job -o name)
  echo "rapidast current pod $rapidast_pod"
  oc wait --for=condition=Ready $rapidast_pod --timeout=120s
  response=$($?)
  echo "response $response"
  oc get $rapidast_pod -o 'jsonpath={..status.conditions}'
  while [[ $(oc get $rapidast_pod -o 'jsonpath={..status.conditions[?(@.type=="Ready")].status}') == "True" ]]; do
    echo "sleeping 5"
    sleep 5
    
  done
  mkdir results/$api_doc
  cp $dast_tool_path/helm/chart/value_test.yaml results/$api_doc/value.yaml

  oc logs $rapidast_pod -n default >> results/$api_doc/pod_logs.out

  ./results.sh rapidast-pvc results/$api_doc
  # ${helm_dir}/helm uninstall rapidast 
  # oc delete pvc rapidast-pvc
#done

phase=$(oc get $rapidast_pod -o jsonpath='{.status.phase}')

if [ $phase != "Succeeded" ]; then
    echo "Pod $rapidast_pod failed. Look at pod logs in archives (results/*/pod_logs.out)"
    exit 1
fi


