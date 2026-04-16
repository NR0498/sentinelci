# SentinelCI

[![CI Pipeline](https://github.com/<your-org>/<your-repo>/actions/workflows/ci.yml/badge.svg)](https://github.com/<your-org>/<your-repo>/actions/workflows/ci.yml)

Replace `<your-org>/<your-repo>` in the badge URL after pushing the repository to GitHub.

SentinelCI is a demo-ready DevSecOps project built around a FastAPI service, automated CI/CD, security scanning, Docker packaging, Jenkins orchestration, Ansible deployment, and Terraform-based infrastructure simulation. The repository is set up for both clean PASS screenshots and intentional FAIL screenshots.

## Project Structure

```text
sentinelci/
|-- app/
|   |-- __init__.py
|   |-- main.py
|   |-- requirements.txt
|   `-- requirements-vulnerable.txt
|-- ansible/
|   `-- deploy.yml
|-- deploy/
|   `-- nginx/
|       `-- default.conf
|-- demo/
|   |-- trivy-safe.json
|   `-- trivy-vulnerable.json
|-- terraform/
|   `-- main.tf
|-- .github/
|   `-- workflows/
|       `-- ci.yml
|-- .flake8
|-- .dockerignore
|-- .gitignore
|-- Dockerfile
|-- Dockerfile.proxy
|-- docker-compose.demo.yml
|-- Jenkinsfile
|-- pytest.ini
|-- README.md
`-- report.py
```

## Architecture

```text
Developer Push or Manual Trigger
        |
        v
GitHub Actions or Jenkins Pipeline
        |
        +--> Install dependencies
        +--> Lint with flake8
        +--> Test with pytest and coverage
        +--> Audit dependencies with pip-audit
        +--> Build app image
        +--> Build proxy image
        +--> Scan app image with Trivy
        +--> Generate SentinelCI report
        +--> Auto deploy multi-container stack
        +--> Upload artifacts
        |
        v
Docker Images: sentinelci-app + sentinelci-proxy
Tags: v1 / v2 / latest
        |
        v
Ansible or Docker Compose Deployment
        |
        v
FastAPI service behind Nginx proxy on port 8080
        |
        v
Terraform infrastructure summary
```

## Demo Profiles

- `app/requirements.txt`: safe profile for PASS screenshots.
- `app/requirements-vulnerable.txt`: vulnerable profile for FAIL screenshots.
- `demo/trivy-safe.json`: sample PASS report input for `report.py`.
- `demo/trivy-vulnerable.json`: sample FAIL report input for `report.py`.

## Tools And Why They Are Included

- `FastAPI`: simple application layer for demonstrating deployment and testing.
- `GitHub Actions`: primary CI/CD workflow for screenshots and artifact capture.
- `Jenkins`: enterprise-style pipeline view with stage visualization.
- `Docker`: image build and tagging for versioned deployment demos.
- `Nginx`: reverse proxy container to make the stack look like a realistic multi-container deployment.
- `pip-audit`: dependency vulnerability auditing.
- `Trivy`: container image vulnerability scanning.
- `report.py`: readable PASS or FAIL report with score and recommendations.
- `Ansible`: deployment automation to a Docker host.
- `Terraform`: infrastructure-as-code validation and planning.
- `flake8`: linting for presentation-friendly code quality checks.
- `pytest` and `pytest-cov`: testing and coverage evidence.

## How To Run And Check Every Tool

### 0. Repo-Local Jenkins And Ansible Install

This repository now includes repo-local tool installers and launchers:

- `scripts/install-tools.ps1`: downloads Jenkins into `tools/jenkins` and builds the local Ansible runner image
- `scripts/run-jenkins.ps1`: starts Jenkins from the repo
- `scripts/run-ansible.ps1`: runs `ansible-playbook` from the repo-local Docker image

Install the local tools:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\install-tools.ps1
```

Start Jenkins locally:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run-jenkins.ps1
```

Run Ansible locally:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run-ansible.ps1
```

Notes:

- Jenkins is stored at `tools/jenkins/jenkins.war`.
- Jenkins data is stored at `tools/jenkins/home`.
- Ansible is provided by the Docker image `sentinelci-ansible:local`.
- Jenkins is started with the Java future-support flag because this machine uses Java 26.

### 1. FastAPI App

Install dependencies:

```bash
python -m pip install -r app/requirements.txt
```

Run the API:

```bash
uvicorn app.main:app --reload
```

Check in browser or terminal:

```bash
curl http://127.0.0.1:8000/
curl http://127.0.0.1:8000/health
```

### 2. flake8 Linting

Run lint checks:

```bash
python -m flake8 --jobs=1 app report.py
```

Expected result:

- No output means lint passed.

### 3. pytest And Coverage

Run tests with coverage:

```bash
python -m pytest --cov=app --cov-report=term-missing --cov-report=xml app
```

Expected result:

- Tests pass.
- Coverage summary appears in terminal.
- `coverage.xml` is generated for CI artifacts.

### 4. pip-audit

Safe run:

```bash
python -m pip_audit -r app/requirements.txt --format json
```

Vulnerable run:

```bash
python -m pip_audit -r app/requirements-vulnerable.txt --format json
```

Expected result:

- Safe profile shows no known vulnerabilities.
- Vulnerable profile reports known issues, which is useful for FAIL screenshots.

### 5. Docker

Build the safe image:

```bash
docker build --build-arg REQUIREMENTS_FILE=requirements.txt -t sentinelci-app:v1 -t sentinelci-app:latest .
docker build -f Dockerfile.proxy -t sentinelci-proxy:v1 -t sentinelci-proxy:latest .
```

Build the vulnerable image:

```bash
docker build --build-arg REQUIREMENTS_FILE=requirements-vulnerable.txt -t sentinelci-app:v2 .
docker build -f Dockerfile.proxy -t sentinelci-proxy:v2 .
```

Check tags:

```bash
docker image ls | grep sentinelci
```

Run the multi-container safe stack:

```bash
docker compose -f docker-compose.demo.yml up -d
docker compose -f docker-compose.demo.yml ps
```

Open in browser:

```text
http://127.0.0.1:8080
```

### 6. Trivy

Safe scan:

```bash
trivy image --format table --severity HIGH,CRITICAL --ignore-unfixed -o trivy-safe.txt sentinelci:v1
trivy image --format json --severity HIGH,CRITICAL --ignore-unfixed -o trivy-safe.json sentinelci-app:v1
```

Vulnerable scan:

```bash
trivy image --format table --severity HIGH,CRITICAL --ignore-unfixed -o trivy-fail.txt sentinelci-app:v2
trivy image --format json --severity HIGH,CRITICAL --ignore-unfixed -o trivy-fail.json sentinelci-app:v2
```

Expected result:

- Table output is easy to screenshot.
- JSON output feeds `report.py`.

### 7. report.py

Generate a PASS report from demo data:

```bash
python report.py --input demo/trivy-safe.json --output demo-safe-report.txt --label "DEMO SUCCESS"
```

Generate a FAIL report from demo data:

```bash
python report.py --input demo/trivy-vulnerable.json --output demo-failure-report.txt --label "DEMO FAILURE" --fail-on-vulns
```

Expected result:

- Report shows status, score, vulnerability summary, top findings, and recommendations.

### 8. GitHub Actions

The workflow supports:

- automatic runs on `push` and `pull_request`
- manual runs through `workflow_dispatch`
- manual selection of `safe` or `vulnerable` dependency profile
- manual `image_tag` selection such as `v1` or `v2`
- optional auto-deployment of a multi-container demo stack after a successful safe run

Manual demo run:

1. Open the repository on GitHub.
2. Go to `Actions`.
3. Open `SentinelCI Demo Pipeline`.
4. Click `Run workflow`.
5. Choose:
   - `safe` with tag `v1` for PASS
   - `vulnerable` with tag `v2` for FAIL
   - leave `auto_deploy = true` for the deployment screenshot

### 9. Jenkins

Jenkins job requirements:

- Git installed
- Docker installed on the agent
- Trivy installed on the agent
- Java available for local Jenkins runtime

If you want to use the repo-local Jenkins runtime instead of a preinstalled Jenkins server:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run-jenkins.ps1
```

Then open:

```text
http://localhost:8080
```

Run the pipeline:

1. Create a Pipeline job.
2. Point it to this repository.
3. Build with parameters:
   - `DEPENDENCY_PROFILE=safe` and `IMAGE_TAG=v1`
   - `DEPENDENCY_PROFILE=vulnerable` and `IMAGE_TAG=v2`
   - keep `AUTO_DEPLOY=true` for the safe build if you want the deploy-stage screenshot

Expected result:

- Stages are displayed clearly.
- PASS or FAIL can be captured from the Stage View and Console Output.

### 10. Ansible

Install the Docker collection:

```bash
ansible-galaxy collection install community.docker
```

If you want to use the repo-local Ansible install on Windows, use the included Docker runner instead of a native control-node install:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run-ansible.ps1
```

Syntax check:

```bash
ansible-playbook --syntax-check -i inventory.ini ansible/deploy.yml
```

Repo-local Docker runner syntax check:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run-ansible.ps1 -ExtraArgs "--syntax-check"
```

Run deployment:

```bash
ansible-playbook -i inventory.ini ansible/deploy.yml
```

Run the repo-local Ansible deployment:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run-ansible.ps1
```

### 11. Terraform

Initialize:

```bash
terraform -chdir=terraform init
```

Validate:

```bash
terraform -chdir=terraform validate
```

Plan:

```bash
terraform -chdir=terraform plan
```

## PASS And FAIL Commands For Demo

### PASS Demo

```bash
python -m pip_audit -r app/requirements.txt --format json
docker build --build-arg REQUIREMENTS_FILE=requirements.txt -t sentinelci:v1 -t sentinelci:latest .
docker build -f Dockerfile.proxy -t sentinelci-proxy:v1 -t sentinelci-proxy:latest .
trivy image --format json --severity HIGH,CRITICAL --ignore-unfixed -o trivy-safe.json sentinelci-app:v1
python report.py --input trivy-safe.json --output final-report-pass.txt --label "DEMO SUCCESS"
docker compose -f docker-compose.demo.yml up -d
```

### FAIL Demo

```bash
python -m pip_audit -r app/requirements-vulnerable.txt --format json
docker build --build-arg REQUIREMENTS_FILE=requirements-vulnerable.txt -t sentinelci-app:v2 .
docker build -f Dockerfile.proxy -t sentinelci-proxy:v2 .
trivy image --format json --severity HIGH,CRITICAL --ignore-unfixed -o trivy-fail.json sentinelci-app:v2
python report.py --input trivy-fail.json --output final-report-fail.txt --label "DEMO FAILURE" --fail-on-vulns
```

## GitHub Actions Workflow Summary

Stage names are intentionally screenshot-friendly:

1. `Stage 1 - Checkout Source`
2. `Stage 2 - Select Dependency Profile`
3. `Stage 3 - Set Up Python`
4. `Stage 4 - Install Dependencies`
5. `Stage 5 - Lint Application`
6. `Stage 6 - Run Test Suite With Coverage`
7. `Stage 7 - Audit Python Dependencies`
8. `Stage 8 - Build Application Image`
9. `Stage 9 - Build Proxy Image`
10. `Stage 10 - Trivy Scan App Image (Table)`
11. `Stage 11 - Trivy Scan App Image (JSON)`
12. `Stage 12 - Display Trivy Findings`
13. `Stage 13 - Generate SentinelCI Security Report`
14. `Stage 14 - Auto Deploy Demo Stack`
15. `Stage 15 - Upload Demo Artifacts`

## Screenshot Guide

### 1. GitHub Actions Screenshots

For PASS screenshot:

1. Open `Actions`.
2. Open `SentinelCI Demo Pipeline`.
3. Run workflow with:
   - `dependency_profile = safe`
   - `image_tag = v1`
4. Capture:
   - workflow run summary showing green status
   - left-side list of stages
   - `Stage 9 - Build Proxy Image`
   - `Stage 12 - Display Trivy Findings`
   - `Stage 13 - Generate SentinelCI Security Report`
   - `Stage 14 - Auto Deploy Demo Stack`
   - artifacts section at the bottom

For FAIL screenshot:

1. Run workflow again with:
   - `dependency_profile = vulnerable`
   - `image_tag = v2`
2. Capture:
   - workflow run summary showing red status
   - failing `Stage 12 - Generate SentinelCI Security Report`
   - `Stage 7 - Audit Python Dependencies` findings
   - `Stage 12 - Display Trivy Findings`

### 2. Jenkins Screenshots

Exact steps to open Jenkins for screenshots:

1. Run:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run-jenkins.ps1
```

2. Open your browser and go to:

```text
http://localhost:8080
```

3. Unlock Jenkins if prompted, then create or open your pipeline job.
4. Click the job name from the Jenkins dashboard.
5. For the best screenshots, open:
   - `Dashboard` for the Jenkins home page
   - the pipeline job page for build history
   - a build number for build details
   - `Console Output` for readable logs
   - `Pipeline Steps` or `Stage View` if available for the stage screenshot
6. Capture:
   - PASS build with the deploy stage visible
   - FAIL build with the red report stage visible
   - Console Output around image builds, Trivy scan, and deployment

### 3. Ansible Screenshots

Ansible does not have a built-in web tab like Jenkins unless you install AWX or Ansible Tower. For this project, the clean screenshot views are:

1. Open Windows Terminal or PowerShell in the repo.
2. Run:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run-ansible.ps1 -ExtraArgs "--syntax-check"
```

3. Capture the terminal showing the playbook path and syntax-check result.
4. Then run the actual deployment:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run-ansible.ps1
```

5. Capture the terminal showing:
   - `Create SentinelCI Docker network`
   - `Pull latest SentinelCI app image`
   - `Pull latest SentinelCI proxy image`
   - `Run SentinelCI API container`
   - `Run SentinelCI proxy container`

### 4. Docker Screenshots

1. Run:

```bash
docker image ls | grep sentinelci
```

2. Capture the terminal showing:
   - `sentinelci-app:v1`
   - `sentinelci-app:v2`
   - `sentinelci-app:latest`
   - `sentinelci-proxy:v1`
   - `sentinelci-proxy:v2`
   - `sentinelci-proxy:latest`

3. Run:

```bash
docker compose -f docker-compose.demo.yml ps
```

4. Capture the terminal showing both running containers:
   - `sentinelci-app`
   - `sentinelci-proxy`

If using Docker Hub:

1. Push the tags.
2. Open the repository tags page.
3. Capture the app repository tags page.
4. Capture the proxy repository tags page.

### 5. Optional Terminal Screenshots

Good terminal captures:

- `pytest` passing with coverage summary
- `pip-audit` vulnerable output
- `trivy` table output
- `python report.py` PASS output
- `python report.py` FAIL output
- `docker compose -f docker-compose.demo.yml ps`
- `terraform validate`
- `ansible-playbook --syntax-check`

## Demo Notes

- The vulnerable profile is intentionally kept separate so the default app stays clean and presentable.
- The pipelines keep going after `pip-audit` finds issues so the Docker, Trivy, and report screenshots are still generated.
- The final PASS or FAIL gate is `report.py`, which keeps the demo visually consistent across GitHub Actions and Jenkins.
- The safe pipeline now auto-deploys a two-container stack for stronger deployment screenshots.

## Future Scope

- Push images automatically to Docker Hub or GitHub Container Registry.
- Add a Jenkins Stage View plugin screenshot section to the docs.
- Add Semgrep or SonarQube for extra static analysis.
- Add Kubernetes deployment manifests for an extended demo.
