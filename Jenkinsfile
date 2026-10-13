
pipeline {

    agent any

    environment {
        PATH = "/Applications/Docker.app/Contents/Resources/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin"
        IMAGE_NAME = "airway-app"
        CONTAINER_NAME = "airway-jenkins-test"
        APP_PORT = "5006"
    }

    stages {

        stage('Checkout') {
            steps {
                echo "cloning repo...."

                git branch: 'feature-1',
                    url: 'https://github.com/nuhakhan1305/DevOps.git'
            }
        }

        stage('Combine') {
            steps {
                echo "building Docker image"

                sh 'docker build -t airway-app:latest ./Airway'
            }
        }

        stage('Test') {
            steps {
                echo "checking Python syntax"

                sh 'python3 -m py_compile Airway/app.py'

                echo "checking Docker image"

                sh 'docker image inspect airway-app:latest'
            }
        }

        stage('Run') {
            steps {
                echo "running Airway application container"

                sh '''
                    docker rm -f airway-jenkins-test || true

                    docker run -d \
                        --name airway-jenkins-test \
                        -p 5006:5005 \
                        airway-app:latest

                    sleep 5

                    curl --fail http://127.0.0.1:5006/health
                '''
            }
        }

        stage('Package Docker Image') {
            steps {
                echo "saving Docker image"

                sh '''
                    mkdir -p artifacts
                    docker save airway-app:latest -o artifacts/airway-app.tar
                '''
            }
        }

        stage('Archive Docker Image') {
            steps {
                echo "archiving Docker image artifact"

                archiveArtifacts artifacts: 'artifacts/airway-app.tar',
                    fingerprint: true
            }
        }
    }

    post {

        always {
            echo "cleaning up test container"

            sh 'docker rm -f airway-jenkins-test || true'
        }

        success {
            echo 'Airway Docker build, test, run and packaging successful!'
        }

        failure {
            echo 'Airway Docker pipeline failed. Check the Jenkins console output.'
        }
    }
}
