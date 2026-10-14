// Lab-06: Containerized Build Stage Automation
// Student: Abdul Basit (FA22-BAI-001)
//
// Required Jenkins configuration (no values are hardcoded here):
//   - Job type: Pipeline from SCM, pointing at your GitHub repository.
//   - Environment variable DOCKER_IMAGE (job or global property), e.g.
//       <dockerhub-username>/linear-regression-lab06:latest
//   - "GitHub hook trigger for GITScm polling" enabled (GitHub plugin).

pipeline {
    agent any

    triggers {
        // Run on GitHub push webhook
        githubPush()
    }

    options {
        disableConcurrentBuilds()
        timeout(time: 15, unit: 'MINUTES')
    }

    stages {
        stage('Checkout') {
            steps {
                // Uses the repository configured in the Jenkins job (Pipeline script from SCM)
                checkout scm
            }
        }

        stage('Build') {
            steps {
                sh '''
                    set -eu

                    if [ -z "${DOCKER_IMAGE:-}" ]; then
                        echo "ERROR: DOCKER_IMAGE is not set in Jenkins." >&2
                        exit 1
                    fi
                    echo "Using image: ${DOCKER_IMAGE}"

                    docker compose version
                    docker compose pull
                    docker compose up -d --force-recreate

                    # Wait for the API to become healthy; fail the build otherwise
                    for i in $(seq 1 30); do
                        if curl -fsS http://localhost:5000/health; then
                            echo
                            echo "API is UP"
                            curl -fsS "http://localhost:5000/predict?x1=2&x2=3&x3=1"
                            echo
                            exit 0
                        fi
                        sleep 2
                    done

                    echo "ERROR: API did not become healthy" >&2
                    docker compose logs --tail=100 || true
                    exit 1
                '''
            }
        }
    }

    post {
        always {
            sh 'docker compose ps || true'
        }
        failure {
            echo 'Build stage failed: see the logs above.'
        }
    }
}
