# SentinelCI

[![CI Pipeline](https://github.com/NR0498/sentinelci/actions/workflows/ci.yml/badge.svg)](https://github.com/NR0498/sentinelci/actions/workflows/ci.yml)

SentinelCI is a demo-ready DevSecOps project that combines application delivery, security scanning, Docker packaging, Jenkins automation, Ansible deployment, and Terraform Infrastructure as Code in one repository. The project is prepared for both successful and failing screenshot flows.

It also includes a deployable dashboard and a real local AWS-compatible
integration:

- multipart evidence uploads are stored in LocalStack S3
- every successful upload publishes an SNS event
- SNS delivery is verified through a subscribed SQS queue
- no AWS account or cloud credentials are required

## Quick Start: Dashboard + LocalStack

Start the complete stack:

```powershell
docker compose -f docker-compose.demo.yml up -d --build
```

Open:

```text
http://127.0.0.1:8080/dashboard
http://127.0.0.1:8080/docs
```

Run the automated S3/SNS proof:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\verify-localstack.ps1
```

The proof performs a real upload, checks that the object is returned by S3,
and confirms that the matching SNS message reached the SQS verification queue.
See [`proof/README.md`](proof/README.md) for captured evidence.

### Testing dynamic scores

The dashboard analyzes the newest uploaded text or JSON report. Use:

- `proof/test-artifacts/sample-security-report.txt` for PASS and score 100
- `proof/test-artifacts/sample-failing-report.txt` for FAIL, score 72, and a
  blocked security pipeline
- `proof/test-artifacts/sample-scan-result.json` for a structured JSON PASS

Trivy JSON reports are also supported. Images and unrecognized documents show
`REVIEW` and `N/A` rather than being treated as a security pass.

## Vercel Dashboard

The dashboard is dependency-free static HTML, CSS, and JavaScript in
`app/dashboard`, so it can be deployed independently:

```powershell
npx vercel --cwd app/dashboard
```

The hosted dashboard is a portable visualization. Live S3/SNS actions require
the local FastAPI + LocalStack stack because LocalStack is intentionally not a
cloud service. When the dashboard is served by FastAPI locally, the API
endpoint is selected automatically.

Current production deployment:
https://dashboard-sooty-six-33.vercel.app

## Final Project Structure

```text
sentinelci/
|-- .github/
|   `-- workflows/
|       `-- ci.yml
|-- ansible/
|   |-- deploy.yml
|   `-- inventory.ini.example
|-- app/
|   |-- __init__.py
|   |-- aws_service.py
|   |-- dashboard/
|   |   |-- app.js
|   |   |-- index.html
|   |   |-- styles.css
|   |   `-- vercel.json
|   |-- main.py
|   |-- requirements.txt
|   |-- requirements-vulnerable.txt
|   `-- test_main.py
|-- demo/
|   |-- trivy-safe.json
|   `-- trivy-vulnerable.json
|-- deploy/
|   `-- nginx/
|       `-- default.conf
|-- scripts/
|   |-- install-tools.ps1
|   |-- run-ansible.ps1
|   `-- run-jenkins.ps1
|   `-- verify-localstack.ps1
|-- localstack/
|   `-- init-aws.sh
|-- proof/
|   |-- README.md
|   `-- screenshots/
|-- terraform/
|   |-- main.tf
|   |-- variables.tf
|   |-- outputs.tf
|   `-- README.md
|-- tools/
|   |-- ansible/
|   |   `-- Dockerfile
|   |-- jenkins/
|   |   `-- jenkins.war
|   `-- README.md
|-- .dockerignore
|-- .flake8
|-- .gitignore
|-- docker-compose.demo.yml
|-- Dockerfile
|-- Dockerfile.proxy
|-- Jenkinsfile
|-- pytest.ini
|-- README.md
`-- report.py
```

## What Each DevOps Tool Does

- `FastAPI`: provides the application being built, tested, and deployed.
- `Docker`: packages the FastAPI app and an Nginx proxy into demo-ready container images.
- `GitHub Actions`: runs linting, tests, dependency audit, image build, Trivy scan, report generation, and artifact upload.
- `Jenkins`: mirrors the same CI/CD flow with screenshot-friendly stages for enterprise-style demos.
- `pip-audit`: scans Python dependencies for known vulnerabilities.
- `Trivy`: scans the built application image for high and critical vulnerabilities.
- `report.py`: converts Trivy JSON into a readable PASS or FAIL security report with score and recommendations.
- `Ansible`: deploys the app and proxy containers to a Docker host and verifies container status.
- `Terraform`: demonstrates Infrastructure as Code using safe local simulated infrastructure outputs.
- `Docker Compose`: starts the local multi-container demo stack for screenshots.

## SAFE And VULNERABLE Demo Profiles

- `app/requirements.txt`: clean SAFE profile for PASS screenshots.
- `app/requirements-vulnerable.txt`: intentionally vulnerable profile for FAIL screenshots.

## Step 0: Install Repo-Local Jenkins And Ansible

Install the local tooling once:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\install-tools.ps1
```

This installs:

- Jenkins runtime in `tools/jenkins/jenkins.war`
- Jenkins home in `tools/jenkins/home`
- repo-local Ansible runner image `sentinelci-ansible:local`

## Step 1: Validate The Python Application

Install SAFE dependencies:

```powershell
.\.venv\Scripts\python -m pip install -r app\requirements.txt
```

Run lint:

```powershell
.\.venv\Scripts\python -m flake8 --jobs=1 app report.py
```

Run tests with coverage:

```powershell
.\.venv\Scripts\python -m pytest --cov=app --cov-report=term-missing --cov-report=xml app
```

Run the FastAPI app:

```powershell
.\.venv\Scripts\python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Open:

```text
http://127.0.0.1:8000
http://127.0.0.1:8000/health
```

## Step 2: Docker Build And Multi-Container Demo

Build SAFE images:

```powershell
docker build --build-arg REQUIREMENTS_FILE=requirements.txt -t sentinelci-app:v1 -t sentinelci-app:latest -t sentinelci-app:sha-local .
docker build -f Dockerfile.proxy -t sentinelci-proxy:v1 -t sentinelci-proxy:latest -t sentinelci-proxy:sha-local .
```

Build VULNERABLE images:

```powershell
docker build --build-arg REQUIREMENTS_FILE=requirements-vulnerable.txt -t sentinelci-app:v2 .
docker build -f Dockerfile.proxy -t sentinelci-proxy:v2 .
```

Show all tags:

```powershell
docker image ls
```

Start the SAFE multi-container stack:

```powershell
docker compose -f docker-compose.demo.yml up -d
docker compose -f docker-compose.demo.yml ps
```

Open the proxied app:

```text
http://127.0.0.1:8080
```

Stop the stack when finished:

```powershell
docker compose -f docker-compose.demo.yml down
```

## Step 3: Dependency Audit And Container Scan

SAFE dependency audit:

```powershell
.\.venv\Scripts\python -m pip_audit -r app\requirements.txt --cache-dir .pip-audit-cache --format json
```

VULNERABLE dependency audit:

```powershell
.\.venv\Scripts\python -m pip_audit -r app\requirements-vulnerable.txt --cache-dir .pip-audit-cache --format json
```

SAFE Trivy scan:

```powershell
trivy image --format table --severity HIGH,CRITICAL --ignore-unfixed -o trivy-safe.txt sentinelci-app:v1
trivy image --format json --severity HIGH,CRITICAL --ignore-unfixed -o trivy-safe.json sentinelci-app:v1
```

VULNERABLE Trivy scan:

```powershell
trivy image --format table --severity HIGH,CRITICAL --ignore-unfixed -o trivy-fail.txt sentinelci-app:v2
trivy image --format json --severity HIGH,CRITICAL --ignore-unfixed -o trivy-fail.json sentinelci-app:v2
```

## Step 4: Generate PASS And FAIL Reports

Generate PASS report:

```powershell
.\.venv\Scripts\python report.py --input demo\trivy-safe.json --output final-report-pass.txt --label "DEMO SUCCESS"
```

Generate FAIL report:

```powershell
.\.venv\Scripts\python report.py --input demo\trivy-vulnerable.json --output final-report-fail.txt --label "DEMO FAILURE" --fail-on-vulns
```

## Step 5: Terraform Demo

Go to the Terraform directory:

```powershell
Set-Location terraform
```

Run init:

```powershell
terraform init
```

Run validate:

```powershell
terraform validate
```

Run plan:

```powershell
terraform plan
```

Run apply:

```powershell
terraform apply -auto-approve
```

Show outputs:

```powershell
terraform output
```

Return to repo root:

```powershell
Set-Location ..
```

Useful Terraform outputs for screenshots:

- `project_name`
- `environment`
- `provisioned_status`
- `docker_image_name`
- `proxy_image_name`
- `deployment_target`
- `network_name`
- `service_summary`

## Step 6: Run GitHub Actions

The GitHub Actions workflow:

- runs linting
- runs tests
- runs pip-audit
- builds the application image
- builds the proxy image
- runs Trivy scan
- generates the final report
- optionally auto-deploys the SAFE demo stack
- uploads report artifacts

Manual SAFE run:

1. Open GitHub repository.
2. Click `Actions`.
3. Open `SentinelCI Demo Pipeline`.
4. Click `Run workflow`.
5. Choose:
   - `dependency_profile = safe`
   - `image_tag = v1`
   - `auto_deploy = true`
6. Click `Run workflow`.

Manual FAIL run:

1. Click `Run workflow` again.
2. Choose:
   - `dependency_profile = vulnerable`
   - `image_tag = v2`
   - `auto_deploy = false`
3. Click `Run workflow`.

## Step 7: Run Jenkins

Start Jenkins locally:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run-jenkins.ps1
```

Open:

```text
http://localhost:8080
```

If Jenkins asks for the unlock password:

```powershell
Get-Content tools\jenkins\home\secrets\initialAdminPassword
```

Create the pipeline job:

1. Click `New Item`
2. Name it `sentinelci-demo`
3. Select `Pipeline`
4. Click `OK`
5. In `General`:
   - check `Do not allow concurrent builds`
6. In `Pipeline`:
   - `Definition = Pipeline script from SCM`
   - `SCM = Git`
   - `Repository URL = https://github.com/NR0498/sentinelci.git`
   - `Branch Specifier = */main`
   - `Script Path = Jenkinsfile`
7. Click `Save`

Run SAFE build:

1. Click `Build with Parameters`
2. Set:
   - `DEPENDENCY_PROFILE = safe`
   - `IMAGE_TAG = v1`
   - `AUTO_DEPLOY = true`
3. Click `Build`

Run FAIL build:

1. Click `Build with Parameters`
2. Set:
   - `DEPENDENCY_PROFILE = vulnerable`
   - `IMAGE_TAG = v2`
   - `AUTO_DEPLOY = false`
3. Click `Build`

## Step 8: Run Ansible

Repo-local syntax check:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run-ansible.ps1 -SyntaxCheck
```

Repo-local deploy:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run-ansible.ps1
```

Native Ansible deploy if you already have Ansible installed:

```bash
ansible-playbook -i ansible/inventory.ini.example ansible/deploy.yml
```

The playbook will:

- pull the latest app image
- pull the latest proxy image
- stop old containers
- create the Docker network
- run the new app container
- run the new proxy container
- verify and print container status

Note:

- The repo-local Ansible runner is best used to demonstrate the packaged control-node workflow.
- For a real deployment run, point `ansible/inventory.ini.example` at a reachable Linux Docker host.

## Step 9: Docker Hub Tagging For Screenshots

Log in:

```powershell
docker login
```

Tag the SAFE images for Docker Hub:

```powershell
docker tag sentinelci-app:v1 <dockerhub-user>/sentinelci-app:v1
docker tag sentinelci-app:latest <dockerhub-user>/sentinelci-app:latest
docker tag sentinelci-app:sha-local <dockerhub-user>/sentinelci-app:sha-local
docker tag sentinelci-proxy:v1 <dockerhub-user>/sentinelci-proxy:v1
docker tag sentinelci-proxy:latest <dockerhub-user>/sentinelci-proxy:latest
docker tag sentinelci-proxy:sha-local <dockerhub-user>/sentinelci-proxy:sha-local
```

Tag the VULNERABLE images:

```powershell
docker tag sentinelci-app:v2 <dockerhub-user>/sentinelci-app:v2
docker tag sentinelci-proxy:v2 <dockerhub-user>/sentinelci-proxy:v2
```

Push the images:

```powershell
docker push <dockerhub-user>/sentinelci-app:v1
docker push <dockerhub-user>/sentinelci-app:v2
docker push <dockerhub-user>/sentinelci-app:latest
docker push <dockerhub-user>/sentinelci-app:sha-local
docker push <dockerhub-user>/sentinelci-proxy:v1
docker push <dockerhub-user>/sentinelci-proxy:v2
docker push <dockerhub-user>/sentinelci-proxy:latest
docker push <dockerhub-user>/sentinelci-proxy:sha-local
```

## Screenshot Checklist

### GitHub Actions Successful Run

Capture:

1. `Actions` page showing `SentinelCI Demo Pipeline`
2. SAFE run summary with green status
3. `Stage 9 - Build Proxy Image`
4. `Stage 12 - Display Trivy Findings`
5. `Stage 13 - Generate SentinelCI Security Report`
6. `Stage 14 - Auto Deploy Demo Stack`

### GitHub Actions Failed Security Run

Capture:

1. FAIL run summary with red status
2. `Stage 7 - Audit Python Dependencies`
3. `Stage 12 - Display Trivy Findings`
4. `Stage 13 - Generate SentinelCI Security Report` showing failure

### Security Report Artifact

Capture:

1. Artifact section at the bottom of the GitHub Actions run
2. Downloaded `final-report.txt` opened in editor or terminal

### Jenkins Dashboard

Capture:

1. Jenkins dashboard with the `sentinelci-demo` job
2. Job page with build history

### Jenkins Console Output

Capture:

1. PASS build `Console Output`
2. FAIL build `Console Output`
3. Focus on:
   - dependency audit
   - image builds
   - Trivy scan
   - report generation
   - auto deploy stage

### Docker Hub Repository Page

Capture:

1. `sentinelci-app` repository tags
2. `sentinelci-proxy` repository tags
3. Make sure tags like `latest`, `v1`, `v2`, and SHA-tag are visible

### Docker Desktop Or Container List

Capture:

1. `docker image ls`
2. `docker compose -f docker-compose.demo.yml ps`
3. Show both:
   - `sentinelci-app`
   - `sentinelci-proxy`

### Terraform

Capture:

1. `terraform init` success
2. `terraform validate` success
3. `terraform plan` output
4. `terraform apply` output
5. `terraform output`

### Ansible

Capture:

1. syntax check output
2. deployment run output
3. status verification lines for both containers

## Short SAFE And FAIL Command Sets

### SAFE

```powershell
.\.venv\Scripts\python -m flake8 --jobs=1 app report.py
.\.venv\Scripts\python -m pytest --cov=app --cov-report=term-missing app
.\.venv\Scripts\python -m pip_audit -r app\requirements.txt --cache-dir .pip-audit-cache --format json
docker build --build-arg REQUIREMENTS_FILE=requirements.txt -t sentinelci-app:v1 -t sentinelci-app:latest -t sentinelci-app:sha-local .
docker build -f Dockerfile.proxy -t sentinelci-proxy:v1 -t sentinelci-proxy:latest -t sentinelci-proxy:sha-local .
docker compose -f docker-compose.demo.yml up -d
.\.venv\Scripts\python report.py --input demo\trivy-safe.json --output final-report-pass.txt --label "DEMO SUCCESS"
```

### VULNERABLE

```powershell
.\.venv\Scripts\python -m pip_audit -r app\requirements-vulnerable.txt --cache-dir .pip-audit-cache --format json
docker build --build-arg REQUIREMENTS_FILE=requirements-vulnerable.txt -t sentinelci-app:v2 .
docker build -f Dockerfile.proxy -t sentinelci-proxy:v2 .
.\.venv\Scripts\python report.py --input demo\trivy-vulnerable.json --output final-report-fail.txt --label "DEMO FAILURE" --fail-on-vulns
```
