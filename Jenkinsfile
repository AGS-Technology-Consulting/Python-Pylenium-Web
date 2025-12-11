pipeline {
    agent any

    environment {
        PYTHON_VERSION = "3.10"
        VENV = ".venv"
        ALLURE_RESULTS = "reports/allure-results"
    }

    stages {
        stage('Checkout Code') {
            steps {
                checkout scm
            }
        }

        stage('Setup Python Environment') {
            steps {
                sh """
                    python3 -m venv ${VENV}
                    source ${VENV}/bin/activate
                    pip3 install --upgrade pip
                    pip3 install -r requirements.txt
                """
            }
        }

        stage('Run Tests') {
            steps {
                sh """
                    source ${VENV}/bin/activate
                    mkdir -p ${ALLURE_RESULTS}
                    pytest --alluredir=${ALLURE_RESULTS} -v
                """
            }
        }

        stage('Publish Allure Report') {
            steps {
                allure([
                    includeProperties: false,
                    jdk: '',
                    properties: [],
                    reportBuildPolicy: 'ALWAYS',
                    results: [[path: "${ALLURE_RESULTS}"]]
                ])
            }
        }
    }

    post {
        always {
            echo "Cleaning workspace…"
            cleanWs()
        }
    }
}
