# Local Tooling

This directory stores repo-local runtime assets:

- `tools/jenkins/jenkins.war`: portable Jenkins runtime
- `tools/jenkins/home/`: Jenkins home directory
- `tools/ansible/Dockerfile`: Dockerized Ansible runner

Install and start the tools with the PowerShell scripts in `scripts/`.

Notes:

- Jenkins is launched with `--enable-future-java` because this machine uses Java 26.
- Ansible runs from the local Docker image `sentinelci-ansible:local`.
