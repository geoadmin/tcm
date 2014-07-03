Welcome to Tile Cluster Manager (TCM)
==========================
TCM is a webfrontend to automate tasks on Amazon webservices (aws) to manage a tile cluster. It allows you to create an image from a instance and start a cluster from it.

Overview
========

Requirements
------------

- Python 2.7
- Flask
- boto

Features
---------------

- Create AMI from an instance
- Launch new cluster (Autoscaling group + ELB)
- Up/down scale cluster
- Graphs for CPU usage and processed requests/min

Installation
============
Install the dependencies. I would recommend to use a virtualenv.
```
$ pip install -r requirements.txt
```

Configuration
-------------
Use config.py.dist as a base for your own configuration
```
$ cp config.py.dist config.py
```
Add your AWS credentials

config.py:

    AWS_ACCESS_KEY_ID = 'your-access-key'
    AWS_SECERET_ACCESS_KEY = 'your-secret-access-key'

Start the application
```
$ python run.py 
 * Running on http://127.0.0.1:5000/
 * Restarting with reloader

```
Point your browser to http://127.0.0.1:5000/

Deployment
-------------
For a production deployment I would not recommend to use the integrated devserver. You can deploy the tcm to any wsgi runtime, for exmaple gunicorn.

```
$ gunicorn -b 10.0.0.2:8080 views:app
```

Turn off debug mode and set a random SECRET_KEY

config.py:

    DEBUG = False
    SECRET_KEY = '1234'


Authenication
-------------
Per default the creator of all resources is "Anonymous". You can easily setup authentication in front of TCM and pass the username using a HTTP header.

Example

Apache reverse proxy with basic auth
```
AuthType Basic
AuthName "Tile Cluster Manager"
AuthBasicProvider file
AuthUserFile /etc/httpd/conf/passwd
Require user valid-ser
```

Write username into HTTP header "X-Remote-User"
```
RewriteEngine On
RewriteCond %{REMOTE_USER} ^(.*)$
RewriteRule ^(.*)$ - [E=R_U:%1]
RequestHeader set X-Remote-User %{R_U}e
```
Make sure TCM picks up the username

config.py:

    USER_HEADER = 'X-Remote-User'


AWS resource tags
-----------------



