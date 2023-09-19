#!/bin/bash

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
  envsubst < config_simple.yaml > $dast_tool_path/config/config.yaml
  cd $dast_tool_path
  ls
  python --version 
  pip install -r requirements.txt

  cat config/config.yaml
  ./rapidast.py --log-level debug --config config/config.yaml
  #mkdir results/$api_doc

  #./results.sh rapidast-pvc results/$api_doc

#done



