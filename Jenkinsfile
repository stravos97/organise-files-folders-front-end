pipeline {
  agent none

  options {
    timeout(time: 1, unit: 'HOURS')
    disableConcurrentBuilds()
    buildDiscarder(logRotator(numToKeepStr: '10'))
  }

  stages {
    stage('Test') { // Renamed stage
      agent {
        label 'linux-builder' // Updated label
      }
      steps {
            sh '''
              python -m venv venv
              . venv/bin/activate
              pip install -e .
              pip install pytest pytest-cov pytest-mock
              pytest tests/ --junitxml=test-results-linux.xml --cov=organize_gui --cov-report xml:coverage-linux.xml
            '''
          }
          post {
            always {
              junit 'test-results-linux.xml'
              recordCoverage(tools: [[parser: 'COBERTURA', pattern: 'coverage-linux.xml']])
            }
    } // End Test stage

    stage('Build Executable') { // Renamed stage
      agent {
        label 'linux-builder' // Updated label
      }
      steps {
            sh '''
              # Activate venv created in test stage (or recreate if necessary)
              if [ ! -d "venv" ]; then
                python -m venv venv
              fi
              . venv/bin/activate
              pip install pyinstaller
              # Run pyinstaller from project root
              pyinstaller --onefile --windowed --name organize-gui organize_gui/app.py
            '''
            // Archive from the default dist directory created in the workspace root
            archiveArtifacts artifacts: 'dist/organize-gui', fingerprint: true
    } // End Build Executable stage

    stage('Python Package') {
      agent {
        label 'linux-builder' // Updated label
      }
      steps {
        sh '''
          # Activate venv created in test stage (or recreate if necessary)
          if [ ! -d "venv" ]; then
            python -m venv venv
          fi
          . venv/bin/activate
          pip install wheel twine
          python setup.py sdist bdist_wheel
        '''
        // Archive from the default dist directory created in the workspace root
        archiveArtifacts artifacts: 'dist/*.whl,dist/*.tar.gz', fingerprint: true
      }
    }
  }

  post {
    success {
      // Slack notification removed
      echo "Build successful: ${env.JOB_NAME} #${env.BUILD_NUMBER}"
    }
    failure {
      // Slack notification removed
      echo "Build failed: ${env.JOB_NAME} #${env.BUILD_NUMBER}"
    }
    always {
      cleanWs() // Clean up workspace
    }
  }
}
