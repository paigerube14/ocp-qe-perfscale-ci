FROM quay.io/openshifttest/python:3.9

LABEL vendor="Red Hat Inc." maintainer="OCP QE Team"

RUN curl -sSL https://mirror.openshift.com/pub/openshift-v4/clients/ocp/stable/openshift-client-linux-amd64-rhel8.tar.gz | tar -xvzf -  &&\
    mv kubectl /bin 

RUN apt-get update && apt-get install -y gettext-base uuid-runtime jq openssh-client sshpass && \
    ln -s /bin/bash /usr/bin/bash && /usr/local/bin/python -m pip install --upgrade pip && pip install virtualenv jq
