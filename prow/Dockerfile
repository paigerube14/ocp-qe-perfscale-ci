FROM quay.io/fedora/fedora:34

LABEL vendor="Red Hat Inc." maintainer="OCP QE Team"

RUN dnf -y install python3-pip && curl -sSL https://mirror.openshift.com/pub/openshift-v4/clients/ocp/stable/openshift-client-linux.tar.gz |  tar  -xvzf  - oc && \
    mv oc /bin && /usr/bin/python3 -m pip install --upgrade pip &&  python3 -m pip install virtualenv --user 
