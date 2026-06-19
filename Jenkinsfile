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
                    if (params.DEPENDENCY_PROFILE == 'vulnerable') {
                        env.REQUIREMENTS_FILE = 'app/requirements-vulnerable.txt'
                        env.REQUIREMENTS_NAME = 'requirements-vulnerable.txt'
                        env.REPORT_LABEL = 'DEMO FAILURE'
                    } else {
                        env.REQUIREMENTS_FILE = 'app/requirements.txt'
                        env.REQUIREMENTS_NAME = 'requirements.txt'
                        env.REPORT_LABEL = 'DEMO SUCCESS'
                    }

                    env.SHORT_SHA = isUnix()
                        ? sh(script: 'git rev-parse --short=7 HEAD', returnStdout: true).trim()
                        : bat(script: '@for /f %%i in (\'git rev-parse --short=7 HEAD\') do @echo %%i', returnStdout: true).trim()
                }
                echo "Selected dependency profile: ${params.DEPENDENCY_PROFILE}"
                echo "Docker image tags: ${params.IMAGE_TAG}, latest, sha-${env.SHORT_SHA}"
            }
        }

        stage('Stage 3 - Install Dependencies') {
            steps {
                echo 'Creating Python virtual environment and installing tools'
                script {
                    if (isUnix()) {
                        sh '''
                            rm -rf "${VENV_DIR}"
                            python3 -m venv "${VENV_DIR}"
                            . "${VENV_DIR}/bin/activate"
                            python -m pip install --upgrade pip setuptools wheel
                            python -m pip install -r "${REQUIREMENTS_FILE}" pip-audit
                        '''
                    } else {
                        bat '''
                            if exist "%VENV_DIR%" rmdir /s /q "%VENV_DIR%"
                            py -3 -m venv "%VENV_DIR%"
                            call "%VENV_DIR%\\Scripts\\activate"
                            python -m pip install --upgrade pip setuptools wheel
                            python -m pip install -r "%REQUIREMENTS_FILE%" pip-audit
                        '''
                    }
                }
            }
        }

        stage('Stage 4 - Lint Application') {
            steps {
                echo 'Running flake8 checks'
                script {
                    if (isUnix()) {
                        sh '''
                            . "${VENV_DIR}/bin/activate"
                            python -m flake8 --jobs=1 app report.py scripts/verify_localstack.py
                        '''
                    } else {
                        bat '''
                            call "%VENV_DIR%\\Scripts\\activate"
                            python -m flake8 --jobs=1 app report.py scripts/verify_localstack.py
                        '''
                    }
                }
            }
        }

        stage('Stage 5 - Run Test Suite') {
            steps {
                echo 'Executing pytest with coverage reporting'
                script {
                    if (isUnix()) {
                        sh '''
                            . "${VENV_DIR}/bin/activate"
                            python -m pytest --cov=app --cov-report=term-missing --cov-report=xml app
                        '''
                    } else {
                        bat '''
                            call "%VENV_DIR%\\Scripts\\activate"
                            python -m pytest --cov=app --cov-report=term-missing --cov-report=xml app
                        '''
                    }
                }
            }
        }

        stage('Stage 6 - Audit Dependencies') {
            steps {
                echo 'Auditing Python dependencies with pip-audit'
                script {
                    if (isUnix()) {
                        sh '''
                            . "${VENV_DIR}/bin/activate"
                            python -m pip_audit -r "${REQUIREMENTS_FILE}" --format json --output pip-audit-report.json || true
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
                    } else {
                        bat '''
                            call "%VENV_DIR%\\Scripts\\activate"
                            python -m pip_audit -r "%REQUIREMENTS_FILE%" --format json --output pip-audit-report.json
                            if errorlevel 1 echo pip-audit reported vulnerabilities and the pipeline will continue to the image scan.
                            python -c "import json, pathlib; report=json.loads(pathlib.Path('pip-audit-report.json').read_text()); findings=[(dep['name'], dep['version'], vuln['id']) for dep in report.get('dependencies', []) for vuln in dep.get('vulns', [])]; print('Dependency audit findings:' if findings else 'Dependency audit passed with no known vulnerabilities.'); [print(f'- {name} {version}: {vuln_id}') for name, version, vuln_id in findings[:10]]"
                            exit /b 0
                        '''
                    }
                }
            }
        }

        stage('Stage 7 - Build Application Image') {
            steps {
                echo 'Building SentinelCI application image'
                script {
                    if (isUnix()) {
                        sh '''
                            docker build \
                              --build-arg REQUIREMENTS_FILE="${REQUIREMENTS_NAME}" \
                              -t "${APP_IMAGE_NAME}:${IMAGE_TAG}" \
                              -t "${APP_IMAGE_NAME}:latest" \
                              -t "${APP_IMAGE_NAME}:sha-${SHORT_SHA}" \
                              .
                        '''
                    } else {
                        bat '''
                            docker build --build-arg REQUIREMENTS_FILE=%REQUIREMENTS_NAME% -t %APP_IMAGE_NAME%:%IMAGE_TAG% -t %APP_IMAGE_NAME%:latest -t %APP_IMAGE_NAME%:sha-%SHORT_SHA% .
                        '''
                    }
                }
            }
        }

        stage('Stage 8 - Build Proxy Image') {
            steps {
                echo 'Building SentinelCI reverse-proxy image'
                script {
                    if (isUnix()) {
                        sh '''
                            docker build \
                              -f Dockerfile.proxy \
                              -t "${PROXY_IMAGE_NAME}:${IMAGE_TAG}" \
                              -t "${PROXY_IMAGE_NAME}:latest" \
                              -t "${PROXY_IMAGE_NAME}:sha-${SHORT_SHA}" \
                              .
                            docker image ls | grep sentinelci
                        '''
                    } else {
                        bat '''
                            docker build -f Dockerfile.proxy -t %PROXY_IMAGE_NAME%:%IMAGE_TAG% -t %PROXY_IMAGE_NAME%:latest -t %PROXY_IMAGE_NAME%:sha-%SHORT_SHA% .
                            docker image ls
                        '''
                    }
                }
            }
        }

        stage('Stage 9 - Run Trivy Scan') {
            steps {
                echo 'Scanning application image with Trivy in table and JSON formats'
                script {
                    if (isUnix()) {
                        sh '''
                            trivy image --format table --severity HIGH,CRITICAL --ignore-unfixed -o trivy-report.txt "${APP_IMAGE_NAME}:${IMAGE_TAG}"
                            trivy image --format json --severity HIGH,CRITICAL --ignore-unfixed -o trivy-report.json "${APP_IMAGE_NAME}:${IMAGE_TAG}"
                            cat trivy-report.txt
                        '''
                    } else {
                        bat '''
                            trivy image --format table --severity HIGH,CRITICAL --ignore-unfixed -o trivy-report.txt %APP_IMAGE_NAME%:%IMAGE_TAG%
                            trivy image --format json --severity HIGH,CRITICAL --ignore-unfixed -o trivy-report.json %APP_IMAGE_NAME%:%IMAGE_TAG%
                            type trivy-report.txt
                        '''
                    }
                }
            }
        }

        stage('Stage 10 - Generate Security Report') {
            steps {
                echo 'Generating the SentinelCI formatted security report'
                script {
                    if (isUnix()) {
                        sh '''
                            . "${VENV_DIR}/bin/activate"
                            python report.py \
                              --input trivy-report.json \
                              --output final-report.txt \
                              --label "${REPORT_LABEL}" \
                              --fail-on-vulns
                        '''
                    } else {
                        bat '''
                            call "%VENV_DIR%\\Scripts\\activate"
                            python report.py --input trivy-report.json --output final-report.txt --label "%REPORT_LABEL%" --fail-on-vulns
                        '''
                    }
                }
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
                script {
                    if (isUnix()) {
                        sh '''
                            docker compose -f docker-compose.demo.yml up -d
                            docker compose -f docker-compose.demo.yml ps
                            . "${VENV_DIR}/bin/activate"
                            python scripts/verify_localstack.py
                        '''
                    } else {
                        bat '''
                            docker compose -f docker-compose.demo.yml up -d
                            docker compose -f docker-compose.demo.yml ps
                            powershell -ExecutionPolicy Bypass -File scripts\\verify-localstack.ps1
                        '''
                    }
                }
            }
        }
    }

    post {
        always {
            archiveArtifacts artifacts: 'final-report.txt,trivy-report.txt,trivy-report.json,pip-audit-report.json,coverage.xml', allowEmptyArchive: true
        }
    }
}
