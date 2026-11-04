#!/usr/bin/env bash
# Boot three cloud-image VMs under libvirt/KVM for a SELinux-enabled cluster test.
#
# Containers cannot test SELinux: the policy belongs to the host kernel, and the
# GitHub-hosted Ubuntu runners use AppArmor. Real VMs boot the distro's own kernel
# and policy, so SELinux behaves as it does on a server.
#
# Usage: vms.sh <cloud image url> <inventory file to write>
set -euo pipefail

IMAGE_URL="$1"
INVENTORY="$2"
WORK=/var/lib/libvirt/images/autobase
NET_PREFIX=192.168.122
NODES=(pgnode01 pgnode02 pgnode03)
MEMORY_MB="${VM_MEMORY_MB:-3072}"
VCPUS="${VM_VCPUS:-2}"

[ -f ~/.ssh/id_ed25519 ] || ssh-keygen -q -t ed25519 -N "" -f ~/.ssh/id_ed25519
PUBKEY=$(cat ~/.ssh/id_ed25519.pub)

sudo mkdir -p "$WORK"
[ -f "$WORK/base.qcow2" ] || sudo curl -fsSL -o "$WORK/base.qcow2" "$IMAGE_URL"

for i in "${!NODES[@]}"; do
  name="${NODES[$i]}"
  ip="$NET_PREFIX.$((11 + i))"
  mac="52:54:00:00:00:$((11 + i))"

  sudo qemu-img create -q -f qcow2 -F qcow2 -b "$WORK/base.qcow2" "$WORK/$name.qcow2" 20G
  sudo virsh net-update default add ip-dhcp-host \
    "<host mac='$mac' name='$name' ip='$ip'/>" --live --config >/dev/null

  cat >"/tmp/$name-user-data" <<EOF
#cloud-config
hostname: $name
disable_root: false
users:
  - name: root
    ssh_authorized_keys:
      - $PUBKEY
# SELinux denials are only recorded in the audit log if auditd is running.
packages:
  - audit
runcmd:
  - systemctl enable --now auditd
EOF
  printf 'instance-id: %s\nlocal-hostname: %s\n' "$name" "$name" >"/tmp/$name-meta-data"

  sudo virt-install --name "$name" --memory "$MEMORY_MB" --vcpus "$VCPUS" \
    --disk "$WORK/$name.qcow2" --import \
    --osinfo detect=on,require=off \
    --network "network=default,mac=$mac" \
    --cloud-init "user-data=/tmp/$name-user-data,meta-data=/tmp/$name-meta-data" \
    --graphics none --noautoconsole >/dev/null
done

for i in "${!NODES[@]}"; do
  ip="$NET_PREFIX.$((11 + i))"
  for _ in $(seq 1 60); do
    ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=5 \
      -o LogLevel=ERROR "root@$ip" true 2>/dev/null && break
    sleep 5
  done
  echo "${NODES[$i]} ($ip): $(ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
    -o LogLevel=ERROR "root@$ip" 'getenforce; uname -r' | tr '\n' ' ')"
done

ips=()
for i in "${!NODES[@]}"; do ips+=("$NET_PREFIX.$((11 + i))"); done

cat >"$INVENTORY" <<EOF
[etcd_cluster]
${ips[0]}
${ips[1]}
${ips[2]}

[consul_instances]
${ips[0]} consul_node_role=server
${ips[1]} consul_node_role=server
${ips[2]} consul_node_role=server

[balancers]
${ips[0]}
${ips[1]}
${ips[2]}

[master]
${ips[0]} hostname=${NODES[0]} postgresql_exists=false

[replica]
${ips[1]} hostname=${NODES[1]} postgresql_exists=false
${ips[2]} hostname=${NODES[2]} postgresql_exists=false

[postgres_cluster:children]
master
replica

[all:vars]
ansible_connection=ssh
ansible_ssh_port=22
ansible_ssh_user=root
ansible_ssh_common_args='-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null'
EOF
