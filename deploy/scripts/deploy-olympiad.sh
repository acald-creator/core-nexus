#!/bin/sh

set -e

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/../.." 2>/dev/null && pwd || pwd)
COMPOSE_DIR="$REPO_ROOT/deploy/compose"
WORKBENCH_SCRIPT="$REPO_ROOT/deploy/scripts/workbench.sh"

if [ ! -d "$COMPOSE_DIR" ]; then
    echo "Error: Compose directory not found."
    exit 1
fi

echo "Creating volumes for persistence..."
docker volume create pihole_dns_data || true
docker volume create portainer_data || true

echo "Starting Docker Compose Baseline (Pi-hole, Portainer, Nexus Console)..."
docker compose -f "$COMPOSE_DIR/baseline.yml" up -d --build

echo "Waiting for baseline services to stabilize..."
sleep 15

echo "Intiating Docker Swarm"
docker swarm init || true
echo y | docker network rm ingress || true
docker network create --opt encrypted --driver overlay ingress || true

# Prepare Firefox Homepage override
# wget https://raw.githubusercontent.com/acald-creator/underground-nexus/main/Production%20Artifacts/firefox-homepage.sh && \
#     sh firefox-homepage.sh || true

# if [ -f "$WORKBENCH_SCRIPT" ]; then
#     sh "$WORKBENCH_SCRIPT"
# fi

echo "Deploying KuberNexus (k3d)"

echo "Installing Kubectl..."
if ! command -v kubectl >/dev/null 2>&1; then
    curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" && sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
fi

echo "Installing k3d..."
if ! command -v k3d >/dev/null 2>&1; then
    wget -q -O - https://raw.githubusercontent.com/k3d-io/k3d/main/install.sh | bash
fi

# Create Kubernetes Cluster
if k3d cluster list | grep -q KuberNexus; then
    echo "KuberNexus cluster already exists."
else
    k3d cluster create KuberNexus \
        -p 8080:80@loadbalancer \
        -p 8443:8443@loadbalancer \
        -p 2222:22@loadbalancer \
        -p 179:179@loadbalancer \
        -p 2375:2376@loadbalancer \
        -p 2378:2379@loadbalancer \
        -p 2381:2380@loadbalancer \
        -p 8472:8472@loadbalancer \
        -p 8843:443@loadbalancer \
        -p 4789:4789@loadbalancer \
        -p 9099:9099@loadbalancer \
        -p 9100:9100@loadbalancer \
        -p 7443:9443@loadbalancer \
        -p 9796:9796@loadbalancer \
        -p 6783:6783@loadbalancer \
        -p 10250:10250@loadbalancer \
        -p 10254:10254@loadbalancer \
        -p 31896:31896@loadbalancer
fi

echo "Building and importing Workbench image..."
docker build -t local/nexus-workbench:latest -f "$REPO_ROOT/platform/workbench/Dockerfile" "$REPO_ROOT/platform/workbench"
k3d image import local/nexus-workbench:latest -c KuberNexus

echo "Applying Kubernetes manifests via Kustomize..."
if [ -d "$REPO_ROOT/deploy/kubernetes/soc/overlays/test" ]; then
    # Create wazuh-auth secret if it doesn't exist
    kubectl create namespace nexus-soc --dry-run=client -o yaml | kubectl apply -f -
    kubectl create secret generic wazuh-auth -n nexus-soc \
      --from-literal=indexer-username=admin \
      --from-literal=indexer-password=admin \
      --from-literal=dashboard-username=admin \
      --from-literal=dashboard-password=admin \
      --from-literal=api-username=wazuh-wui \
      --from-literal=api-password=admin \
      --dry-run=client -o yaml | kubectl apply -f -

    kubectl apply -k "$REPO_ROOT/deploy/kubernetes/soc/overlays/test" --enable-helm
else
    echo "Kustomize overlay not found, skipping..."
fi

echo "Deployment Completed Successfully."
