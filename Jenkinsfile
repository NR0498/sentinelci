pipeline {
    agent any

    options {
        timestamps()
        disableConcurrentBuilds()
    }

    parameters {
        choice(
            name: 'DEPENDENCY_PROFILE',
            choices: ['safe', 'vulnerable'],
            description: 'Use safe for PASS screenshots or vulnerable for FAIL screenshots.'
        )
        string(
            name: 'IMAGE_TAG',
            defaultValue: 'v1',
            description: 'Docker tag to display in Jenkins and Docker screenshots.'
        )
        booleanParam(
            name: 'AUTO_DEPLOY',
            defaultValue: true,
            description: 'Start the multi-container demo stack after a successful safe run.'
        )
    }

    environment {
        APP_IMAGE_NAME = 'sentinelci-app'
        PROXY_IMAGE_NAME = 'sentinelci-proxy'
        VENV_DIR = '.venv-jenkins'
    }

    stages {
        stage('Stage 1 - Checkout Source') {
            steps {
                echo 'Checking out SentinelCI source code'
                checkout scm
            }
        }

        stage('Stage 2 - Select Demo Profile') {
            steps {
                script {
                    env.REQUIREMENTS_FILE = params.DEPENDENCY_PROFILE == 'vulnerable' ?
                        'app/requirements-vulnerable.txt' :
                        'app/requirements.txt'
                    env.REPORT_LABEL = params.DEPENDENCY_PROFILE == 'vulnerable' ?
                        'DEMO FAILURE' :
                        'DEMO SUCCESS'
                }
                echo "Selected dependency profile: ${params.DEPENDENCY_PROFILE}"
                echo "Docker image tags: ${params.IMAGE_TAG}, latest"
            }
        }

        stage('Stage 3 - Install Python Dependencies') {
            steps {
                echo 'Creating Python virtual environment and installing tools'
                sh '''
                    python3 -m venv ${VENV_DIR}
                    . ${VENV_DIR}/bin/activate
                    python -m pip install --upgrade pip setuptools wheel
                    python -m pip install -r ${REQUIREMENTS_FILE} pip-audit
                '''
            }
        }

        stage('Stage 4 - Lint Application') {
            steps {
                echo 'Running flake8 checks'
                sh '''
                    . ${VENV_DIR}/bin/activate
                    flake8 --jobs=1 app report.py
                '''
            }
        }

        stage('Stage 5 - Run Test Suite') {
            steps {
                echo 'Executing pytest with coverage reporting'
                sh '''
                    . ${VENV_DIR}/bin/activate
                    pytest --cov=app --cov-report=term-missing --cov-report=xml app
                '''
            }
        }

        stage('Stage 6 - Audit Dependencies') {
            steps {
                echo 'Auditing Python dependencies with pip-audit'
                sh '''
                    . ${VENV_DIR}/bin/activate
                    pip-audit -r ${REQUIREMENTS_FILE} --format json --output pip-audit-report.json || true
                    python - <<'PY'
import json
from pathlib import Path
report = json.loads(Path("pip-audit-report.json").read_text())
findings = [
    (dep["name"], dep["version"], vuln["id"])
    for dep in report.get("dependencies", [])
    for vuln in dep.get("vulns", [])
]
if findings:
    print("Dependency audit findings:")
    for name, version, vuln_id in findings[:10]:
        print(f"- {name} {version}: {vuln_id}")
else:
    print("Dependency audit passed with no known vulnerabilities.")
PY
                '''
            }
        }

        stage('Stage 7 - Build Application Image') {
            steps {
                echo 'Building SentinelCI application image'
                sh '''
                    docker build \
                      --build-arg REQUIREMENTS_FILE=$(basename ${REQUIREMENTS_FILE}) \
                      -t ${APP_IMAGE_NAME}:${IMAGE_TAG} \
                      -t ${APP_IMAGE_NAME}:latest \
                      .
                '''
            }
        }

        stage('Stage 8 - Build Proxy Image') {
            steps {
                echo 'Building SentinelCI reverse-proxy image'
                sh '''
                    docker build \
                      -f Dockerfile.proxy \
                      -t ${PROXY_IMAGE_NAME}:${IMAGE_TAG} \
                      -t ${PROXY_IMAGE_NAME}:latest \
                      .
                    docker image ls | grep sentinelci
                '''
            }
        }

        stage('Stage 9 - Run Trivy Scan') {
            steps {
                echo 'Scanning application image with Trivy in table and JSON formats'
                sh '''
                    trivy image --format table --severity HIGH,CRITICAL --ignore-unfixed -o trivy-report.txt ${APP_IMAGE_NAME}:${IMAGE_TAG}
                    trivy image --format json --severity HIGH,CRITICAL --ignore-unfixed -o trivy-report.json ${APP_IMAGE_NAME}:${IMAGE_TAG}
                    cat trivy-report.txt
                '''
            }
        }

        stage('Stage 10 - Generate Security Report') {
            steps {
                echo 'Generating the SentinelCI formatted security report'
                sh '''
                    . ${VENV_DIR}/bin/activate
                    python report.py \
                      --input trivy-report.json \
                      --output final-report.txt \
                      --label "${REPORT_LABEL}" \
                      --fail-on-vulns
                '''
            }
        }

        stage('Stage 11 - Auto Deploy Demo Stack') {
            when {
                allOf {
                    expression { params.AUTO_DEPLOY }
                    expression { params.DEPENDENCY_PROFILE == 'safe' }
                }
            }
            steps {
                echo 'Starting the multi-container demo stack'
                sh '''
                    docker compose -f docker-compose.demo.yml up -d
                    docker compose -f docker-compose.demo.yml ps
                '''
            }
        }
    }

    post {
        always {
            archiveArtifacts artifacts: 'final-report.txt,trivy-report.txt,trivy-report.json,pip-audit-report.json,coverage.xml', allowEmptyArchive: true
        }
    }
}
