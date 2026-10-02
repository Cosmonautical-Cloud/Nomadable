# Inventory File Guide for Nomadable

This document explains how to structure your Ansible inventory file (`hosts.yml`) when deploying a mixed macOS/Ubuntu cluster via `playbooks/main.yml`.

Nomadable itself has no OS-specific logic — it just imports [Nomadintosh](https://github.com/Cosmonautical-Cloud/Nomadintosh)'s and [Nomaduntu](https://github.com/Cosmonautical-Cloud/Nomaduntu)'s own playbooks, each of which internally gates every task on `ansible_facts['os_family']` (`Darwin` / `Debian`). A single inventory group can freely mix macOS and Ubuntu hosts — each host only ever runs the half of the combined playbook that matches its own OS, and both OS's Consul/Nomad roles derive `datacenter` from the same inventory group name, so they end up in the same datacenter regardless of platform.

For the full host-variable reference, see each child project's own docs — this file only covers what's specific to running them together:

- [Nomadintosh inventory docs](https://github.com/Cosmonautical-Cloud/Nomadintosh/blob/main/inventory/README.md) (macOS host variables: `server.enabled`, `container.enabled`, `podman.enabled`, `docker.enabled`, `seaweedfs.*`, `nfs_mounts_shares`, `volumes`)
- [Nomaduntu inventory docs](https://github.com/Cosmonautical-Cloud/Nomaduntu/blob/main/inventory/README.md) (Ubuntu host variables: `server.enabled`, `docker.enabled`, `nfs_mounts_shares`, `volumes`)

## Joining an existing external cluster

If you run each OS group's playbook separately against a *partial* inventory (e.g. Semaphore running Nomadintosh against only your macOS hosts, and Nomaduntu against only your Ubuntu hosts, rather than a single Nomadable run against a combined inventory), a group with no `server.enabled: true` hosts of its own won't automatically find the real Consul/Nomad servers. Both child projects support the same two optional variables for this:

| Variable | Effect |
|---|---|
| `existing_consul_datacenter` | Fixes Consul's `datacenter` to a known value instead of deriving it from whichever `server.enabled` host that run happens to find. |
| `existing_cluster_servers` | A list of hostnames/IPs merged into `retry_join` for both Consul and Nomad. |

Running a single Nomadable playbook against a combined inventory (all hosts, both OSes, in one run) makes this unnecessary — every `server.enabled: true` host in the run is already visible to every other host's template, whatever its OS.

## Example inventory with mixed hosts

```yaml
all:
  vars:
    ansible_user: violet
    ansible_ssh_private_key_file: ~/.ssh/id_rsa
    nas_host: 192.0.2.10              # NFS server - required whenever any host sets nfs_mounts_shares

jellify:
  hosts:
    galileo.jellify.app:            # macOS - handled by Nomadintosh
      container:
        enabled: true
      nfs_mounts_shares:
        - share_export_path: /var/nfs/shared/Jellify
    kepler.jellify.app:              # Ubuntu - handled by Nomaduntu
      docker:
        enabled: true
      nfs_mounts_shares:
        - share_export_path: /var/nfs/shared/Jellify
```

The same share entry mounts at a per-OS path: `galileo` gets `/Volumes/Jellify` (Nomadintosh's `volume_mount_path` + the export's last path component), `kepler` gets `/mnt/jellify` (Nomaduntu's, lowercased) — see each child project's `nfs_mounts` role README for the exact rule.

`nas_host` has no default in either child project — it's site-specific, so set it yourself (inventory `group_vars`/`host_vars`, or extra vars such as Semaphore variables). Any host with `nfs_mounts_shares` but no `nas_host` fails before anything is changed.
