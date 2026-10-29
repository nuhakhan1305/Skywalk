pipeline {
    agent any

    stages {

        stage('Checkout') {
            steps {
                echo "Cloning Airway repository..."
                checkout scm
            }
        }

        stage('Test') {
            steps {
                echo "Checking Airway Python application"
                sh 'python3 -m py_compile app.py'
            }
        }

        stage('Run') {
            steps {
                echo "Checking Airway application code"
                sh 'python3 -c "import ast; ast.parse(open(\'app.py\').read()); print(\'Airway application code is valid\')"'
            }
        }

        stage('Package') {
            steps {
                echo "Packaging Airway project"
                sh 'tar -czf airway-project.tar.gz --exclude=.git --exclude=.venv .'
            }
        }

        stage('Archive') {
            steps {
                echo "Archiving Airway project"
                archiveArtifacts artifacts: 'airway-project.tar.gz'
            }
        }
    }

    post {
        success {
            echo 'Airway testing and packaging completed successfully!'
        }

        failure {
            echo 'Pipeline failed. Check Jenkins Console Output.'
        }
    }
}
