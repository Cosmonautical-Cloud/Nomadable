# Nomadable

<img src="logo.png" alt="Hashicorp Nomad Logo" width="200" height="225"  />

An Ansible playbook for deploying [Nomad](https://developer.hashicorp.com/nomad/docs) + [Consul](https://developer.hashicorp.com/consul/docs) across a mixed-OS cluster.

Nomadable is the parent playbook that composes the platform-specific child playbooks:

- **[Nomadintosh](https://github.com/anultravioletaurora/Nomadintosh)** — macOS (Apple Silicon) nodes managed via Homebrew and LaunchAgents
- **[Nomaduntu](https://github.com/anultravioletaurora/Nomaduntu)** — Ubuntu nodes managed via the HashiCorp apt repository and systemd

A single inventory can contain a mix of macOS and Ubuntu hosts. Nomadable dispatches to the correct child playbook based on the `ansible_os_family` fact of each host, so all nodes end up in the same Nomad/Consul datacenter regardless of operating system.

**[Nomad](https://developer.hashicorp.com/nomad/docs)** is a workload orchestrator by HashiCorp. It schedules and runs containerised and bare-metal applications across a cluster of machines.

**[Consul](https://developer.hashicorp.com/consul/docs)** is a service mesh and service discovery tool, also by HashiCorp. It provides a distributed key-value store, health checking, and DNS-based service discovery. Nomad integrates with Consul natively to handle cluster membership and service registration.

## Requirements

- Ansible installed on the control machine
- The Nomadintosh/Nomaduntu collections, pinned in [`collections/requirements.yml`](collections/requirements.yml):
  ```
  ansible-galaxy collection install -r collections/requirements.yml
  ```
- SSH access to all hosts in the inventory

## Inventory

Hosts are organised into named groups; the group name becomes the Consul/Nomad [**datacenter**](https://developer.hashicorp.com/consul/docs/reference/agent/configuration-file/general#datacenter) for every host in that group. A single group may contain a mix of macOS and Ubuntu hosts.

Example inventory with mixed hosts:

```yaml
all:
  children:
    cosmonautical:
      hosts:
        mac1.example.com:
          server:
            enabled: true
        mac2.example.com: {}
        ubuntu1.example.com: {}
```

See the individual child playbook READMEs for the full list of supported host variables:
- [Nomadintosh inventory docs](https://github.com/anultravioletaurora/Nomadintosh/blob/main/inventory/README.md)
- [Nomaduntu inventory docs](https://github.com/anultravioletaurora/Nomaduntu)

## Running the playbook

Run a full deployment across all hosts:

```zsh
ansible-playbook -i inventory/hosts.yml playbooks/main.yml
```

To limit execution to a single host or group:

```zsh
ansible-playbook -i inventory/hosts.yml playbooks/main.yml --limit <hostname>
```

### Deployment scripts

The repository includes helper scripts for common workflows:

- `./deploy.zsh` — runs the full deployment:

```zsh
./deploy.zsh
```

- `./check.zsh` — runs the playbook in Ansible check mode with diff output:

```zsh
./check.zsh
```


## What it does

Nomadable delegates to the appropriate child playbook for each host based on its OS:

- **macOS hosts** → [Nomadintosh](https://github.com/anultravioletaurora/Nomadintosh) — see that project's README for a full breakdown of what is configured.
- **Ubuntu hosts** → [Nomaduntu](https://github.com/anultravioletaurora/Nomaduntu) — see that project's README for a full breakdown of what is configured.

Both child playbooks configure Consul and Nomad with a shared datacenter derived from the inventory group name, so all nodes in a group join the same cluster regardless of OS. If you instead run each OS group separately against a partial inventory (e.g. per-OS Semaphore tasks), see [inventory/README.md](inventory/README.md#joining-an-existing-external-cluster) for `existing_consul_datacenter`/`existing_cluster_servers`, which both child projects support for joining a control plane whose servers aren't part of that particular run's own inventory.

## Remarks

- **Multi-platform clusters** — Nomad's native support for multiple platforms means macOS and Ubuntu nodes can participate in the same cluster and share workloads. Platform-specific capabilities (e.g. hardware acceleration on macOS, GPU passthrough on Linux) are exposed via Nomad node attributes and can be targeted with job constraints.
- **Child playbook versions** — Each child playbook is maintained independently. Pin submodule or collection versions as appropriate for your environment to avoid unexpected changes on deployment.

## Wiring into Semaphore

1. Add this repository as a Semaphore Repository, and a Key Store entry (SSH key plus become/sudo password) covering every host in the inventory — the same credentials `inventory/hosts.yml` would otherwise hold locally.
2. Add a Semaphore Inventory. `inventory/hosts.yml` is gitignored — it holds plaintext SSH/become credentials, not something to commit — so define the hosts directly as a Semaphore "Static" inventory instead of pointing at a file in this repo. Use [`inventory/hosts.example.yml`](inventory/hosts.example.yml) as the shape to replicate.
3. Add a Task Template of type "Ansible Playbook": this repository, `playbooks/main.yml`, and the Inventory/Key Store from the steps above. Semaphore installs `collections/requirements.yml` automatically before each run, so both child collections are pulled fresh from Galaxy at whatever version is pinned there — no separate `ansible-galaxy collection install` step to configure, and no stale local collection cache to worry about (unlike a manual `./deploy.zsh` run — see the note on `collections/requirements.yml`'s pins).
4. There's no `plan`/`apply` split here the way Nomad-Jobs' Terraform pipeline has — Ansible has no true dry-run equivalent to `terraform plan`, only `--check --diff` (what `./check.zsh` runs locally), which isn't guaranteed identical to the real run for every module. If a review step before applying matters, add a second Task Template running the same playbook with `--check --diff` appended, to read before triggering the real one.
5. Running this combined playbook through Semaphore, against a single inventory covering every host, means `existing_consul_datacenter`/`existing_cluster_servers` (see [inventory/README.md](inventory/README.md#joining-an-existing-external-cluster)) shouldn't be needed — those exist for the *partial*-inventory case (e.g. separate per-OS Nomadintosh/Nomaduntu Semaphore templates), which this setup replaces.
