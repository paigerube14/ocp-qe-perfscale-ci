
def aws = null
def install = null
def loaded_ci = null
def upgrade_ci = null
def destroy_ci = null
def build_string = "DEFAULT"
def load_result = "SUCCESS"
def loaded_url = ""
def upgrade_url = ""
def proxy_settings = ""

def userId = currentBuild.rawBuild.getCause(hudson.model.Cause$UserIdCause)?.userId
if (userId) {
  currentBuild.displayName = "${userId}-${currentBuild.displayName}"
}

pipeline{
    agent any

    parameters {
        string(name: 'BUILD_NUMBER', defaultValue: '', description: 'Build number of job that has installed the cluster.')
        string(name: 'OCP_PREFIX', defaultValue: '', description: 'Name of ocp cluster you want to build')
        string(name: 'OCP_VERSION', defaultValue: '', description: 'Build version to install the cluster.')
        choice(choices: ['','aws', 'azure', 'gcp', 'osp', 'alicloud', 'ibmcloud', 'vsphere'], name: 'CLOUD_TYPE', description: '''Cloud type (As seen on https://gitlab.cee.redhat.com/aosqe/flexy-templates/-/tree/master/functionality-testing/aos-4_9, after ""-on-") <br/>
        Will be ignored if BUILD_NUMBER is set''')
        choice(choices: ['','ovn', 'sdn'], name: 'NETWORK_TYPE', description: 'Network type, will be ignored if BUILD_NUMBER is set')
        choice(choices: ['','ipi', 'upi', 'sno'], name: 'INSTALL_TYPE', description: '''Type of installation (set to SNO for sno cluster type),  <br/>
        will be ignored if BUILD_NUMBER is set''')
        string(name: 'MASTER_COUNT', defaultValue: '3', description: 'Number of master nodes in your cluster to create.')
        string(name: "WORKER_COUNT", defaultValue: '3', description: 'Number of worker nodes in your cluster to create.')

        choice(choices: ["","cluster-density","pod-density","node-density","etcd-perf","max-namespaces","max-services","pod-network-policy-test","router-perf","storage-perf"], name: 'CI_TYPE', description: '''Type of scale-ci job to run. Can be left blank to not run ci job''')
        booleanParam(name: 'DESTROY_WHEN_DONE', defaultValue: 'False', description: 'If you want to destroy the cluster created at the end of your run ')
        string(name: 'SCALE_UP', defaultValue: '0', description: 'If value is set to anything greater than 0, cluster will be scaled up before executing the workload.')
        string(name: 'SCALE_DOWN', defaultValue: '0', description:
        '''If value is set to anything greater than 0, cluster will be scaled down after the execution of the workload is complete,<br>
        if the build fails, scale down may not happen, user should review and decide if cluster is ready for scale down or re-run the job on same cluster.'''
        )
        string(name:'JENKINS_AGENT_LABEL',defaultValue:'oc45',description:
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
        string(name: 'JOB_ITERATIONS', defaultValue: '1000', description: 'This variable configures the number of cluster-density jobs iterations to perform (1 namespace per iteration). By default 1000.')
        string(name: 'NODE_COUNT', defaultValue: '3', description: 'Number of nodes to be used in your cluster for this workload.')
        string(name: "PODS_PER_NODE", defaultValue: '150', description: 'Number of pods per node.')
        booleanParam(name: 'WRITE_TO_FILE', defaultValue: true, description: 'Value to write to google sheet (will run https://mastern-jenkins-csb-openshift-qe.apps.ocp4.prod.psi.redhat.com/job/scale-ci/job/paige-e2e-multibranch/job/write-to_sheet)')
        string(name: 'UPGRADE_VERSION', description: 'This variable sets the version number you want to upgrade your OpenShift cluster to (can list multiple by separating with comma, no spaces).')
        booleanParam(name: 'ENABLE_FORCE', defaultValue: true, description: 'This variable will force the upgrade or not')
        booleanParam(name: 'SCALE', defaultValue: false, description: 'This variable will scale the cluster up one node at the end up the upgrade')
        string(name: 'MAX_UNAVAILABLE', defaultValue: "1", description: 'This variable will set the max number of unavailable nodes during the upgrade')
        text(name: 'ENV_VARS', defaultValue: '', description:'''<p>
               Enter list of additional (optional) Env Vars you'd want to pass to the script, one pair on each line. <br>
               e.g.<br>
               SOMEVAR1='env-test'<br>
               SOMEVAR2='env2-test'<br>
               ...<br>
               SOMEVARn='envn-test'<br>
               </p>'''
            )
        string(name: 'E2E_BENCHMARKING_REPO', defaultValue:'https://github.com/cloud-bulldozer/e2e-benchmarking', description:'You can change this to point to your fork if needed.')
        string(name: 'E2E_BENCHMARKING_REPO_BRANCH', defaultValue:'master', description:'You can change this to point to a branch on your fork if needed.')
    }


    stages{
        stage("Build Flexy Clusters") {
           agent { label params['JENKINS_AGENT_LABEL'] }
           steps {
                script{
                    def install_type_custom = params.INSTALL_TYPE
                     if(params.BUILD_NUMBER == "") {
                         def network_ending = ""
                          if (params.CLOUD_TYPE == "vsphere") {
                                network_ending = "-vmc7"
                          }
                           if (params.NETWORK_TYPE != "sdn") {
                            if (params.CLOUD_TYPE == "alicloud") {
                                network_ending = "-fips-${params.NETWORK_TYPE}-ci"
                            }else {
                                network_ending += "-${params.NETWORK_TYPE}"
                            }
                           }
                            def worker_type = ""
                            if (params.CLOUD_TYPE == "aws") {
                                if (params.INSTALL_TYPE == "sno") {
                                    worker_type = "master_worker_AllInOne: 'true', num_masters: 1, num_workers: 0, vm_type: 'm5.4xlarge', "
                                    install_type_custom = "ipi"
                                } else {
                                worker_type = "vm_type_workers: 'm5.xlarge', num_workers: " + WORKER_COUNT + ", num_masters: " + MASTER_COUNT + ","
                                }
                            }
                            else if (params.CLOUD_TYPE == "azure") {
                                worker_type = "vm_type_workers: 'Standard_D8s_v3', region: centralus, num_workers: " + WORKER_COUNT + ", num_masters: " + MASTER_COUNT + ","
                            }
                            else if (params.CLOUD_TYPE == "gcp") {
                                worker_type = "vm_type_workers: 'n1-standard-4', num_workers: " + WORKER_COUNT + ", num_masters: " + MASTER_COUNT + ","
                                if (params.NETWORK_TYPE != "sdn") {
                                 network_ending = network_ending + "-ci"
                                }
                            }
                            else if (params.CLOUD_TYPE == "osp") {
                                worker_type = "vm_type_workers: 'ci.m1.xlarge', num_workers: " + WORKER_COUNT + ", num_masters: " + MASTER_COUNT + ","
                            }
                            else if (params.CLOUD_TYPE == "alicloud") {

                                worker_type = "vm_type_workers: 'ecs.g6.xlarge', num_workers: " + WORKER_COUNT + ", num_masters: " + MASTER_COUNT + ","
                            }
                            else if (params.CLOUD_TYPE == "ibmcloud") {
                                worker_type = "vm_type_workers: 'bx2d-4x16', region: 'jp-tok', num_workers: " + WORKER_COUNT + ", num_masters: " + MASTER_COUNT + ","
                            }
                            else if (params.CLOUD_TYPE == "vsphere") {
                                worker_type = " num_workers: " + WORKER_COUNT + ", num_masters: " + MASTER_COUNT + ","
                            }
                            def version = params.OCP_VERSION
                            sh "echo ${version}"
                            def version_list = version.tokenize(".")
                            sh "echo version ${version_list}"
                            def major_v = version_list[0]
                            def minor_v = version_list[1]
                            sh "echo minor ${minor_v} major ${major_v}"
                            def var_loc = "private-templates/functionality-testing/aos-${major_v}_${minor_v}/${install_type_custom}-on-${params.CLOUD_TYPE}/versioned-installer${network_ending}"
                            sh "echo var ${var_loc}"
                            install = build job:"ocp-common/Flexy-install", propagate: false, parameters:[string(name: "INSTANCE_NAME_PREFIX", value: OCP_PREFIX),string(name: "VARIABLES_LOCATION", value: "${var_loc}"),string(name: "JENKINS_AGENT_LABEL", value: JENKINS_AGENT_LABEL),text(name: "LAUNCHER_VARS",
                            value: "{ ${worker_type} installer_payload_image: 'registry.ci.openshift.org/ocp/release:${params.OCP_VERSION}'}"),text(name: "BUSHSLICER_CONFIG", value: ''),text(name: 'REPOSITORIES', value: '''
GIT_PRIVATE_URI=git@gitlab.cee.redhat.com:aosqe/cucushift-internal.git
GIT_PRIVATE_TEMPLATES_URI=https://gitlab.cee.redhat.com/aosqe/flexy-templates.git'''),
text(name: 'CREDENTIALS', value: '''
DYNECT_CREDENTIALS=b1666c61-4a76-40b7-950f-a3d40f721e59
REG_STAGE=41c2dd39-aad7-4f07-afec-efc052b450f5
REG_QUAY=c1802784-0f74-4b35-99fb-32dfa9a207ad
REG_CLOUD=fba37700-62f8-4883-8905-53f86461ba5b
REG_CONNECT=819c9e9f-1e9c-4d2b-9dc0-fc630674bc9b
REG_REDHAT=819c9e9f-1e9c-4d2b-9dc0-fc630674bc9b
REG_BREW_OSBS=brew-registry-osbs-mirror
REG_NIGHTLY_BUILDS=9a9187c6-a54c-452a-866f-bea36caea6f9
REG_CI_BUILDS=registry.svc.ci.openshift.org
GIT_FLEXY_SSH_KEY=e2f7029f-ab8d-4987-8950-39feb80d5fbd
GIT_PRIVATE_SSH_KEY=1d2207b6-15c0-4cb0-913a-637788d12257
REG_SVC_CI=9a9187c6-a54c-452a-866f-bea36caea6f9''' ) ]
                    } else {
                     copyArtifacts(
                        filter: '',
                        fingerprintArtifacts: true,
                        projectName: 'ocp-common/Flexy-install',
                        selector: specific(params.BUILD_NUMBER),
                        target: 'flexy-artifacts'
                       )
                     }
                 copyArtifacts(
                    fingerprintArtifacts: true,
                    projectName: 'ocp-common/Flexy-install',
                    selector: specific(params.BUILD_NUMBER),
                    filter: "workdir/install-dir/",
                    target: 'flexy-artifacts'
                   )
                if (fileExists("flexy-artifacts/workdir/install-dir/client_proxy_setting.sh")) {
                 sh "echo yes"
                 proxy_settings = sh returnStdout: true, script: 'cat flexy-artifacts/workdir/install-dir/client_proxy_setting.sh'
                 proxy_settings = proxy_settings.replace('export ', '')
                }

                ENV_VARS += '\n' + proxy_settings
                sh "echo $ENV_VARS"

                 }
            }
        }
        stage("Perf Testing"){
            agent { label params['JENKINS_AGENT_LABEL'] }
            steps{
                    script {
                        if (params.BUILD_NUMBER != "") {
                            build_string = params.BUILD_NUMBER
                        } else {
                            if( install.result.toString() == "SUCCESS" ) {
                                build_string = install.number.toString()
                            }
                        }
                        if( build_string != "DEFAULT" ) {
                          if(params.CI_TYPE == "cluster-density") {
                            loaded_ci = build job: "scale-ci/e2e-benchmarking-multibranch-pipeline/cluster-density", propagate: false, parameters:[string(name: "BUILD_NUMBER", value: "${build_string}"),string(name: "JENKINS_AGENT_LABEL", value: JENKINS_AGENT_LABEL),string(name: "JOB_ITERATIONS", value: JOB_ITERATIONS),text(name: "ENV_VARS", value: ENV_VARS),string(name: "SCALE_UP", value: SCALE_UP),string(name: "SCALE_DOWN", value: SCALE_DOWN),booleanParam(name: "WRITE_TO_FILE", value: WRITE_TO_FILE),string(name: "E2E_BENCHMARKING_REPO", value: E2E_BENCHMARKING_REPO),string(name: "E2E_BENCHMARKING_REPO_BRANCH", value: E2E_BENCHMARKING_REPO_BRANCH)]
                           } else if (params.CI_TYPE == "pod-density" ) {
                            loaded_ci = build job: "scale-ci/e2e-benchmarking-multibranch-pipeline/pod-density", propagate: false, parameters:[string(name: "BUILD_NUMBER", value: "${build_string}"),string(name: "JENKINS_AGENT_LABEL", value: JENKINS_AGENT_LABEL),string(name: "PODS", value: JOB_ITERATIONS),text(name: "ENV_VARS", value: ENV_VARS),string(name: "SCALE_UP", value: SCALE_UP),string(name: "SCALE_DOWN", value: SCALE_DOWN),booleanParam(name: "WRITE_TO_FILE", value: WRITE_TO_FILE),string(name: "E2E_BENCHMARKING_REPO", value: E2E_BENCHMARKING_REPO),string(name: "E2E_BENCHMARKING_REPO_BRANCH", value: E2E_BENCHMARKING_REPO_BRANCH) ]
                           } else if (params.CI_TYPE == "node-density") {
                            loaded_ci = build job: "scale-ci/e2e-benchmarking-multibranch-pipeline/node-density", propagate: false, parameters:[string(name: "BUILD_NUMBER", value: "${build_string}"),string(name: "JENKINS_AGENT_LABEL", value: JENKINS_AGENT_LABEL),string(name: "PODS_PER_NODE", value: PODS_PER_NODE),string(name: 'NODE_COUNT', value: NODE_COUNT),text(name: "ENV_VARS", value: ENV_VARS),string(name: "SCALE_UP", value: SCALE_UP),string(name: "SCALE_DOWN", value: SCALE_DOWN),booleanParam(name: "WRITE_TO_FILE", value: WRITE_TO_FILE),string(name: "E2E_BENCHMARKING_REPO", value: E2E_BENCHMARKING_REPO),string(name: "E2E_BENCHMARKING_REPO_BRANCH", value: E2E_BENCHMARKING_REPO_BRANCH) ]
                           } else if (params.CI_TYPE == "etcd-perf") {
                           loaded_ci = build job: "scale-ci/e2e-benchmarking-multibranch-pipeline/etcd-perf", propagate: false, parameters:[string(name: "BUILD_NUMBER", value: "${build_string}"),string(name: "JENKINS_AGENT_LABEL", value: JENKINS_AGENT_LABEL),string(name: "SCALE_UP", value: SCALE_UP),string(name: "SCALE_DOWN", value: SCALE_DOWN),text(name: "ENV_VARS", value: ENV_VARS),string(name: "E2E_BENCHMARKING_REPO", value: E2E_BENCHMARKING_REPO),string(name: "E2E_BENCHMARKING_REPO_BRANCH", value: E2E_BENCHMARKING_REPO_BRANCH)]
                           } else if (params.CI_TYPE == "max-namespaces") {
                           loaded_ci = build job: "scale-ci/e2e-benchmarking-multibranch-pipeline/max-namespaces", propagate: false,parameters:[string(name: "BUILD_NUMBER", value: "${build_string}"),string(name: "JENKINS_AGENT_LABEL", value: JENKINS_AGENT_LABEL),string(name: "NAMESPACE_COUNT", value: JOB_ITERATIONS),text(name: "ENV_VARS", value: ENV_VARS),string(name: "SCALE_UP", value: SCALE_UP),string(name: "SCALE_DOWN", value: SCALE_DOWN),booleanParam(name: "WRITE_TO_FILE", value: WRITE_TO_FILE),string(name: "E2E_BENCHMARKING_REPO", value: E2E_BENCHMARKING_REPO),string(name: "E2E_BENCHMARKING_REPO_BRANCH", value: E2E_BENCHMARKING_REPO_BRANCH) ]
                           } else if (params.CI_TYPE == "max-services") {
                           loaded_ci = build job: "scale-ci/e2e-benchmarking-multibranch-pipeline/max-services",propagate: false, parameters:[string(name: "BUILD_NUMBER", value: "${build_string}"),string(name: "JENKINS_AGENT_LABEL", value: JENKINS_AGENT_LABEL),string(name: "SERVICE_COUNT", value: JOB_ITERATIONS),text(name: "ENV_VARS", value: ENV_VARS),string(name: "SCALE_UP", value: SCALE_UP),string(name: "SCALE_DOWN", value: SCALE_DOWN),booleanParam(name: "WRITE_TO_FILE", value: WRITE_TO_FILE),string(name: "E2E_BENCHMARKING_REPO", value: E2E_BENCHMARKING_REPO),string(name: "E2E_BENCHMARKING_REPO_BRANCH", value: E2E_BENCHMARKING_REPO_BRANCH) ]
                           } else if (params.CI_TYPE == "pod-network-policy-test") {
                           loaded_ci = build job: "scale-ci/e2e-benchmarking-multibranch-pipeline/pod-network-policy-test", propagate: false, parameters:[string(name: "BUILD_NUMBER", value: "${build_string}"), string(name: "JENKINS_AGENT_LABEL", value: JENKINS_AGENT_LABEL),string(name: "SCALE_UP", value: SCALE_UP),string(name: "SCALE_DOWN", value: SCALE_DOWN),text(name: "ENV_VARS", value: ENV_VARS),string(name: "E2E_BENCHMARKING_REPO", value: E2E_BENCHMARKING_REPO),string(name: "E2E_BENCHMARKING_REPO_BRANCH", value: E2E_BENCHMARKING_REPO_BRANCH)]
                           } else if (params.CI_TYPE == "router-perf") {
                           loaded_ci = build job: "scale-ci/e2e-benchmarking-multibranch-pipeline/router-perf",propagate: false, parameters:[string(name: "BUILD_NUMBER", value: "${build_string}"),string(name: "SCALE_UP", value: SCALE_UP),string(name: "SCALE_DOWN", value: SCALE_DOWN),string(name: "JENKINS_AGENT_LABEL", value: JENKINS_AGENT_LABEL),text(name: "ENV_VARS", value: ENV_VARS),string(name: "E2E_BENCHMARKING_REPO", value: E2E_BENCHMARKING_REPO),string(name: "E2E_BENCHMARKING_REPO_BRANCH", value: E2E_BENCHMARKING_REPO_BRANCH)]
                           }else if (params.CI_TYPE == "storage-perf") {
                           loaded_ci = build job: "scale-ci/e2e-benchmarking-multibranch-pipeline/storage-perf", propagate: false, parameters:[string(name: "BUILD_NUMBER", value: "${build_string}"),string(name: "SCALE_UP", value: SCALE_UP),string(name: "SCALE_DOWN", value: SCALE_DOWN),string(name: "JENKINS_AGENT_LABEL", value: JENKINS_AGENT_LABEL),text(name: "ENV_VARS", value: ENV_VARS),string(name: "E2E_BENCHMARKING_REPO", value: E2E_BENCHMARKING_REPO),string(name: "E2E_BENCHMARKING_REPO_BRANCH", value: E2E_BENCHMARKING_REPO_BRANCH)]
                           } else{
                            sh 'echo "No Scale-ci Job"'
                           }

                          if( loaded_ci != null ) {
                            load_result = loaded_ci.result.toString()
                          }
                          }else{
                            sh 'echo "Installation of cluster failed, not running scale-ci job"'
                           }
                        }
            }
        }
        stage('Upgrade'){
            agent { label params['JENKINS_AGENT_LABEL'] }
            steps{
                script{
                    if( build_string != "DEFAULT" ) {
                        if( load_result == "SUCCESS" ) {
                            if( UPGRADE_VERSION != "" ) {
                                upgrade_ci = build job: "scale-ci/e2e-benchmarking-multibranch-pipeline/upgrade", propagate: false,parameters:[string(name: "BUILD_NUMBER", value: build_string),string(name: "MAX_UNAVAILABLE", value: MAX_UNAVAILABLE),string(name: "JENKINS_AGENT_LABEL", value: JENKINS_AGENT_LABEL),string(name: "UPGRADE_VERSION", value: UPGRADE_VERSION),booleanParam(name: "WRITE_TO_FILE", value: WRITE_TO_FILE),booleanParam(name: "ENABLE_FORCE", value: ENABLE_FORCE),booleanParam(name: "SCALE", value: SCALE),text(name: "ENV_VARS", value: ENV_VARS)]
                            } else {
                            sh 'echo "No upgrade version set, not running upgrade"'
                            }
                        } else{
                            sh 'echo "Scale ci job failed, not running upgrade"'
                           }

                    } else {
                        sh 'echo "Installation of cluster failed, not running upgrade"'
                    }
                }
            }
        }
        stage("Write out results") {
            agent { label params['JENKINS_AGENT_LABEL'] }
                steps{
                    script{
                      def status = "PASS"
                      if(params.WRITE_TO_FILE == true) {
                         sh "echo write to file $loaded_ci "
                          if ( install != null ) {
                            if( install.result.toString() != "SUCCESS" ) {
                                status = "Install Failed"
                            }
                          }
                         if( load_result == "SUCCESS" ) {
                            if ( upgrade_ci != null) {
                             if( upgrade_ci.result.toString()  != "SUCCESS") {
                               status = "Upgrade Failed"
                              }
                            }
                         } else {
                            status = "Load Failed"
                         }
                        if(loaded_ci != null ) {
                            loaded_url = loaded_ci.absoluteUrl
                        }
                        if(upgrade_ci != null ) {
                            upgrade_url = upgrade_ci.absoluteUrl
                        }
                        build job: 'scale-ci/e2e-benchmarking-multibranch-pipeline/write-scale-ci-results', propagate: false,parameters: [string(name: "JENKINS_AGENT_LABEL", value: JENKINS_AGENT_LABEL), string(name: "BUILD_NUMBER", value: build_string), string(name: 'CI_STATUS', value: "${status}"), string(name: 'UPGRADE_JOB_URL', value: upgrade_url),
                            string(name: 'CI_JOB_URL', value: loaded_url), booleanParam(name: 'ENABLE_FORCE', value: ENABLE_FORCE), booleanParam(name: 'SCALE', value: SCALE), string(name: 'LOADED_JOB_URL', value: BUILD_URL), string(name: 'JOB', value: "loaded-upgrade")]
                         }

                    }
                  }
        }
        stage('Destroy Flexy Cluster'){
            agent { label params['JENKINS_AGENT_LABEL'] }
            steps{
                script{
                    if(install != null && (install.result.toString() != "SUCCESS" || params.DESTROY_WHEN_DONE == true)) {
                        destroy_ci = build job: 'ocp-common/Flexy-destroy', parameters: [string(name: "BUILD_NUMBER", value: install.number.toString()),string(name: "JENKINS_AGENT_LABEL", value: JENKINS_AGENT_LABEL)]
                    } else if(install == null && params.DESTROY_WHEN_DONE == true) {
                        destroy_ci = build job: 'ocp-common/Flexy-destroy', parameters: [string(name: "BUILD_NUMBER", value: build_string),string(name: "JENKINS_AGENT_LABEL", value: JENKINS_AGENT_LABEL)]
                    }
                }
            }
        }
        stage('Setting Proper Status'){
            agent { label params['JENKINS_AGENT_LABEL'] }
            steps{
                script{
                if( build_string == "DEFAULT" ) {
                 sh 'echo "build failed"'
                 currentBuild.result = "FAILURE"

                }
                if( load_result != "SUCCESS" ) {
                    sh 'echo "load failed"'
                    currentBuild.result = "FAILURE"
                }
                if( upgrade_ci != null ) {
                    sh 'echo "upgrade not null"'
                    if( upgrade_ci.result.toString() != "SUCCESS" ) {

                         sh 'echo "upgrade failed"'
                         currentBuild.result = "FAILURE"
                    }
                }
                if( destroy_ci != null) {
                    sh 'echo "destroy not null"'
                    if( destroy_ci.result.toString() != "SUCCESS") {
                        sh 'echo "destroy failed"'
                        currentBuild.result = "FAILURE"
                    }
                }
             }
         }
         }

       }

}
