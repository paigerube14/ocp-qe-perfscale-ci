# E2E Benchmarking CI Repo - Cluster Post Config

## Purpose

A job that will allow adding and removing firewall ports for HostNetwork Uperf testing. Can be extended to do other operations. To be called after fresh Flexy-cluster is created. And then call again before flexy-destroy to revert any changes made to the cluster.


## Current supported cloud cluster types
* AWS
* Azure
* GCP
* Vsphere
* Alicloud/Alibaba (only infra nodes)

### Author
Paige Rubendall <@paigerube14 on Github>
