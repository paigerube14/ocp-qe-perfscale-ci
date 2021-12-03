FROM python:3.8

LABEL vendor="Red Hat Inc." maintainer="OCP QE Team"

RUN curl -sSL https://mirror.openshift.com/pub/openshift-v4/clients/ocp/stable/openshift-client-linux.tar.gz |  tar  -xvzf  - oc && \
    mv oc /bin && /usr/local/bin/python3 -m pip install --upgrade pip &&  python3 -m pip install virtualenv --user 