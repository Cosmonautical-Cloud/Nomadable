# Nomadable

<img src="logo.png" alt="Hashicorp Nomad Logo" width="200" height="225"  />

An Ansible playbook for deploying [Nomad](https://developer.hashicorp.com/nomad/docs) + [Consul](https://developer.hashicorp.com/consul/docs) across a mixed-OS cluster.

Nomadable is the parent playbook that composes the platform-specific child playbooks:

- **[Nomadintosh](https://github.com/Cosmonautical-Cloud/Nomadintosh)** — macOS (Apple Silicon) nodes managed via Homebrew and LaunchAgents
- **[Nomaduntu](https://github.com/Cosmonautical-Cloud/Nomaduntu)** — Ubuntu nodes managed via the HashiCorp apt repository and systemd

A single inventory can contain a mix of macOS and Ubuntu hosts. Nomadable dispatches to the correct child playbook based on the `ansible_os_family` fact of each host, so all nodes end up in the same Nomad/Consul datacenter regardless of operating system.

**[Nomad](https://developer.hashicorp.com/nomad/docs)** is a workload orchestrator by HashiCorp. It schedules and runs containerised and bare-metal applications across a cluster of machines.

**[Consul](https://developer.hashicorp.com/consul/docs)** is a service mesh and service discovery tool, also by HashiCorp. It provides a distributed key-value store, health checking, and DNS-based service discovery. Nomad integrates with Consul natively to handle cluster membership and service registration.

## Scope

Nomadable (and the [Nomadintosh](https://github.com/Cosmonautical-Cloud/Nomadintosh)/[Nomaduntu](https://github.com/Cosmonautical-Cloud/Nomaduntu) child playbooks it composes) provisions the Nomad + Consul **agents** themselves — it intentionally does not deploy the job specs those agents run. Nomadintosh used to also template and register a couple of job specs directly, but that role was removed 2026-09-05; job specs now live in dedicated repos instead — [`Jellify/Nomad-Jobs`](https://github.com/anultravioletaurora/Nomad-Jobs) (Terraform-managed) and a legacy hand-deployed `nomad-jobs` repo. If you're looking to add or change a running job, it belongs in one of those, not here.

## Requirements

- Ansible installed on the control machine
- The Nomadintosh/Nomaduntu collections (and their shared [`cosmonautical.notify`](https://github.com/Cosmonautical-Cloud/ansible-collection-notify) dependency), pinned in [`collections/requirements.yml`](collections/requirements.yml):
  ```
  ansible-galaxy collection install -r collections/requirements.yml
  ```
- SSH access to all hosts in the inventory

## Inventory

Each host's Nomad [**datacenter**](https://developer.hashicorp.com/nomad/docs/configuration#datacenter) is its DNS domain label (`hopper.jellify.app` → `jellify`), and the Consul datacenter is the Consul servers' domain label — so hosts must be listed by fully qualified name. Inventory groups are freeform: organise hosts however you like, and target groups from roles (via [group variables](#group-variables)) and Nomad jobs (via `meta.inventory_groups`), mixing hosts across datacenters. A single group may contain a mix of macOS and Ubuntu hosts.

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
- [Nomadintosh inventory docs](https://github.com/Cosmonautical-Cloud/Nomadintosh/blob/main/inventory/README.md)
- [Nomaduntu inventory docs](https://github.com/Cosmonautical-Cloud/Nomaduntu)

## Playbooks

Ansible Galaxy has no synopsis/description field for playbooks shipped inside a collection (unlike roles, which get one from `meta/main.yml`), so this is the canonical place it's documented:

| Playbook | Description |
|---|---|
| `playbooks/main.yml` | Full deployment — imports `cosmonautical.nomadintosh.deploy` and `cosmonautical.nomaduntu.deploy` against whatever's in the inventory; each host only ever runs the half matching its own OS. See [What it does](#what-it-does) below for the full breakdown. Idempotent — safe to rerun. |
| `playbooks/reboot.yml` | Reboots every host in the inventory, serially within each OS's own playbook — imports `cosmonautical.nomadintosh.reboot` and `cosmonautical.nomaduntu.reboot`. Does not run the full deployment. |
| `playbooks/clean.yml` | Prunes stale upgrade residue on every host — `brew cleanup` on macOS, `apt autoremove` on Ubuntu — by importing `cosmonautical.nomadintosh.clean` and `cosmonautical.nomaduntu.clean`. Does not run the full deployment. |

### Running them

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

- `./reboot.zsh` — reboots every host in the inventory, one at a time:

```zsh
./reboot.zsh
```

- `./clean.zsh` — prunes stale upgrade residue on every host:

```zsh
./clean.zsh
```


## What it does

Nomadable delegates to the appropriate child playbook for each host based on its OS:

- **macOS hosts** → [Nomadintosh](https://github.com/Cosmonautical-Cloud/Nomadintosh) — see that project's README for a full breakdown of what is configured.
- **Ubuntu hosts** → [Nomaduntu](https://github.com/Cosmonautical-Cloud/Nomaduntu) — see that project's README for a full breakdown of what is configured.

Both child playbooks derive datacenters the same way — Nomad from each host's DNS domain, Consul from the servers' domain — so macOS and Ubuntu hosts in the same domain land in the same datacenter. If you instead run each OS group separately against a partial inventory (e.g. per-OS Semaphore tasks), see [inventory/README.md](inventory/README.md#joining-an-existing-external-cluster) for `existing_consul_datacenter`/`existing_cluster_servers`, which both child projects support for joining a control plane whose servers aren't part of that particular run's own inventory.

## Remarks

- **Multi-platform clusters** — Nomad's native support for multiple platforms means macOS and Ubuntu nodes can participate in the same cluster and share workloads. Platform-specific capabilities (e.g. hardware acceleration on macOS, GPU passthrough on Linux) are exposed via Nomad node attributes and can be targeted with job constraints.
- **Child playbook versions** — Each child playbook is maintained independently. Pin submodule or collection versions as appropriate for your environment to avoid unexpected changes on deployment.

## Group variables

Anything that should be versioned and reviewed — and bumped by Renovate — lives in [`group_vars/`](group_vars), not in the inventory itself. The inventory (local `inventory/hosts.yml` or Semaphore's Static inventory) only says which hosts are in which group.

[`playbooks/vars_plugins/nomadable_group_vars.py`](playbooks/vars_plugins/nomadable_group_vars.py) loads `group_vars/` (and `host_vars/`, if present) for every run, whatever inventory it uses, with nothing to configure: Ansible picks up `vars_plugins/` next to the playbook on its own. It's needed because Ansible normally only reads `group_vars/` beside the inventory source, which a Semaphore Static inventory isn't, or beside the playbook, which only applies to plays in that directory, and every play in `playbooks/main.yml` is imported from the child collections. These load at group_vars precedence, so a host's own inventory vars still override them; Semaphore's extra variables override both. `main.yml` stops before deploying anything if the plugin didn't run, rather than deploying hosts without their group's toolchain.

| Group | What it provisions |
|---|---|
| `github_runners` | Toolchain for GitHub Actions self-hosted runners — pinned bun, Maestro, Android SDK (see [`github_runners.yml`](group_vars/github_runners.yml)). The runner itself is the `actions-runner` Nomad job in Jellify/Nomad-Jobs, which targets this group via Nomadintosh's `inventory_groups` node meta |

To add a runner, add the host to `github_runners` in the inventory — its datacenter still comes from its DNS name, so a group can mix hosts from any datacenter.

Versions annotated with a `# renovate:` comment are bumped by Renovate (see `renovate.json`). Merging a bump doesn't touch any host — it lands on the next deploy.

## Wiring into Semaphore

1. Add this repository as a Semaphore Repository, and a Key Store entry (SSH key plus become/sudo password) covering every host in the inventory — the same credentials `inventory/hosts.yml` would otherwise hold locally.
2. Add a Semaphore Inventory. `inventory/hosts.yml` is gitignored — it holds plaintext SSH/become credentials, not something to commit — so define the hosts directly as a Semaphore "Static" inventory instead of pointing at a file in this repo. Use [`inventory/hosts.example.yml`](inventory/hosts.example.yml) as the shape to replicate.
3. Add a Task Template of type "Ansible Playbook": this repository, `playbooks/main.yml`, and the Inventory/Key Store from the steps above. No extra CLI arguments are needed: the committed [group variables](#group-variables) load on top of the Static inventory automatically. Semaphore installs `collections/requirements.yml` automatically before each run, so both child collections are pulled fresh from Galaxy at whatever version is pinned there — no separate `ansible-galaxy collection install` step to configure, and no stale local collection cache to worry about (unlike a manual `./deploy.zsh` run — see the note on `collections/requirements.yml`'s pins).
4. There's no `plan`/`apply` split here the way Nomad-Jobs' Terraform pipeline has — Ansible has no true dry-run equivalent to `terraform plan`, only `--check --diff` (what `./check.zsh` runs locally), which isn't guaranteed identical to the real run for every module. If a review step before applying matters, add a second Task Template running the same playbook with `--check --diff` appended, to read before triggering the real one.
5. One Static inventory covering every host needs nothing else. If you split inventories instead (e.g. one per datacenter, each with its own Task Template or Variable Group), any run whose inventory has no `server.enabled` hosts must set `existing_consul_datacenter` and `existing_cluster_servers` in its extra variables (see [inventory/README.md](inventory/README.md#joining-an-existing-external-cluster)) — otherwise those hosts would derive a Consul datacenter of their own and have no servers to join. Their Nomad datacenter still comes from DNS either way.
