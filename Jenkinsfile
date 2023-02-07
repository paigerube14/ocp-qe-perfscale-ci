@Library('flexy') _

// rename build
def private_ip_address = ""
def userId = currentBuild.rawBuild.getCause(hudson.model.Cause$UserIdCause)?.userId
if (userId) {
  currentBuild.displayName = userId
}

pipeline {
  agent none

  parameters {
        string(name: 'BUILD_NUMBER', defaultValue: '', description: 'Build number of job that has installed the cluster.')
        string(name: 'JENKINS_AGENT_LABEL',defaultValue:'oc410 || oc411 || oc412')
        string(name: 'EGRESS_REPO', defaultValue:'https://github.com/SachinNinganure/Egress-Load-test', description:'You can change this to point to your fork if needed.')
        string(name: 'EGRESS_REPO_BRANCH', defaultValue:'master', description:'You can change this to point to a branch on your fork if needed.')
        text(name: 'ENV_VARS', defaultValue: '', description:'''<p>
               Enter list of additional (optional) Env Vars you'd want to pass to the script, one pair on each line. <br>
               e.g.<br>
               SOMEVAR1='env-test'<br>
               SOMEVAR2='env2-test'<br>
               ...<br>
               SOMEVARn='envn-test'<br>
               </p>'''
        )
        booleanParam(name: 'DEBUG', defaultValue: false)
    }

  stages {
    stage('Sequential'){
      agent { label params['JENKINS_AGENT_LABEL'] }
      stages{
        stage('Copy artifacts'){
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
              currentBuild.displayName = "${currentBuild.displayName}-${params.BUILD_NUMBER}-${currentBuild.number}"
              currentBuild.description = "Copying Artifact from Flexy-install build <a href=\"${buildinfo.buildUrl}\">Flexy-install#${params.BUILD_NUMBER}</a>"
              buildinfo.params.each { env.setProperty(it.key, it.value) }
            }
            script {   
              if (fileExists("flexy-artifacts/workdir/install-dir/cluster_info.json")){ 
                private_ip_address = "cat flexy-artifacts/workdir/install-dir/cluster_info.json"
                println private_ip_address
                ENV_VARS += '\n' + private_ip_address
                sh label: '', script: '''
                echo "$ENV_VARS" > .env_override
                set -a && source .env_override && set +a
                private_ip_address=`grep INT_SVC_INSTANCE_INTERNAL_IP flexy-artifacts/workdir/install-dir/cluster_info.json|cut -d "," -f3-|cut -d ":" -f2-|sed 's/}//g'|cut -d "." -f1 |sed 's/-/./g'|cut -d "." -f2-`
                echo "I am at the last of the logic, $private_ip_address"
                echo $private_ip_address >flexy-artifacts/workdir/install-dir/ipfile.txt
                '''
                private_ip_address = sh returnStdout: true, script: 'cat flexy-artifacts/workdir/install-dir/ipfile.txt'
                println private_ip_address
                println "now copying ip to ENV variable"
                ENV_VARS += '\n' + "PRIVATE_IP_ADDRESS=" + private_ip_address
                println "printing the ENV variable $ENV_VARS"
                }
              }
          }
        }
        stage('Checkout repo'){
          steps{
            dir('Egress-Load-test'){
              git branch: params.EGRESS_REPO_BRANCH, url: params.EGRESS_REPO
            }
          }
        }
        stage('Debug info'){
          when {
            environment name: 'DEBUG', value: 'true'
          }
          steps{
            ansiColor('xterm') {
              sh label: '', script: '''
              # Get ENV VARS Supplied by the user to this job and store in .env_override
              echo "$ENV_VARS" > .env_override
              # Export those env vars so they could be used by CI Job
              set -a && source .env_override && set +a
              mkdir -p ~/.kube
              cp $WORKSPACE/flexy-artifacts/workdir/install-dir/auth/kubeconfig ~/.kube/config
              ls -ls ~/.kube/
              env
              oc version
              oc project default
              ansible --version
              python --version
              python3 --version
              whoami
              '''
            }
          }
        }

	      stage('Run egress script to test the egress functionality'){
          steps{
            ansiColor('xterm') {
              sh label: '', script: '''
              # Get ENV VARS Supplied by the user to this job and store in .env_override
              echo "$ENV_VARS" > .env_override
              # Export those env vars so they could be used by CI Job
              set -a && source .env_override && set +a
              mkdir -p ~/.kube
              cp $WORKSPACE/flexy-artifacts/workdir/install-dir/auth/kubeconfig ~/.kube/config
              ls -la
              cd Egress-Load-test 
	            pwd

              '''
            }
          }
        }
        stage('Archive Artifacts') {
          steps {
                  sh 'pwd'
		              archiveArtifacts artifacts: 'Egress-Load-test/*', fingerprint: true
                }
            }

        }
      }
    }
  }