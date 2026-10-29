
pipeline {
    agent any

    environment {
        PATH = "/Applications/Docker.app/Contents/Resources/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
    }

    stages {
        stage('Check Docker') {
            steps {
                sh 'which docker'
                sh 'docker --version'
            }
        }

        stage('Build') {
            steps {
                echo "Build Airway Docker Image"
                sh 'docker build -t airway-app .'
            }
        }

        stage('Run') {
            steps {
                echo "Run Airway Application in Docker Container"
                sh 'docker rm -f airway-jenkins-test || true'
                sh 'docker run -d -p 5006:5005 --name airway-jenkins-test airway-app'
            }
        }
    }

    post {
        success {
            echo 'Airway pipeline completed successfully!'
        }

        failure {
            echo 'Airway pipeline failed. Please check the logs.'
        }
    }
}
