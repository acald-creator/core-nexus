# Zeek (network metadata)

DaemonSet for [Zeek](https://zeek.org/) protocol/metadata logging. Complements Suricata
(ADR 0007 + ADR 0011): Suricata = signatures; Zeek = conn/DNS/HTTP context.

Vector collects stdout logs from pods labeled `app.kubernetes.io/name=zeek`.

```bash
kubectl apply -k deploy/kubernetes/system/zeek
```

**Lab note:** `eth0` may differ on Rancher Desktop lima VMs. Patch `ZEek_INTERFACE` or
node interface in `daemonset.yaml` if Zeek fails to attach.
