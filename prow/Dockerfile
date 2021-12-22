FROM quay.io/openshifttest/python:3.9

LABEL vendor="Red Hat Inc." maintainer="OCP QE Team"

RUN curl -sSL https://mirror.openshift.com/pub/openshift-v4/clients/ocp/stable/openshift-client-linux.tar.gz | tar -xvzf -  &&  mv oc /bin && mv kubectl /bin && apt-get update && apt-get install gettext-base && apt-get install uuid-runtime && ln -s /bin/bash /usr/bin/bash && /usr/local/bin/python -m pip install --upgrade pip && pip install virtualenv
