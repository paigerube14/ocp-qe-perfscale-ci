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

pipeline {
    agent { label params.JENKINS_AGENT_LABEL }

    options {
        timeout(time: 1, unit: 'HOURS')
        ansiColor('xterm')
    }

    parameters {
        string(
            name: 'FLEXY_BUILD_NUMBER',
            defaultValue: '',
            description: '''
                Build number of Flexy job that installed the cluster.<br/>
                <b>Note that only AWS clusters are supported at the moment.</b>
            '''
        )
        separator(
            name: 'WORKLOAD_CONFIG_OPTIONS',
            sectionHeader: 'Workload Configuration Options',
            sectionHeaderStyle: '''
                font-size: 14px;
                font-weight: bold;
                font-family: 'Orienta', sans-serif;
            '''
        )
        string(
          name: 'JENKINS_JOB',
          defaultValue: '', 
          description: 'Scale-ci job url'
        )
        text(
          name: 'JOB_OUTPUT', 
          defaultValue: '', 
          description:'This is the output that was run from the scale-ci job. This will be used to help get comparison sheets'
        )
        string(
            name: 'JENKINS_AGENT_LABEL',
            defaultValue: 'oc412',
            description:
            '''
            scale-ci-static: for static agent that is specific to scale-ci, useful when the jenkins dynamic agent isn't stable<br>
            4.y: oc4y || mac-installer || rhel8-installer-4y <br/>
                e.g, for 4.8, use oc48 || mac-installer || rhel8-installer-48 <br/>
            3.11: ansible-2.6 <br/>
            3.9~3.10: ansible-2.4 <br/>
            3.4~3.7: ansible-2.4-extra || ansible-2.3 <br/>
            '''
        )
        text(
            name: 'ENV_VARS', 
            defaultValue: '', 
            description:'''<p>
              Enter list of additional (optional) Env Vars you'd want to pass to the script, one pair on each line. <br>
              See https://github.com/cloud-bulldozer/kraken-hub/blob/main/docs/cerberus.md for list of variables to pass <br>
              e.g.<br>
              SOMEVAR1='env-test'<br>
              SOMEVAR2='env2-test'<br>
              ...<br>
              SOMEVARn='envn-test'<br>
              </p>
            '''
        )
    }

    stages {
        stage('Validate job parameters') {
            steps {
                script {
                    if (params.FLEXY_BUILD_NUMBER == '') {
                        error 'A Flexy build number must be specified'
                    }
                }
            }
        }
        stage('Run Workload and Mr. Sandman') {
            steps {
                checkout([
                    $class: 'GitSCM',
                    branches: [[name: 'netobserv-perf-tests' ]],
                    userRemoteConfigs: [[url: GIT_URL ]],
                    extensions: [[$class: 'RelativeTargetDirectory', relativeTargetDir: 'ocp-qe-perfscale-ci-netobs']]
                ])
                script {
                    // run Mr. Sandman
                    returnCode = sh(returnStatus: true, script: """
                        python3.9 --version
                        python3.9 -m pip install virtualenv
                        python3.9 -m virtualenv venv3
                        source venv3/bin/activate
                        python --version
                        python -m pip install -r $WORKSPACE/ocp-qe-perfscale-ci-netobs/scripts/requirements.txt
                        python $WORKSPACE/ocp-qe-perfscale-ci-netobs/scripts/sandman.py --file $WORKSPACE/workload-artifacts/workloads/**/*.out
                    """)
                    // fail pipeline if Mr. Sandman run failed, continue otherwise
                    if (returnCode.toInteger() != 0) {
                        error('Mr. Sandman tool failed :(')
                    }
                    else {
                        println 'Successfully ran Mr. Sandman tool :)'
                    }
                    // update build description fields
                    // UUID
                    env.UUID = sh(returnStdout: true, script: "jq -r '.uuid' $WORKSPACE/ocp-qe-perfscale-ci-netobs/data/workload.json").trim()
                    currentBuild.description += "<b>UUID:</b> ${env.UUID}<br/>"
                    // STARTTIME_TIMESTAMP is unix timestamp of start time
                    env.STARTTIME_TIMESTAMP = sh(returnStdout: true, script: "jq -r '.starttime_timestamp' $WORKSPACE/ocp-qe-perfscale-ci-netobs/data/workload.json").trim()
                    currentBuild.description += "<b>STARTTIME_TIMESTAMP:</b> ${env.STARTTIME_TIMESTAMP}<br/>"
                    // ENDTIME_TIMESTAMP is unix timestamp of end time
                    env.ENDTIME_TIMESTAMP = sh(returnStdout: true, script: "jq -r '.endtime_timestamp' $WORKSPACE/ocp-qe-perfscale-ci-netobs/data/workload.json").trim()
                    currentBuild.description += "<b>ENDTIME_TIMESTAMP:</b> ${env.ENDTIME_TIMESTAMP}<br/>"
                }
            }
        }
        stage('Run Post to Elastic tool') {
            copyArtifacts(
                    fingerprintArtifacts: true, 
                    projectName: env.JENKINS_JOB,
                    selector: specific(env.BUILD_NUMBER),
                    target: 'workload-artifacts'
            )
            checkout([
              $class: 'GitSCM',
              branches: [[name: GIT_BRANCH ]],
              doGenerateSubmoduleConfigurations: false,
              userRemoteConfigs: [[url: GIT_URL ]]
            ])
            steps {
                withCredentials([usernamePassword(credentialsId: 'elasticsearch-perfscale-ocp-qe', usernameVariable: 'ES_USERNAME', passwordVariable: 'ES_PASSWORD')]) {
                    script {
                        NOPE_ARGS = '--starttime $STARTTIME_TIMESTAMP --endtime $ENDTIME_TIMESTAMP --jenkins-job $JENKINS_JOB --jenkins-build $BUILD_NUMBER --uuid $UUID'
                        returnCode = sh(returnStatus: true, script: """
                            python3.9 --version
                            python3.9 -m pip install virtualenv
                            python3.9 -m virtualenv venv3
                            source venv3/bin/activate
                            python --version
                            pip install -r requirements.txt
                            env
                            python post_to_es.py $NOPE_ARGS
                        """)
                        // fail pipeline if NOPE run failed, continue otherwise
                        if (returnCode.toInteger() == 2) {
                            unstable('NOPE tool ran, but Elasticsearch upload failed - check build artifacts for data and try uploading it locally :/')
                        }
                        else if (returnCode.toInteger() != 0) {
                            error('NOPE tool failed :(')
                        }
                        else {
                            println 'Successfully ran NOPE tool :)'
                        }
                    }
                }
            }
        }
    }
}
