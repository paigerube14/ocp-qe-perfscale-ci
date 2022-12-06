package main

import (
	"k8s.io/client-go/discovery"
	"path/filepath"
	"sigs.k8s.io/controller-runtime/pkg/envtest"
)

func main() {

	// need to go through each of these folders: https://github.com/openshift/api
	// ignore some?
	testEnv := &envtest.Environment{
		CRDDirectoryPaths: []string{
			filepath.Join("vendor", "github.com", "openshift", "api", "network", "v1"),
		},
		ErrorIfCRDPathMissing: true,
	}

	cfg, err := testEnv.Start()
	handleErr(err)

	defer testEnv.Stop()

	cl, err := discovery.NewDsicoveryClientForConfig(cfg)
	handleErr(err)

	schema, err := cl.OpenAPISchema()
	handleErr()

	// Do whatever you want with the schema
}
