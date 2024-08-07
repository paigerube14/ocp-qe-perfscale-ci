@Library('flexy') _

// rename build
def userCause = currentBuild.rawBuild.getCause(Cause.UserIdCause)
def upstreamCause = currentBuild.rawBuild.getCause(Cause.UpstreamCause)

userId = "ocp-perfscale-qe"
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

pipeline {
  agent none

  parameters {
        string(
          name: "UUID", 
          defaultValue: "", 
          description: 'UUID of current run to do comparison on'
        )
        string(
          name: "BASELINE_UUID", 
          defaultValue: "", 
          description: 'Set a baseline uuid to use for comparison, if blank will find baseline uuid for profile, workload and worker node count to then compare'
        )
        booleanParam(
          name: "PREVIOUS_VERSION", 
          defaultValue: false,
          description: "If you want to compare the current UUID's data to any <ocp-version>-1  release data"
        )
        booleanParam(
          name: "HUNTER_ANALYZE", 
          defaultValue: false,
          description: "If you want to compare the current UUID's data to any <ocp-version>-1  release data"
        )
        string(
          name: "CONFIG", 
          defaultValue: "examples/small-scale-cluster-density.yaml", 
          description: 'Set of time to look back at to find any comparable results'
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
        string(
          name: 'ORION_REPO', 
          defaultValue:'https://github.com/cloud-bulldozer/orion.git', 
          description:'You can change this to point to your fork if needed.'
        )
        string(
          name: 'ORION_REPO_BRANCH', 
          defaultValue:'main', 
          description:'You can change this to point to a branch on your fork if needed.'
        )
    }

  stages {

    stage('Run Orion Comparison'){
      when {
            expression { params.UUID != "" }
        }
      agent { label params['JENKINS_AGENT_LABEL'] }
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
            branches: [[name: params.ORION_REPO_BRANCH ]],
            doGenerateSubmoduleConfigurations: false,
            extensions: [
                [$class: 'CloneOption', noTags: true, reference: '', shallow: true],
                [$class: 'PruneStaleBranch'],
                [$class: 'CleanCheckout'],
                [$class: 'IgnoreNotifyCommit'],
                [$class: 'RelativeTargetDirectory', relativeTargetDir: 'orion']
            ],
            userRemoteConfigs: [[url: params.ORION_REPO ]]
        ])
        
        script{
            env.EMAIL_ID_FOR_RESULTS_SHEET = "${userId}@redhat.com"
            withCredentials([usernamePassword(credentialsId: 'elasticsearch-perfscale-ocp-qe', usernameVariable: 'ES_USERNAME', passwordVariable: 'ES_PASSWORD'),
            file(credentialsId: 'sa-google-sheet', variable: 'GSHEET_KEY_LOCATION')]) {
                RETURNSTATUS = sh(returnStatus: true, script: '''
                    # Get ENV VARS Supplied by the user to this job and store in .env_override
                    echo "$ENV_VARS" > .env_override
                    # Export those env vars so they could be used by CI Job
                    set -a && source .env_override && set +a

                    export ES_SERVER="https://$ES_USERNAME:$ES_PASSWORD@search-ocp-qe-perf-scale-test-elk-hcm7wtsqpxy7xogbu72bor4uve.us-east-1.es.amazonaws.com"

                    python3.9 --version
                    python3.9 -m pip install virtualenv
                    python3.9 -m virtualenv venv3
                    source venv3/bin/activate
                    python --version

                    cd orion
                    pip install -r requirements.txt
                    pip install .
                    hunter_var=""
                    if [[ $HUNTER_ANALYZE == "true" ]]; then
                      hunter_var=" --hunter-analyze"
                    fi
                    uuid_var=""
                    if [[ -n $UUID ]]; then
                      uuid_var=" --uuid $UUID "
                    fi
                    
                    export es_metadata_index="perf_scale_ci*"
                    export es_benchmark_index="ripsaw-kube-burner*"
                    orion cmd --config $CONFIG --debug$uuid_var$hunter_var

                  ''')
                if (RETURNSTATUS.toInteger() != 0) {
                    currentBuild.result = "FAILURE"
                }
                archiveArtifacts(
                        artifacts: 'orion/output.csv',
                        allowEmptyArchive: true,
                        fingerprint: true
                )
          }
        }
      }

    }
 }
}
