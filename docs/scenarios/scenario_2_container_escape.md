# Threat Emulation Scenario 2: Container Escape & gVisor Isolation

## The Threat
If an attacker compromises a container, their next goal is typically to break out of the container boundary and compromise the underlying host node. A common technique is attempting to mount host filesystems or reading sensitive host-mounted files like `/etc/shadow`.

## The Execution
To emulate this, we executed a privileged read attempt (`cat /etc/shadow`) inside two distinctly different environments:

1. **Standard Runtime:** The `nexus-workbench` pod (running via the default `runc` runtime).
2. **Hermetic Runtime:** The `nexus-athena` pod (running via our new Phase 2 `gvisor` RuntimeClass).

```bash
# Execution 1 (Standard)
kubectl exec -n soc nexus-workbench-5fd9bf9dc9-tjcdb -- bash -c 'cat /etc/shadow'

# Execution 2 (Hermetic)
kubectl exec -n soc nexus-athena-775f4f478c-n26jj -- bash -c 'cat /etc/shadow'
```

## The Detection (The Power of gVisor)
By monitoring our host-level eBPF tracing hooks (Tetragon), we observed a massive architectural difference between the two runtimes.

### Standard Container (`nexus-workbench`)
Because `runc` containers share the host's Linux kernel, the attacker's commands are executed directly as syscalls on the host. Tetragon immediately caught the malicious `cat` execution:

```json
{
  "process_exec": {
    "process": {
      "binary": "/usr/bin/cat",
      "arguments": "/etc/shadow",
      "pod": {
        "name": "nexus-workbench-5fd9bf9dc9-tjcdb"
      }
    }
  }
}
```
*Result: The attack hit the host kernel, but eBPF successfully logged the anomaly.*

### Hermetic Sandbox (`nexus-athena`)
When the exact same command was run inside the gVisor-backed `nexus-athena` pod, **Tetragon saw absolutely nothing**. 

*Why?* Because gVisor intercepts all syscalls from the container and executes them in a specialized, user-space kernel (the `runsc` Sentry). The attacker's `cat /etc/shadow` command was processed entirely inside the sandbox and denied. The underlying host kernel was never touched, rendering the attack invisible to host-level eBPF hooks.

## Conclusion

This scenario **illustrates a target-state** hermetic design (architecture Phase 2+),
not a claim that Phase 2 is already proven in the lab. Tetragon improves visibility
into standard workloads; gVisor is intended to **contain** high-assurance workloads
by intercepting syscalls in user space. Isolation strength depends on RuntimeClass
configuration and threat model — do not treat it as absolute or “impenetrable.”
If Athena is compromised inside gVisor, the goal is that host-kernel attack surface
is greatly reduced, not that escape is impossible by definition.
