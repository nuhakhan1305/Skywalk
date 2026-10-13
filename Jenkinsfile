
pipeline {
    agent any

    environment {
        PATH = "/Applications/Docker.app/Contents/Resources/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin"
        IMAGE_NAME = "skywalk-app"
        CONTAINER_NAME = "skywalk-jenkins-test"
        APP_PORT = "5006"
    }

    stages {
        stage('Checkout') {
            steps {
                echo "Skywalk repository checked out by Jenkins SCM."
            }
        }

        stage('Build Docker Image') {
            steps {
                echo "Building Skywalk Docker image"
                sh 'docker build -t skywalk-app:latest .'
            }
        }

        stage('Test') {
            steps {
                echo "Checking Python syntax"
                sh 'python3 -m py_compile app.py'

                echo "Checking Docker image"
                sh 'docker image inspect skywalk-app:latest'
            }
        }

        stage('Run and Verify') {
            steps {
                echo "Running Skywalk application container"
                sh '''
                    docker rm -f skywalk-jenkins-test || true

                    docker run -d \
                        --name skywalk-jenkins-test \
                        -p 5006:5005 \
                        skywalk-app:latest

                    sleep 5
                    curl --fail http://127.0.0.1:5006/health
                '''
            }
        }

        stage('Package Docker Image') {
            steps {
                echo "Saving Docker image"
                sh '''
                    mkdir -p artifacts
                    docker save skywalk-app:latest -o artifacts/skywalk-app.tar
                '''
            }
        }

        stage('Archive Docker Image') {
            steps {
                echo "Archiving Docker image"
                archiveArtifacts artifacts: 'artifacts/skywalk-app.tar',
                                 fingerprint: true
            }
        }
    }

    post {
        always {
            echo "Cleaning up Skywalk test container"
            sh 'docker rm -f skywalk-jenkins-test || true'
        }

        success {
            echo 'Skywalk Docker build, verification and packaging successful!'
        }

        failure {
            echo 'Skywalk pipeline failed. Check the Jenkins Console Output.'
        }
    }
}
