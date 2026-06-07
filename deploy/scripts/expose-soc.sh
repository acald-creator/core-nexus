#!/bin/sh
echo "Exposing SOC services to localhost..."

# Kill existing port-forwards
pkill -f "kubectl port-forward" || true

# Wazuh Dashboard (HTTPS)
kubectl port-forward -n nexus-soc svc/wazuh-dashboard 5601:5601 > /dev/null 2>&1 &
echo "Wazuh Dashboard exposed at https://localhost:5601"

# MinIO Console (HTTP)
kubectl port-forward -n soc svc/minio 9001:9001 > /dev/null 2>&1 &
echo "MinIO Console exposed at http://localhost:9001"

# Jupyter Workbench (HTTP)
kubectl port-forward -n soc svc/nexus-workbench 8888:8888 > /dev/null 2>&1 &
echo "Jupyter Workbench exposed at http://localhost:8888"

echo "Port forwarding is running in the background."
