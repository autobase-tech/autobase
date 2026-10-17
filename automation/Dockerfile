FROM debian:13-slim
LABEL maintainer="Autobase <info@autobase.tech>"

USER root

# Set SHELL to Bash to ensure pipefail is supported
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Copy autobase repository
COPY automation /autobase/automation

# Install required packages, Python dependencies, Ansible requirements
RUN apt-get clean && rm -rf /var/lib/apt/lists/partial \
  && apt-get update -o Acquire::CompressionTypes::Order::=gz \
  && DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends -y \
     ca-certificates gnupg keychain debian-archive-keyring apt-transport-https \
     git python3 python3-dev python3-pip ssh-client sshpass gcc g++ cmake make libssl-dev curl lsb-release \
  # requirements
  && pip3 install --break-system-packages --no-cache-dir --retries 3 --timeout 60 \
    -r /autobase/automation/requirements.txt \
  && ansible-galaxy install --force -r /autobase/automation/requirements.yml \
  && ansible-galaxy collection list \
  # Azure collection requirements
  && pip3 install --break-system-packages --no-cache-dir --retries 3 --timeout 60 \
    -r /root/.ansible/collections/ansible_collections/azure/azcollection/requirements.txt \
  # cleanup
  && apt-get autoremove -y --purge gnupg git python3-dev gcc g++ cmake make libssl-dev \
  && apt-get clean -y autoclean \
  && rm -rf /var/lib/apt/lists/* /tmp/* \
  && chmod +x /autobase/automation/entrypoint.sh

# Link collection source for Ansible runtime
RUN mkdir -p /root/.ansible/collections/ansible_collections/vitabaks \
  && ln -sfn /autobase/automation /root/.ansible/collections/ansible_collections/vitabaks/autobase

# Set environment variables
ENV ANSIBLE_COLLECTIONS_PATH=/root/.ansible/collections:/usr/local/lib/python3.13/dist-packages
ENV ANSIBLE_CONFIG=/autobase/automation/ansible.cfg
ENV USER=root

WORKDIR /autobase/automation/playbooks

ENTRYPOINT ["/autobase/automation/entrypoint.sh"]
