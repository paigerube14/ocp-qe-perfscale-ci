package main

import (
	"k8s.io/client-go/discovery"
	"log"
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
	log.Fatal(err)

	defer testEnv.Stop()

	cl, err := discovery.NewDiscoveryClientForConfig(cfg)
	log.Fatal(err)

	schema, err := cl.OpenAPISchema()
	log.Fatal(err)

	log.Print(schema)
}
