@Library('flexy') _

// rename build
def userCause = currentBuild.rawBuild.getCause(Cause.UserIdCause)
def upstreamCause = currentBuild.rawBuild.getCause(Cause.UpstreamCause)

userId = "prubenda"
if (userCause) {
    userId = userCause.getUserId()
}
else if (upstreamCause) {
    def upstreamJob = Jenkins.getInstance().getItemByFullName(upstreamCause.getUpstreamProject(), hudson.model.Job.class)
    if (upstreamJob) {
        def upstreamBuild = upstreamJob.getBuildByNumber(upstreamCause.getUpstreamBuild())
        if (upstreamBuild) {
            def realUpstreamCause = upstreamBuild.getCause(Cause.UserIdCause)
            if (realUpstreamCause) {
                userId = realUpstreamCause.getUserId()
            }
        }
    }
}
if (userId) {
    currentBuild.displayName = userId
}

println "user $userId"

def RETURNSTATUS = "default"

pipeline {
  agent none

  parameters {
        string(name: 'BUILD_NUMBER', defaultValue: '', description: 'Build number of job that has installed the cluster.')
        choice(choices: ["cluster-density","node-density","node-density-heavy","pod-density","pod-density-heavy","max-namespaces","max-services", "concurrent-builds","network-perf","router-perf","etcd-perf"], name: 'WORKLOAD', description: '''Type of kube-burner job to run''')
        string(name: "UUID", defaultValue: "", description: 'Json files of what data to output into a google sheet')
        string(
          name: "COMPARISON_CONFIG",
          defaultValue: "podLatency.json",
          description: 'JSON config files of what data to output into a Google Sheet'
        )
        string(
          name: "TOLERANCY_RULES",
          defaultValue: "pod-latency-tolerancy-rules.yaml",
          description: 'JSON config files of what data to output into a Google Sheet'
        )
        text(name: 'ENV_VARS', defaultValue: '', description:'''<p>
               Enter list of additional (optional) Env Vars you'd want to pass to the script, one pair on each line. <br>
               e.g.<br>
               SOMEVAR1='env-test'<br>
               SOMEVAR2='env2-test'<br>
               ...<br>
               SOMEVARn='envn-test'<br>
               </p>'''
            )
        string(name:'JENKINS_AGENT_LABEL',defaultValue:'oc411',description:
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
        string(name: 'E2E_BENCHMARKING_REPO', defaultValue:'https://github.com/cloud-bulldozer/e2e-benchmarking', description:'You can change this to point to your fork if needed.')
        string(name: 'E2E_BENCHMARKING_REPO_BRANCH', defaultValue:'master', description:'You can change this to point to a branch on your fork if needed.')
    }

  stages {

    stage('Run Benchmark Comparison'){
      agent { label params['JENKINS_AGENT_LABEL'] }
      environment{
          EMAIL_ID_FOR_RESULTS_SHEET = "${userId}@redhat.com"
      }
      steps{
        deleteDir()
        checkout([
          $class: 'GitSCM',
          branches: [[name: GIT_BRANCH ]],
          doGenerateSubmoduleConfigurations: false,
          userRemoteConfigs: [[url: GIT_URL ]
          ]])
        checkout([
            $class: 'GitSCM',
            branches: [[name: params.E2E_BENCHMARKING_REPO_BRANCH ]],
            doGenerateSubmoduleConfigurations: false,
            extensions: [
                [$class: 'CloneOption', noTags: true, reference: '', shallow: true],
                [$class: 'PruneStaleBranch'],
                [$class: 'CleanCheckout'],
                [$class: 'IgnoreNotifyCommit'],
                [$class: 'RelativeTargetDirectory', relativeTargetDir: 'e2e-benchmark']
            ],
            userRemoteConfigs: [[url: params.E2E_BENCHMARKING_REPO ]]
        ])
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

        script{
            withCredentials([usernamePassword(credentialsId: 'elasticsearch-perfscale-ocp-qe', usernameVariable: 'ES_USERNAME', passwordVariable: 'ES_PASSWORD'),
                    file(credentialsId: 'sa-google-sheet', variable: 'GSHEET_KEY_LOCATION')]) {
                
                RETURNSTATUS = sh(returnStatus: true, script: '''
                    # Get ENV VARS Supplied by the user to this job and store in .env_override
                    echo "$ENV_VARS" > .env_override
                    # Export those env vars so they could be used by CI Job
                    set -a && source .env_override && set +a
                    cp $GSHEET_KEY_LOCATION $WORKSPACE/.gsheet.json
                    export GSHEET_KEY_LOCATION=$WORKSPACE/.gsheet.json
                    export EMAIL_ID_FOR_RESULTS_SHEET=$EMAIL_ID_FOR_RESULTS_SHEET

                    export ES_SERVER="https://$ES_USERNAME:$ES_PASSWORD@search-ocp-qe-perf-scale-test-elk-hcm7wtsqpxy7xogbu72bor4uve.us-east-1.es.amazonaws.com"
                    export ES_SERVER_BASELINE="https://$ES_USERNAME:$ES_PASSWORD@search-ocp-qe-perf-scale-test-elk-hcm7wtsqpxy7xogbu72bor4uve.us-east-1.es.amazonaws.com"
  
                    mkdir -p ~/.kube
                    cp $WORKSPACE/flexy-artifacts/workdir/install-dir/auth/kubeconfig ~/.kube/config


                    python3.9 --version
                    python3.9 -m pip install virtualenv
                    python3.9 -m virtualenv venv3

                    source venv3/bin/activate
                    python --version
                    pip install -r requirements.txt

                    export BASELINE_UUID=$(python find_baseline_uuid.py --workload $WORKLOAD)
                    env | grep BASELINE_UUID

                    if [[ $WORKLOAD == "network-perf" ]]; then 
                      export TOLERANCY_RULES=$WORKSPACE/e2e-benchmark/workloads/network-perf/$TOLERANCY_RULES
                      echo "not set up for this type of comparison"
                      exit 1 
                    elif [[ $WORKLOAD == "router-perf" ]]; then 
                      export TOLERANCY_RULES=$WORKSPACE/e2e-benchmark/workloads/router-perf-v2/$TOLERANCY_RULES
                    elif [[ $WORKLOAD == "etcd-perf" ]]; then 
                      export TOLERANCY_RULES=$WORKSPACE/e2e-benchmark/workloads/etcd-perf/$TOLERANCY_RULES
                      echo "not set up for this type of omparison"
                      exit 1
                    else
                      export TOLERANCY_RULES=$WORKSPACE/e2e-benchmark/workloads/kube-burner/$TOLERANCY_RULES
                    fi
                    
                    if [[ -n $BASELINE_UUID ]]; then 
                      cd e2e-benchmark/utils

                      source compare.sh
                      run_benchmark_comparison |& tee "comparison.out"
                      ! grep "Benchmark comparison failed" comparison.out
                    else 
                      echo "need to add $UUID to ElasticSearch to track new configuration"
                      exit 1
                    fi

                ''')
                archiveArtifacts(
                    artifacts: 'comparison.out',
                    allowEmptyArchive: true,
                    fingerprint: true
                )

                if (RETURNSTATUS.toInteger() != 0) {
                    currentBuild.result = "FAILURE"
                }
          }
        }
      }

    }
 }
}
