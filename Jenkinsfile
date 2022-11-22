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
        string(name: 'KUBEADMIN_PASS', defaultValue: '', description: 'Password to login to password.')
        string(name: 'DAST_TOOL_URL', defaultValue: 'https://github.com/RedHatProductSecurity/rapidast.git', description: 'Rapidast tool github url .')
        string(name: 'DAST_TOOL_BRANCH', defaultValue: 'development', description: 'Rapdiast tool github barnch to checkout.')
        string(name: 'GIT_LAB_URL', defaultValue: 'https://gitlab.cee.redhat.com/jechoi/rapidast-ocp.git', description: 'Rapidast tool github url .')
        string(name: 'GIT_LAB_BRANCH', defaultValue: 'main', description: 'Rapdiast tool github barnch to checkout.')
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
          branches: [[name: GIT_BRANCH ]],
          doGenerateSubmoduleConfigurations: false,
          userRemoteConfigs: [[url: GIT_URL ]
          ]])
        checkout([
            $class: 'GitSCM',
            branches: [[name: params.DAST_TOOL_BRANCH ]],
            doGenerateSubmoduleConfigurations: false,
            extensions: [
                [$class: 'CloneOption', noTags: true, reference: '', shallow: true],
                [$class: 'PruneStaleBranch'],
                [$class: 'CleanCheckout'],
                [$class: 'IgnoreNotifyCommit'],
                [$class: 'RelativeTargetDirectory', relativeTargetDir: 'dast_tool']
            ],
            userRemoteConfigs: [[url: params.DAST_TOOL_URL ]]
        ])
        checkout changelog: false,
          poll: false,
          scm: [
              $class: 'GitSCM',
              branches: [[name: "${params.GIT_LAB_BRANCH}"]],
              doGenerateSubmoduleConfigurations: false,
              extensions: [
                  [$class: 'CloneOption', noTags: true, reference: '', shallow: true],
                  [$class: 'PruneStaleBranch'],
                  [$class: 'CleanCheckout'],
                  [$class: 'IgnoreNotifyCommit'],
                  [$class: 'RelativeTargetDirectory', relativeTargetDir: 'dast_git_lab']
              ],
              submoduleCfg: [],
              userRemoteConfigs: [[
                  name: 'origin',
                  refspec: "+refs/heads/${params.GIT_LAB_BRANCH}:refs/remotes/origin/${params.GIT_LAB_BRANCH}",
                  url: "${params.GIT_LAB_URL}"
              ]]
          ]
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
           # Get ENV VARS Supplied by the user to this job and store in .env_override
          echo "$ENV_VARS" > .env_override
          # Export those env vars so they could be used by CI Job
          set -a && source .env_override && set +a
          mkdir -p ~/.kube
          cp $WORKSPACE/flexy-artifacts/workdir/install-dir/auth/kubeconfig ~/.kube/config
          ls

          if [[ ! -z $(kubectl get ns rapidast) ]]; then 
              kubectl delete ns rapidast
          fi
          kubectl create ns rapidast

          mkdir /dast_tool/config/openapi


          cp dast_git_lab/ocp-openapi-v2-1.23.5%2B3afdacb.json /dast_tool/config/openapi/

          ls /dast_tool/config/openapi
          cp dast_git_lab/config.yaml /dast_tool/config/config.yaml
          cp dast_git_lab/add-ocp-token-cookie.js dast_tool/scripts

          kubectl apply -f operator_configs/catalog_source.yaml
          kubectl apply -f operator_configs/subscription.yaml
          kubectl apply -f operator_configs/operatorgroup.yaml


          kubectl apply -f dast_tool/operator/config/samples/research_v1alpha1_rapidast.yaml

          mkdir results
          bash results.sh rapidast-pvc results
          ls

          ''')
          sh "echo $RETURNSTATUS"
          archiveArtifacts(
              artifacts: 'results/*',
              allowEmptyArchive: true,
              fingerprint: true
          )
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