# Loads this repository's top-level group_vars/ (and host_vars/) for every
# run, whatever inventory it uses - including a Semaphore static inventory,
# which lives outside the repo, so Ansible's own host_group_vars plugin never
# looks here. playbooks/group_vars/ wouldn't do either: playbook-relative
# group_vars only apply to plays in that directory, and every play in
# main.yml is imported from the child collections.
#
# Ansible picks up vars_plugins/ next to the playbook automatically, and
# REQUIRES_ENABLED = False runs it without any ansible.cfg entry, so nothing
# extra has to be configured wherever the playbook runs.

from __future__ import annotations

import os

from ansible.plugins.vars.host_group_vars import VarsModule as HostGroupVarsModule

DOCUMENTATION = """
    name: nomadable_group_vars
    short_description: Load Nomadable's top-level group_vars/ and host_vars/
    description:
      - Same as ansible.builtin.host_group_vars, but always reads from the
        repository root rather than from beside the inventory source.
    extends_documentation_fragment:
      - vars_plugin_staging
"""

REPO_ROOT = os.path.realpath(os.path.join(os.path.dirname(__file__), "..", ".."))


class VarsModule(HostGroupVarsModule):
    REQUIRES_ENABLED = False

    def get_vars(self, loader, path, entities, cache=True):
        return super().get_vars(loader, REPO_ROOT, entities, cache)
