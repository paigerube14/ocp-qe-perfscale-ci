FROM quay.io/openshifttest/python:3.9

LABEL vendor="Red Hat Inc." maintainer="OCP QE Team"

RUN curl -sSL https://mirror.openshift.com/pub/openshift-v4/clients/ocp/stable/openshift-client-linux.tar.gz | tar -xvzf - oc &&  mv oc /bin && /usr/local/bin/python -m pip install --upgrade pip
