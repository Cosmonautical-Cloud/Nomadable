#! /bin/zsh

# Run Nomadable in check mode
ansible-playbook playbooks/main.yml --check --diff
