# Global COVID Data Tracker
### Project by: Samaye Lohan, Shubham Makharia, Yash Mehta, and Logan Heft
### Brown University

## Setup for starting this project on GitPod:
--- 
1. Fork this project into your own GitHub account
2. Start a GitPod container on your forked repository by pasting the following URL into your web-browser:

<center>gitpod.io/#/{url to your repo}</center>


For example, if your github username is lheft, the url would be as follows:

<center>http://gitpod.io/#/https://github.com/lheft/data1050-demo-project-f20</center>


If you connect to port 1050 you should see a page similar to this:
INSERT IMAGES BELOW




# Launching The App
---
1. Open the gitpod instance and run these commands to set persistent environment variables associated with your user for the current repository:

''gp env HOST="t-scholar-233105:us-central1:project1050"''
''gp env PORT="pg8000"''
''gp env DB_USER="postgres"''
''gp env DB_PASS="tempPassword123"''
''gp env DB_NAME="project"''
''gp env KEY="mOcbKU0Rvg9BCoOOv-a7mH0_XQjWCDN2Tt9uVP7_AFQ="''
''gp env GOOGLE_APPLICATION_CREDENTIALS="GAC.json"''

Now close the gitpod window and reopen it and create a new workspace since the commands do not modify your current terminal session, but rather persists the variables for the next workspace on this repository.

2. Run pip install -r requirements.txt to get the environment running.

3. Run python app.py

