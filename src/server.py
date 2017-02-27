#!/usr/bin/env python

from flask import Flask, render_template, request, jsonify
import logging
import requests
from ConfigParser import SafeConfigParser

# SPARQL2Git modules
import static
from github import SPARQL2GitHub

app = Flask(__name__)

# Set logging format
logging.basicConfig(level=logging.DEBUG, format=static.LOG_FORMAT)
app.debug_log_format = static.LOG_FORMAT
s2glogger = logging.getLogger(__name__)

config = SafeConfigParser()
config.read('config.ini')

CLIENT_ID = config.get('auth', 'github_client_id')
CLIENT_SECRET = config.get('auth', 'github_client_secret')

gapi = SPARQL2GitHub()

@app.route("/", methods=["GET"])
def hello():
    return render_template('index.html', client_id=CLIENT_ID)

@app.route("/callback", methods=["GET"])
def callback_oauth():
    s2glogger.debug("Received GitHub code: {}".format(request.args['code']))
    github_auth = { 'client_id' : CLIENT_ID,
                    'client_secret' : CLIENT_SECRET,
                    'code' : request.args['code'],
                    'accept' : 'json' }
    headers = {'Accept' : 'application/json'}
    r = requests.post('https://github.com/login/oauth/access_token', data = github_auth, headers=headers).json()
    s2glogger.debug("Access token from GitHub: {}".format(r))

    access_token = r['access_token']
    user_info = requests.get('https://api.github.com/user', params={'access_token' : access_token}, headers=headers).json()
    s2glogger.debug("User info: {}".format(user_info))
    user_emails = requests.get('https://api.github.com/user/emails', params={'access_token' : access_token}, headers=headers).json()
    s2glogger.debug("User emails: {}".format(user_emails))

    gapi.auth(user_info, access_token)

    sparql_repos = gapi.user_sparql_repos()

    return render_template('browser.html', user_info=user_info, user_emails=user_emails, sparql_repos=sparql_repos)

@app.route("/queries", methods=["GET"])
def queries():
    # Queries for the user and repo in params

    return jsonify(gapi.files_in_repo(request.args.get('repo', '')))

@app.route("/query", methods=["GET"])
def query():
    # Raw content of specified query

    return gapi.query_raw_content(request.args.get('repo', ''), request.args.get('file', ''))

if __name__ == "__main__":
    app.run(debug=True)
