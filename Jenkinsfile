@Library('flexy') _

// rename build
def userId = currentBuild.rawBuild.getCause(hudson.model.Cause$UserIdCause)?.userId
if (userId) {
  currentBuild.displayName = userId
}

def RETURNSTATUS = "default"
def output = ""
pipeline {
  agent none
  parameters {
        string(name: 'BUILD_NUMBER', defaultValue: '', description: 'Build number of job that has installed the cluster.')
        string(name: 'DAST_TOOL_URL', defaultValue: 'https://github.com/RedHatProductSecurity/rapidast.git', description: 'Rapidast tool github url .')
        string(name: 'DAST_TOOL_BRANCH', defaultValue: 'development', description: 'Rapdiast tool github barnch to checkout.')
        string(name:'JENKINS_AGENT_LABEL',defaultValue:'oc45',description:
        '''
        scale-ci-static: for static agent that is specific to scale-ci, useful when the jenkins dynamic agent isn't stable<br>
        4.y: oc4y || mac-installer || rhel8-installer-4y <br/>
            e.g, for 4.8, use oc48 || mac-installer || rhel8-installer-48 <br/>
        3.11: ansible-2.6 <br/>
        3.9~3.10: ansible-2.4 <br/>
        3.4~3.7: ansible-2.4-extra || ansible-2.3 <br/>
        '''
        )
       text(name: 'ENV_VARS', defaultValue: '', description:'''<p>
               Enter list of additional (optional) Env Vars you'd want to pass to the script, one pair on each line. <br>
               See https://github.com/cloud-bulldozer/kraken-hub/blob/main/docs/cerberus.md for list of variables to pass <br>
               e.g.<br>
               SOMEVAR1='env-test'<br>
               SOMEVAR2='env2-test'<br>
               ...<br>
               SOMEVARn='envn-test'<br>
               </p>'''
            )
     }

  stages {
    stage('Kraken Run'){
      agent { label params['JENKINS_AGENT_LABEL'] }
      steps{
        deleteDir()
        checkout([
            $class: 'GitSCM',
            branches: [[name: params.DAST_TOOL_BRANCH ]],
            doGenerateSubmoduleConfigurations: false,
            userRemoteConfigs: [[url: params.DAST_TOOL_URL ]]
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
        script {
          RETURNSTATUS = sh(returnStatus: true, script: '''
          
          ls
          python3.9 --version
          python3.9 -m pip install virtualenv
          python3.9 -m virtualenv venv3
          source venv3/bin/activate
          python --version
          pip --version
          pip install  docker-compose
          docker-compose --help
          ./runenv.sh
          ./test/scan-example-with-podman.sh
          ''')
          sh "echo $RETURNSTATUS"
        }
      script{
            def status = "FAIL"
            sh "echo $RETURNSTATUS"
            if( RETURNSTATUS.toString() == "0") {
                status = "PASS"
            }else {
                currentBuild.result = "FAILURE"
           }
      }
     }
   }
  }
}