#!/bin/bash

is_base64() {
  # Check if input is base64 encoded
  if [[ "$1" =~ ^[A-Za-z0-9+/=]+$ ]]; then
    return 0
  else
    return 1
  fi
}

# Check if ANSIBLE_INVENTORY_JSON is set and create inventory.json if it is
if [[ -n "${ANSIBLE_INVENTORY_JSON}" ]]; then
  if is_base64 "${ANSIBLE_INVENTORY_JSON}"; then
    echo "Creating inventory.json with the (base64 decoded) content of ANSIBLE_INVENTORY_JSON"
    echo "${ANSIBLE_INVENTORY_JSON}" | base64 -d > /autobase/inventory.json
  else
    echo "Creating inventory.json with the content of ANSIBLE_INVENTORY_JSON"
    echo "${ANSIBLE_INVENTORY_JSON}" > /autobase/inventory.json
  fi
  # Set ANSIBLE_INVENTORY environment variable
  export ANSIBLE_INVENTORY=/autobase/inventory.json
fi

# Check if SSH_PRIVATE_KEY_CONTENT is set and create the SSH private key file if it is
if [[ -n "${SSH_PRIVATE_KEY_CONTENT}" ]]; then
  mkdir -p /root/.ssh
  if is_base64 "${SSH_PRIVATE_KEY_CONTENT}"; then
    echo "Creating SSH private key file with the (base64 decoded) content of SSH_PRIVATE_KEY_CONTENT"
    echo "${SSH_PRIVATE_KEY_CONTENT}" | base64 -d > /root/.ssh/id_rsa
  else
    echo "Creating SSH private key file with the content of SSH_PRIVATE_KEY_CONTENT"
    echo "${SSH_PRIVATE_KEY_CONTENT}" > /root/.ssh/id_rsa
  fi

  chmod 600 /root/.ssh/id_rsa

  # Ensure the key file ends with a newline
  sed -i -e '$a\' /root/.ssh/id_rsa

  echo "Checking SSH private key with ssh-keygen"
  ssh-keygen -y -f /root/.ssh/id_rsa > /dev/null

  # Set ANSIBLE_PRIVATE_KEY_FILE environment variable
  export ANSIBLE_PRIVATE_KEY_FILE=/root/.ssh/id_rsa
fi

# Execute the passed command
exec "$@"
