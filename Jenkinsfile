pipeline {
    agent any

    environment {
        PATH = "/Applications/Docker.app/Contents/Resources/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
        KUBECONFIG = '/Users/nuhakhan/.kube/config'
    }

    stages {
        stage('Build Docker Image') {
            steps {
                // Builds the image with your week9 tag
                sh 'docker build -t nuhakhan1305/airway-app:week9 .'
            }
        }

        stage('Docker Login') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'dockerhub-creds',
                    usernameVariable: 'DOCKER_USER',
                    passwordVariable: 'DOCKER_TOKEN'
                )]) {
                    sh 'echo "$DOCKER_TOKEN" | docker login -u "$DOCKER_USER" --password-stdin'
                }
            }
        }

        stage('Push Docker Image to Docker Hub') {
            steps {
                sh 'docker push nuhakhan1305/airway-app:week9'
            }
        }

        stage('Deploy to Kubernetes') {
            steps {
                // Note: I changed this to deplo.yaml to match your exact filename
                sh 'kubectl apply -f deplo.yaml'
                sh 'kubectl apply -f service.yaml'
            }
        }
    }

    post {
        success {
            echo 'Pipeline completed successfully!'
        }
        failure {
            echo 'Pipeline failed. Please check the logs.'
        }
    }
}