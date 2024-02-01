#/!/bin/bash

export CONFIG_LOC=${PWD}/configs
export TOLERANCE_LOC=${PWD}/tolerancy-configs

cd e2e-benchmarking/utils

if [[ -n "$BASELINE_UUID" ]]; then
    echo "setting baseline server"
    export ES_SERVER_BASELINE=$ES_SERVER
    # might want to be able to loop through multiple baseline uuids if more than one is passed
    grafana_url_ending="&from=now-1y&to=now&var-platform=AWS&var-platform=Azure&var-platform=GCP&var-platform=IBMCloud&var-platform=AlibabaCloud&var-platform=VSphere&var-platform=rosa"
    if [[ $WORKLOAD == "ingress-perf" ]]; then
        echo "grafana url https://grafana.rdu2.scalelab.redhat.com:3000/d/nlAhmRyVk/ingress-perf?orgId=1&var-datasource=QE%20Ingress-perf&var-uuid=${UUID}&var-uuid=${BASELINE_UUID}&var-termination=edge&var-termination=http&var-termination=passthrough&var-termination=reencrypt&var-latency_metric=avg_lat_us&var-compare_by=uuid.keyword&var-clusterType=rosa&var-clusterType=self-managed${grafana_url_ending}"

    elif [[ $WORKLOAD == "k8s-netperf" ]]; then
        echo "Need to fid grafana url"
    else
        echo "grafana url https://grafana.rdu2.scalelab.redhat.com:3000/d/8wDGrVY4k/kube-burner-compare-update?orgId=1&var-Datasource=QE%20kube-burner&var-sdn=OVNKubernetes&var-workload=${WORKLOAD}&var-worker_nodes=&var-latencyPercentile=P99&var-condition=Ready&var-component=kube-apiserver&var-uuid=${UUID}&var-uuid=${BASELINE_UUID}${grafana_url_ending}"

    fi
fi

ls

ls /tmp/${WORKLOAD}-${UUID}

rm -rf /tmp/${WORKLOAD}-${UUID}
rm -rf *.csv
echo "ls remove"
ls
source compare.sh
mkdir results

COMPARISON_OUTPUT_LIST=""

if [[ ( -n $TOLERANCY_RULES_PARAM ) && ( -z "$BASELINE_UUID" ) ]]; then 
    echo "Wanted to compare using tolerancy rules but no baseline uuid found"
    echo "Won't run comparison"
    exit 0
elif [[ ${UUID} == ${BASELINE_UUID} ]]; then 
    echo "Not running comparison as uuid and baseline are the same"
    exit 0
fi

export COMPARISON_CONFIG=${COMPARISON_CONFIG_PARAM}
export TOLERANCY_RULES=${TOLERANCY_RULES_PARAM}

echo $CONFIG_LOC
run_benchmark_comparison
failed_comparison=$?

cp *.csv results/
cd ../..

echo "failed comparisons: $failed_comparison"
if [[ $failed_comparison -ne 0 ]]; then
    exit 1
else 
    exit 0
fi