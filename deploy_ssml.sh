#!/bin/bash
helm_dir=${1}

oc label ns default security.openshift.io/scc.podSecurityLabelSync=false pod-security.kubernetes.io/enforce=privileged pod-security.kubernetes.io/audit=privileged pod-security.kubernetes.io/warn=privileged --overwrite

export CONSOLE_URL=$(oc get routes console -n openshift-console -o jsonpath='{.spec.host}')

export TOKEN=$(oc whoami -t)

echo "$CONSOLE_URL"
#curl -k "https://${CONSOLE_URL}/api/kubernetes/openapi/v2" -H "Cookie: openshift-session-token=${TOKEN}"  -H "Accept: application/json"  >> openapi.json

#edit rapidast config file
envsubst < values.yaml.template > dast_tool/helm/chart/value_test.yaml

${helm_dir}/helm install rapidast ./dast_tool/helm/chart -f ./dast_tool/helm/chart/value_test.yaml

# wait for pod to be completed or error


rapidast_pod=$(oc get pods -n default -l job-name=rapidast-job -o name)

oc wait --for=condition=Ready $rapidast_pod
while [[ $(oc get $rapidast_pod -o 'jsonpath={..status.conditions[?(@.type=="Ready")].status}') == "True" ]]; do
  echo "sleeping 5"
  sleep 5
  
done
pod_name=${rapidast_pod#*/}
oc logs $pod_name >> results/pod_logs.out

./results.sh rapidast-pvc results

phase=$(oc get $rapidast_pod -o jsonpath='{.status.phase}')

if [ $phase != "Succeeded" ]; then
    echo "Pod $rapidast_pod failed. Look at pod logs in archives (results/pod_logs.out)"
    exit 1
fi


