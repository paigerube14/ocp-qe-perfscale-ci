@Library('flexy') _

// rename build
def userId = currentBuild.rawBuild.getCause(hudson.model.Cause$UserIdCause)?.userId
if (userId) {
  currentBuild.displayName = userId
}

pipeline {
  agent none

  parameters {
        string(name: 'BUILD_NUMBER', defaultValue: '', description: 'Build number of job that has installed the cluster.')
        string(name:'HOST_NETWORK_CONFIGS', defaultValue:'true', description:'If set to true, nodes and cluster is configured for hostnetwork testing.')
        string(name: 'PROVISION_OR_TEARDOWN', defaultValue: 'PROVISION', description:
        '''Set this to PROVISION to configure Firewall Rules otherwise TEARDOWN to remove Firewall Rules<br>
        This is useful for Hostnetwork Uperf Testing where you'd want to have certain firewall ports opened for your flexy cluster
        before you trigger the tests.<br>
        <b>REMEMBER: If you use this job, do not forget to Teardown, else Flexy-destroy for your cluster will fail</b>
        '''
        )
        string(name:'JENKINS_AGENT_LABEL',defaultValue:'oc48',description:
        '''
        scale-ci-static: for static agent that is specific to scale-ci, useful when the jenkins dynamic agen
 isn't stable<br>
        4.y: oc4y || mac-installer || rhel8-installer-4y <br/>
            e.g, for 4.8, use oc48 || mac-installer || rhel8-installer-48 <br/>
        3.11: ansible-2.6 <br/>
        3.9~3.10: ansible-2.4 <br/>
        3.4~3.7: ansible-2.4-extra || ansible-2.3 <br/>
        '''
        )
        string(name:'INFRA_NODES', defaultValue:'true', description:'If set to true, infra nodes machineset will be created, and options listed below will be used')
        text(name: 'ENV_VARS', defaultValue: '''PLEASE FILL ME''', description:'''<p>
               Enter list of additional Env Vars you need to pass to the script, one pair on each line. <br>
               e.g.<b>for AWS:</b><br>
               OPENSHIFT_INFRA_NODE_VOLUME_IOPS=0            <br>
               OPENSHIFT_INFRA_NODE_VOLUME_TYPE=gp2          <br>
               OPENSHIFT_INFRA_NODE_VOLUME_SIZE=100          <br>
               OPENSHIFT_INFRA_NODE_INSTANCE_TYPE=m5.12xlarge<br>
               OPENSHIFT_WORKLOAD_NODE_VOLUME_IOPS=0         <br>
               OPENSHIFT_WORKLOAD_NODE_VOLUME_TYPE=gp2       <br>
               OPENSHIFT_WORKLOAD_NODE_VOLUME_SIZE=500       <br>
               OPENSHIFT_WORKLOAD_NODE_INSTANCE_TYPE=m5.8xlarge<br>
               OPENSHIFT_PROMETHEUS_STORAGE_CLASS=gp2        <br>
               OPENSHIFT_ALERTMANAGER_STORAGE_CLASS=gp2      <br>
               e.g. <b>for Azure:</b><br>
               OPENSHIFT_INFRA_NODE_VOLUME_SIZE=128                <br>
               OPENSHIFT_INFRA_NODE_VOLUME_TYPE=Premium_LRS        <br>
               OPENSHIFT_INFRA_NODE_VM_SIZE=Standard_D48s_v3       <br>
               OPENSHIFT_WORKLOAD_NODE_VOLUME_SIZE=500             <br>
               OPENSHIFT_WORKLOAD_NODE_VOLUME_TYPE=Premium_LRS     <br>
               OPENSHIFT_WORKLOAD_NODE_VM_SIZE=Standard_D32s_v3    <br>
               OPENSHIFT_PROMETHEUS_STORAGE_CLASS=Premium_LRS  <br>
               OPENSHIFT_ALERTMANAGER_STORAGE_CLASS=Premium_LRS<br>
               e.g.<b>for GCP:</b><br>
               OPENSHIFT_INFRA_NODE_VOLUME_SIZE=100    <br>
               OPENSHIFT_INFRA_NODE_VOLUME_TYPE=pd-ssd <br>
               OPENSHIFT_INFRA_NODE_INSTANCE_TYPE=n1-standard-64 <br>
               OPENSHIFT_WORKLOAD_NODE_VOLUME_SIZE=500 <br>
               OPENSHIFT_WORKLOAD_NODE_VOLUME_TYPE=pd-ssd <br>
               OPENSHIFT_WORKLOAD_NODE_INSTANCE_TYPE=n1-standard-32 <br>
               GCP_PROJECT=openshift-qe <br>
               GCP_SERVICE_ACCOUNT_EMAIL=openshift-qe.iam.gserviceaccount.com <br>
               e.g. <b>for vSphere:</b><br>
               OPENSHIFT_INFRA_NODE_VOLUME_SIZE=120<br>
               OPENSHIFT_INFRA_NODE_CPU_COUNT=48<br>
               OPENSHIFT_INFRA_NODE_MEMORY_SIZE=196608<br>
               OPENSHIFT_INFRA_NODE_CPU_CORE_PER_SOCKET_COUNT=2<br>
               OPENSHIFT_INFRA_NODE_NETWORK_NAME=qe-segment<br>
               OPENSHIFT_WORKLOAD_NODE_VOLUME_SIZE=500<br>
               OPENSHIFT_WORKLOAD_NODE_CPU_COUNT=32<br>
               OPENSHIFT_WORKLOAD_NODE_MEMORY_SIZE=131072<br>
               OPENSHIFT_WORKLOAD_NODE_CPU_CORE_PER_SOCKET_COUNT=2<br>
               OPENSHIFT_WORKLOAD_NODE_NETWORK_NAME=qe-segment<br>
               e.g. <b>for Alicloud:</b><br>
               OPENSHIFT_INFRA_NODE_VOLUME_SIZE=100 <br>
               OPENSHIFT_INFRA_NODE_INSTANCE_TYPE=ecs.g6.13xlarge <br>
               OPENSHIFT_WORKLOAD_NODE_VOLUME_SIZE=500 <br>
               OPENSHIFT_WORKLOAD_NODE_INSTANCE_TYPE=ecs.g6.8xlarge <br>
               OPENSHIFT_PROMETHEUS_STORAGE_CLASS=alicloud-disk <br>
               OPENSHIFT_ALERTMANAGER_STORAGE_CLASS=alicloud-disk <br>
               e.g. <b>for Ibmcloud:</b><br>
               OPENSHIFT_INFRA_NODE_INSTANCE_TYPE=bx2d-48x192<br>
               OPENSHIFT_WORKLOAD_NODE_INSTANCE_TYPE=bx2-32x128<br>
               OPENSHIFT_PROMETHEUS_STORAGE_CLASS=ibmc-vpc-block-5iops-tier<br>
               OPENSHIFT_ALERTMANAGER_STORAGE_CLASS=ibmc-vpc-block-5iops-tier<br>
               <b>And ALWAYS INCLUDE(except for vSphere provider) this part, for Prometheus AlertManager, it may look like</b>:<br>
               OPENSHIFT_PROMETHEUS_RETENTION_PERIOD=15d<br>
               OPENSHIFT_PROMETHEUS_STORAGE_SIZE=500Gi  <br>
               OPENSHIFT_ALERTMANAGER_STORAGE_SIZE=20Gi <br></p>'''
            )
    }

  stages {
    stage('Configure given Flexy Cluster for HostNetwork tests'){
      agent { label params['JENKINS_AGENT_LABEL'] }
      steps{
        deleteDir()

        copyArtifacts(
            filter: '', 
            fingerprintArtifacts: true, 
            projectName: 'ocp-common/Flexy-install', 
            selector: specific(params.BUILD_NUMBER),
            target: 'flexy-artifacts'
        )
        script {
          buildinfo = readYaml file: "flexy-artifacts/BUILDINFO.yml"
          currentBuild.displayName = "${currentBuild.displayName}-${params.BUILD_NUMBER}"
          currentBuild.description = "Copying Artifact from Flexy-install build <a href=\"${buildinfo.buildUrl}\">Flexy-install#${params.BUILD_NUMBER}</a>"
          buildinfo.params.each { env.setProperty(it.key, it.value) }
        }
        ansiColor('xterm') {
        withCredentials([file(credentialsId: 'b73d6ed3-99ff-4e06-b2d8-64eaaf69d1db', variable: 'OCP_AWS'),
                         file(credentialsId: 'eb22dcaa-555c-4ebe-bb39-5b25628cc6bb', variable: 'OCP_GCP'),
                         file(credentialsId: 'ocp-azure', variable: 'OCP_AZURE')]) {
          sh label: '', script: '''
          if [[ $HOST_NETWORK_CONFIGS == "true" ]]; then
            # Get ENV VARS Supplied by the user to this job and store in .env_override
            echo "$ENV_VARS" > .env_override
            # Export those env vars so they could be used by CI Job
            set -a && source .env_override && set +a
            mkdir -p ~/.kube
            cp $WORKSPACE/flexy-artifacts/workdir/install-dir/auth/kubeconfig ~/.kube/config
            oc config view
            oc projects
            ls -ls ~/.kube/
            env
            set -x
            export CLUSTER_NAME=$(oc get machineset -n openshift-machine-api -o=go-template='{{(index (index .items 0).metadata.labels "machine.openshift.io/cluster-api-cluster" )}}')
            if [[ $(echo $VARIABLES_LOCATION | grep azure -c) > 0 ]]; then

              # create azure profile
              az login --service-principal -u `cat $OCP_AZURE | jq -r '.clientId'` -p "`cat $OCP_AZURE | jq -r '.clientSecret'`" --tenant `cat $OCP_AZURE | jq -r '.tenantId'`
              az account set --subscription `cat $OCP_AZURE | jq -r '.subscriptionId'`

              export NETWORK_NAME=$(az network nsg list -g  $CLUSTER_NAME-rg --query "[].name" -o tsv | grep "nsg")

              if [[ $PROVISION_OR_TEARDOWN == "PROVISION" ]]; then
                echo "Add Firewall Rules"
                az network nsg rule create -g $CLUSTER_NAME-rg --name scale-ci-icmp --nsg-name  $NETWORK_NAME --priority 100 --access Allow --description "scale-ci allow Icmp" --protocol Icmp --destination-port-ranges "*"
                az network nsg rule create -g $CLUSTER_NAME-rg --name scale-ci-ssh --nsg-name  $NETWORK_NAME --priority 103 --access Allow --description "scale-ci allow ssh" --protocol Tcp --destination-port-ranges "22"
                az network nsg rule create -g $CLUSTER_NAME-rg --name scale-ci-pbench-agent --nsg-name $NETWORK_NAME --priority 102 --access Allow --description "scale-ci allow pbench-agent" --protocol Tcp --destination-port-ranges "2022"
                az network nsg rule create -g $CLUSTER_NAME-rg --name scale-ci-net --nsg-name $NETWORK_NAME --priority 104 --access Allow --description "scale-ci allow tcp,udp network tests" --protocol "*" --destination-port-ranges "20000-20109"
                # Typically `net.ipv4.ip_local_port_range` is set to `32768 60999` in which uperf will pick a few random ports to send flags over.
                # Currently there is no method outside of sysctls to control those ports
                # See pbench issue #1238 - https://github.com/distributed-system-analysis/pbench/issues/1238
                az network nsg rule create -g $CLUSTER_NAME-rg --name scale-ci-hostnet --nsg-name $NETWORK_NAME --priority 106 --access Allow --description "scale-ci allow tcp,udp hostnetwork tests" --protocol "*" --destination-port-ranges "32768-60999"
                az network nsg rule list -g $CLUSTER_NAME-rg  --nsg-name $NETWORK_NAME  | grep scale
              fi

              if [[ $PROVISION_OR_TEARDOWN == "TEARDOWN" ]]; then
                echo "Remove Firewall Rules"
                az network nsg rule delete -g $CLUSTER_NAME-rg --nsg-name $NETWORK_NAME --name scale-ci-icmp
                az network nsg rule delete -g $CLUSTER_NAME-rg --nsg-name $NETWORK_NAME --name scale-ci-ssh
                az network nsg rule delete -g $CLUSTER_NAME-rg --nsg-name $NETWORK_NAME --name scale-ci-pbench-agent
                az network nsg rule delete -g $CLUSTER_NAME-rg --nsg-name $NETWORK_NAME --name scale-ci-net
                az network nsg rule delete -g $CLUSTER_NAME-rg --nsg-name $NETWORK_NAME --name scale-ci-hostnet
              fi

            fi
            if [[ $(echo $VARIABLES_LOCATION | grep gcp -c) > 0 ]]; then

              # login to service account
              gcloud auth activate-service-account `cat $OCP_GCP | jq -r '.client_email'`  --key-file=$OCP_GCP --project=`cat $OCP_GCP | jq -r '.project_id'`
              gcloud auth list
              gcloud config set account `cat $OCP_GCP | jq -r '.client_email'`

              export NETWORK_NAME=$(gcloud compute networks list  | grep $CLUSTER_NAME | awk '{print $1}')

              if [[ $NETWORK_NAME == "" ]]; then
                sub_cluster_name=$(echo ${CLUSTER_NAME%-*})
                 export NETWORK_NAME=$(gcloud compute networks list  | grep $sub_cluster_name | awk '{print $1}')

              fi
              echo $NETWORK_NAME
              if [[ $PROVISION_OR_TEARDOWN == "PROVISION" ]]; then
                echo "Add Firewall Rules"
                gcloud compute firewall-rules create $CLUSTER_NAME-scale-ci-icmp --network $NETWORK_NAME --priority 101 --description "scale-ci allow icmp" --allow icmp
                gcloud compute firewall-rules create $CLUSTER_NAME-scale-ci-ssh --network $NETWORK_NAME --direction INGRESS --priority 102  --description "scale-ci allow ssh" --allow tcp:22
                gcloud compute firewall-rules create $CLUSTER_NAME-scale-ci-pbench --network $NETWORK_NAME --direction INGRESS --priority 103 --description "scale-ci allow pbench-agents" --allow tcp:2022
                gcloud compute firewall-rules create $CLUSTER_NAME-scale-ci-net --network $NETWORK_NAME --direction INGRESS --priority 104 --description "scale-ci allow tcp,udp network tests" --rules tcp,udp:20000-20109 --action allow
                gcloud compute firewall-rules create $CLUSTER_NAME-scale-ci-hostnet --network $NETWORK_NAME --priority 105 --description "scale-ci allow tcp,udp hostnetwork tests" --rules tcp,udp:32768-60999 --action allow
                gcloud compute firewall-rules list | grep $CLUSTER_NAME
              fi

              if [[ $PROVISION_OR_TEARDOWN == "TEARDOWN" ]]; then
                echo "Remove Firewall Rules"
                gcloud compute firewall-rules delete $CLUSTER_NAME-scale-ci-icmp --quiet
                gcloud compute firewall-rules delete $CLUSTER_NAME-scale-ci-ssh --quiet
                gcloud compute firewall-rules delete $CLUSTER_NAME-scale-ci-pbench --quiet
                gcloud compute firewall-rules delete $CLUSTER_NAME-scale-ci-net --quiet
                gcloud compute firewall-rules delete $CLUSTER_NAME-scale-ci-hostnet --quiet
                gcloud compute firewall-rules list | grep $CLUSTER_NAME
              fi
            fi

            if [[ $(echo $VARIABLES_LOCATION | grep aws -c) > 0 ]]; then

              # create aws credentials and config
              mkdir ~/.aws
              cp $OCP_AWS ~/.aws/credentials
              echo "[profile default]
  region = `cat $WORKSPACE/flexy-artifacts/workdir/install-dir/terraform.aws.auto.tfvars.json | jq -r ".aws_region"`
  output = text" >> ~/.aws/config
              cp ~/.aws/config $WORKSPACE/aws_config

              export NETWORK_NAME=$(aws ec2 describe-instances --query 'Reservations[*].Instances[*].[InstanceId,Tags[?Key==`Name`].Value|[0],State.Name,PrivateIpAddress,PublicIpAddress, PrivateDnsName, VpcId]' --output text | column -t  | grep $CLUSTER_NAME  | awk '{print $7}' | grep -v '^$' | sort -u)

              if [[ $PROVISION_OR_TEARDOWN == "PROVISION" ]]; then
                echo "Add Firewall Rules"

                for security_group in $(aws ec2 describe-security-groups --filters "Name=vpc-id,Values=$NETWORK_NAME" --output json | jq -r ".SecurityGroups[].GroupId"); do
                aws ec2 authorize-security-group-ingress --group-id $security_group --protocol tcp --port 22 --cidr 0.0.0.0/0
                aws ec2 authorize-security-group-ingress --group-id $security_group --protocol tcp --port 2022 --cidr 0.0.0.0/0
                aws ec2 authorize-security-group-ingress --group-id $security_group --protocol tcp --port 20000-20109 --cidr 0.0.0.0/0
                aws ec2 authorize-security-group-ingress --group-id $security_group --protocol udp --port 20000-20109 --cidr 0.0.0.0/0
                aws ec2 authorize-security-group-ingress --group-id $security_group --protocol tcp --port 32768-60999 --cidr 0.0.0.0/0
                aws ec2 authorize-security-group-ingress --group-id $security_group --protocol udp --port 32768-60999 --cidr 0.0.0.0/0
                done
              fi

              if [[ $PROVISION_OR_TEARDOWN == "TEARDOWN" ]]; then

                echo "Remove Firewall Rules"

                for security_group in $(aws ec2 describe-security-groups --filters "Name=vpc-id,Values=$NETWORK_NAME" --output json | jq -r ".SecurityGroups[].GroupId"); do
                aws ec2 revoke-security-group-ingress --group-id $security_group --protocol tcp --port 22 --cidr 0.0.0.0/0
                aws ec2 revoke-security-group-ingress --group-id $security_group --protocol tcp --port 2022 --cidr 0.0.0.0/0
                aws ec2 revoke-security-group-ingress --group-id $security_group --protocol tcp --port 20000-20109 --cidr 0.0.0.0/0
                aws ec2 revoke-security-group-ingress --group-id $security_group --protocol udp --port 20000-20109 --cidr 0.0.0.0/0
                aws ec2 revoke-security-group-ingress --group-id $security_group --protocol tcp --port 32768-60999 --cidr 0.0.0.0/0
                aws ec2 revoke-security-group-ingress --group-id $security_group --protocol udp --port 32768-60999 --cidr 0.0.0.0/0
                done
              fi

            fi

            set +x
            rm -rf ~/.kube ~/.aws
          fi
          '''
          }
        }
      }
        
    }
    stage('Configure given Flexy Cluster for LargeScale Tests - Configure Infra node for Prometheus'){
      agent { label params['JENKINS_AGENT_LABEL'] }
      steps{
        copyArtifacts(
            filter: '', 
            fingerprintArtifacts: true, 
            projectName: 'ocp-common/Flexy-install', 
            selector: specific(params.BUILD_NUMBER),
            target: 'flexy-artifacts'
        )
        script {
          buildinfo = readYaml file: "flexy-artifacts/BUILDINFO.yml"
          currentBuild.displayName = "${currentBuild.displayName}-${params.BUILD_NUMBER}"
          currentBuild.description = "Copying Artifact from Flexy-install build <a href=\"${buildinfo.buildUrl}\">Flexy-install#${params.BUILD_NUMBER}</a>"
          buildinfo.params.each { env.setProperty(it.key, it.value) }
        }
        ansiColor('xterm') {
        withCredentials([file(credentialsId: 'b73d6ed3-99ff-4e06-b2d8-64eaaf69d1db', variable: 'OCP_AWS'),
                         file(credentialsId: 'eb22dcaa-555c-4ebe-bb39-5b25628cc6bb', variable: 'OCP_GCP'),
                         file(credentialsId: 'ocp-azure', variable: 'OCP_AZURE')]) {
          sh label: '', script: '''
          if [[ $INFRA_NODES == "true" ]]; then
            # Get ENV VARS Supplied by the user to this job and store in .env_override
            echo "$ENV_VARS" > .env_override
            # Export those env vars so they could be used by CI Job
            set -a && source .env_override && set +a
            mkdir -p ~/.kube
            cp $WORKSPACE/flexy-artifacts/workdir/install-dir/auth/kubeconfig ~/.kube/config

            oc config view
            oc projects
            ls -ls ~/.kube/
            env
            set -x
            if [[ $(oc get machineset -n openshift-machine-api $(oc get machinesets -A  -o custom-columns=:.metadata.name | shuf -n 1) -o=jsonpath='{.metadata.annotations}' | grep -c "machine.openshift.io") -ge 1 ]]; then
              export MACHINESET_METADATA_LABEL_PREFIX=machine.openshift.io
            else
              export MACHINESET_METADATA_LABEL_PREFIX=sigs.k8s.io
            fi
            export CLUSTER_NAME=$(oc get machineset -n openshift-machine-api -o=go-template='{{(index (index .items 0).metadata.labels "machine.openshift.io/cluster-api-cluster" )}}')

            if [[ $(echo $VARIABLES_LOCATION | grep aws -c) > 0 ]]; then
              export AMI_ID=$(oc get machineset -n openshift-machine-api -o=go-template='{{(index .items 0).spec.template.spec.providerSpec.value.ami.id}}')
              export CLUSTER_REGION=$(oc get machineset -n openshift-machine-api -o=go-template='{{(index .items 0).spec.template.spec.providerSpec.value.placement.region}}')
              envsubst < infra-node-machineset-aws.yaml | oc apply -f -
              envsubst < workload-node-machineset-aws.yaml | oc apply -f -
            elif [[ $(echo $VARIABLES_LOCATION | grep azure -c) > 0 ]]; then
              export AMI_ID=$(oc get machineset -n openshift-machine-api -o=go-template='{{(index .items 0).spec.template.spec.providerSpec.value.ami.id}}')
              export AZURE_LOCATION=$(oc get machineset -n openshift-machine-api -o=go-template='{{(index .items 0).spec.template.spec.providerSpec.value.location}}')
              envsubst < infra-node-machineset-azure.yaml | oc apply -f -
              envsubst < workload-node-machineset-azure.yaml | oc apply -f -
            elif [[ $(echo $VARIABLES_LOCATION | grep gcp -c) > 0 ]]; then

              echo $NETWORK_NAME
              # login to service account
              gcloud auth activate-service-account `cat $OCP_GCP | jq -r '.client_email'`  --key-file=$OCP_GCP --project=`cat $OCP_GCP | jq -r '.project_id'`
              gcloud auth list
              gcloud config set account `cat $OCP_GCP | jq -r '.client_email'`
              export NETWORK_NAME=$(gcloud compute networks list  | grep $CLUSTER_NAME | awk '{print $1}')
              if [[ $NETWORK_NAME == "" ]]; then
                sub_cluster_name=$(echo ${CLUSTER_NAME%-*})
                 export NETWORK_NAME=$(gcloud compute networks list | grep $sub_cluster_name | awk '{print $1}')
              fi
              echo $NETWORK_NAME
              export SUBNET_NETWORK_NAME=$(gcloud compute networks subnets list --network=$NETWORK_NAME | grep worker | awk '{print $1}')

              export WORKER_NODE_MACHINESET=$(oc get machinesets --no-headers -n openshift-machine-api | awk {'print $1'} | awk 'NR==1{print $1}')
              export WORKER_MACHINESET_IMAGE=$(oc get machineset ${WORKER_NODE_MACHINESET} -n openshift-machine-api -o jsonpath='{.spec.template.spec.providerSpec.value.disks[0].image}')
              first_worker_node=$(oc get nodes -l 'node-role.kubernetes.io/worker=' --no-headers -o name | head -n 1)


              export GCP_REGION=$(oc get ${first_worker_node} -o=jsonpath='{.metadata.labels}' |  jq '."topology.kubernetes.io/region"' | sed 's/"//g' )

              oc apply -f gcp-sc-pd-ssd.yaml
              envsubst < infra-node-machineset-gcp.yaml | oc apply -f -
              envsubst < workload-node-machineset-gcp.yaml | oc apply -f -
            elif [[ $(echo $VARIABLES_LOCATION | grep vsphere -c) > 0 ]]; then
              export WORKER_NODE_MACHINESET=$(oc get machinesets --no-headers -n openshift-machine-api | awk {'print $1'} | awk 'NR==1{print $1}')
              export WORKER_MACHINESET_IMAGE=$(oc get machineset ${WORKER_NODE_MACHINESET} -n openshift-machine-api -o jsonpath='{.spec.template.spec.providerSpec.value.disks[0].image}')
              export TEMPLATE_NAME=$(oc get machineset -n openshift-machine-api $(oc get machinesets --no-headers -A -o custom-columns=:.metadata.name | head -1) -o=jsonpath='{.spec.template.spec.providerSpec.value.template}')
              export DATACENTER=$(oc get machineset -n openshift-machine-api $(oc get machinesets --no-headers -A -o custom-columns=:.metadata.name | head -1) -o=jsonpath='{.spec.template.spec.providerSpec.value.workspace.datacenter}')
              export DATASTORE=$(oc get machineset -n openshift-machine-api $(oc get machinesets --no-headers -A -o custom-columns=:.metadata.name | head -1) -o=jsonpath='{.spec.template.spec.providerSpec.value.workspace.datastore}')
              export FOLDER=$(oc get machineset -n openshift-machine-api $(oc get machinesets --no-headers -A -o custom-columns=:.metadata.name | head -1) -o=jsonpath='{.spec.template.spec.providerSpec.value.workspace.folder}')
              export RESOURCE_POOL=$(oc get machineset -n openshift-machine-api $(oc get machinesets --no-headers -A -o custom-columns=:.metadata.name | head -1) -o=jsonpath='{.spec.template.spec.providerSpec.value.workspace.resourcePool}')
              export VSPHERE_SERVER=$(oc get machineset -n openshift-machine-api $(oc get machinesets --no-headers -A -o custom-columns=:.metadata.name | head -1) -o=jsonpath='{.spec.template.spec.providerSpec.value.workspace.server}')
              envsubst < infra-node-machineset-vsphere.yaml | oc apply -f -
              envsubst < workload-node-machineset-vsphere.yaml | oc apply -f -
            elif [[ $(echo $VARIABLES_LOCATION | grep alicloud -c) > 0 ]]; then
              export WORKER_NODE_MACHINESET=$(oc get machinesets --no-headers -n openshift-machine-api | awk {'print $1'} | awk 'NR==1{print $1}')
              export WORKER_MACHINESET_IMAGE=$(oc get machineset ${WORKER_NODE_MACHINESET} -n openshift-machine-api -o jsonpath='{.spec.template.spec.providerSpec.value.imageId}')
              export CLUSTER_REGION=$(oc get machineset -n openshift-machine-api -o=go-template='{{(index .items 0).spec.template.spec.providerSpec.value.regionId}}')

              envsubst < infra-node-machineset-alicloud.yaml | oc apply -f -
              envsubst < workload-node-machineset-alicloud.yaml | oc apply -f -

            elif [[ $(echo $VARIABLES_LOCATION | grep ibmcloud -c) > 0 ]]; then
              export WORKER_NODE_MACHINESET=$(oc get machinesets --no-headers -n openshift-machine-api | awk {'print $1'} | awk 'NR==1{print $1}')
              export CLUSTER_REGION=$(oc get machineset -n openshift-machine-api -o=go-template='{{(index .items 0).spec.template.spec.providerSpec.value.region}}')
              envsubst < infra-node-machineset-ibmcloud.yaml | oc apply -f -
              envsubst < workload-node-machineset-ibmcloud.yaml | oc apply -f -

            fi
            retries=0
            attempts=60
            while [[ $(oc get nodes -l 'node-role.kubernetes.io/infra=' --no-headers| wc -l) -lt 3 ]]; do
              oc get nodes
              oc get machines -A
              oc get machinesets -A
              sleep 30
              ((retries += 1))
              if [[ "${retries}" -gt ${attempts} ]]; then
                echo "error: infra nodes didn't become READY in time, failing"
                exit 1
              fi
            done
            retries=0
            while [[ $(oc get nodes -l 'node-role.kubernetes.io/workload=' --no-headers| wc -l) -lt 1 ]]; do
              oc get nodes
              oc get machines -A
              oc get machinesets -A
              sleep 30
              ((retries += 1))
              if [[ "${retries}" -gt ${attempts} ]]; then
                echo "error: workload nodes didn't become READY in time, failing"
                exit 1
              fi
            done
            oc get nodes
            oc label nodes --overwrite -l 'node-role.kubernetes.io/infra=' node-role.kubernetes.io/worker-
            oc label nodes --overwrite -l 'node-role.kubernetes.io/workload=' node-role.kubernetes.io/worker-
            if [[ $(find $WORKSPACE/flexy-artifacts/workdir/install-dir/ | grep vsphere -c) > 0 ]]; then
              envsubst < monitoring-config-vsphere.yaml | oc apply -f -
            else
              envsubst < monitoring-config.yaml | oc apply -f -
            fi
            oc patch -n openshift-ingress-operator ingresscontrollers.operator.openshift.io default -p '{"spec": {"nodePlacement": {"nodeSelector": {"matchLabels": {"node-role.kubernetes.io/infra": ""}}}}}' --type merge
            git clone --single-branch --depth 1 https://github.com/cloud-bulldozer/performance-dashboards.git
            pushd performance-dashboards/dittybopper
            ./deploy.sh
            popd
            set +x
            rm -rf ~/.kube ~/.aws
          fi
          '''
          }
        }
      }
        
    }
  }
}

