pipeline{
    agent any

    environment {
        Vercel_Token = credentials('vercel_token')
    }

    stages {
        stage('Install'){
            steps {
                bat 'npm install'
            }
        }
        stage('Test'){
            steps {
                echo 'Skipping test - no test script found'
            }
        }
        stage('Build'){
            steps {
                bat 'npm run build'
            }
        }
        stage('Deploy'){
            steps {
                bat 'npx vercel --prod --yes --token = %Vercel_Token%'
            }
        }
    }
}