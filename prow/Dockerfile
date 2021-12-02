FROM python:3.8

LABEL vendor="Red Hat Inc." maintainer="OCP QE Team"

RUN curl https://mirror.openshift.com/pub/openshift-v4/x86_64/clients/ocp/stable-4.9/openshift-client-linux.tar.gz |  tar  -xvzf  - oc && \
    mv oc /bin && /usr/local/bin/python -m pip install --upgrade pip