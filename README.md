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


This webapp runs through GCP. In order to run this from a local workspace or in GitPod, contact one of the contributors to this repo for Key_CREDENTIALS to access the database instance and run the dashboard.

Once key_CREDENTIALS has been secured, run the following command to launch the webapp.

export KEY="key_CREDENTIALS" && pip install -r requirements.txt && python app.py
