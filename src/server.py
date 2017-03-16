#!/usr/bin/env python

from flask import Flask, render_template, request, make_response, session
import logging
import requests
from ConfigParser import SafeConfigParser
from json import dumps

# SPARQL2Git modules
import static
from github import SPARQL2GitHub

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0 # Avoid browser caching of static assets

# Set logging format
logging.basicConfig(level=logging.DEBUG, format=static.LOG_FORMAT)
app.debug_log_format = static.LOG_FORMAT
s2glogger = logging.getLogger(__name__)

config = SafeConfigParser()
config.read('config.ini')

CLIENT_ID = config.get('auth', 'github_client_id')
CLIENT_SECRET = config.get('auth', 'github_client_secret')

app.secret_key = CLIENT_SECRET # We use GitHub's secret to encrypt session cookies

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
    s2glogger.debug("Access token and scopes from GitHub: {}".format(r))

    access_token = r['access_token']
    scope = r['scope']
    user_info = requests.get('https://api.github.com/user', params={'access_token' : access_token}, headers=headers).json()
    s2glogger.debug("User info: {}".format(user_info))

    session['username'] = user_info['login']
    session['access_token'] = access_token

    # gapi.auth(session['username'], session['access_token'])

    sparql_repos = gapi.user_sparql_repos(session['username'], session['access_token'])

    return render_template('repos.html', username=session['username'], sparql_repos=sparql_repos)

@app.route("/edit", methods=["GET"])
def edit():
    repo = request.args.get('repo', '')

    s2glogger.debug("Preparing editor with user {}".format(session['username']))
    s2glogger.debug("Preparing editor with repo {}".format(repo))
    files = gapi.files_in_repo(session['username'], session['access_token'], repo)

    return render_template('browser.html', username=session['username'], files=files, repo=repo)

@app.route("/queries", methods=["GET"])
def queries():
    # Queries for the user and repo in params

    return make_response(dumps(gapi.files_in_repo(session['username'], session['access_token'], request.args.get('repo', ''))))

@app.route("/query", methods=["GET"])
def query():
    # JSON object with content of specified query, separating query from metadata

    return gapi.query_contents(session['username'], session['access_token'], request.args.get('repo', ''), request.args.get('file', ''))

@app.route("/newrepo", methods=["POST"])
def newrepo():

    repo_name = request.form.get('repo_name', '')
    repo_description = request.form.get('repo_description', '')
    resp = gapi.create_repo(session['username'], session['access_token'], repo_name, repo_description)

    return resp

# @app.route("/newquery", methods=["POST"])
# def newquery():
#
#     query_name = request.form.get('query_name', '')
#     repo = request.form.get('repo', '')
#     resp = gapi.create_query(repo, query_name)
#
#     return resp

@app.route("/commitquery", methods=["POST"])
def commitquery():

    query_name = request.form.get('query_name', '')
    commit = request.form.get('commit', '')
    sha = request.form.get('sha', '')
    content = request.form.get('content', '')
    repo = request.form.get('repo', '')
    content = request.form.get('content', '')
    summary = request.form.get('summary', '')
    endpoint = request.form.get('endpoint' , '')
    mime = request.form.get('mime', '')
    tags = request.form.get('tags', '')
    enum = request.form.get('enumerate', '')
    method = request.form.get('method', '')
    pagination = request.form.get('pagination', '')

    full_content = "#+ summary: {}\n#+ endpoint: {}\n".format(summary, endpoint)
    if mime:
        full_content += "#+ mime: {}\n".format(mime)
    if tags:
        full_content += "#+ tags:\n"
        for tag in tags.split(','):
            full_content += "#+   - {}\n".format(tag)
    if enum:
        full_content += "#+ enumerate:\n"
        for en in enum.split(','):
            full_content += "#+   - {}\n".format(en)
    if method:
        full_content += "#+ method: {}\n".format(method)
    if pagination:
        full_content += "#+ pagination: {}\n".format(pagination)
    full_content += "\n"
    full_content += content

    s2glogger.debug("Committing full contents: {}".format(full_content))

    resp = gapi.commit_query(session['username'], session['access_token'], repo, query_name, commit, sha, full_content)

    return resp

@app.route("/deletequery", methods=["POST"])
def deletequery():

    repo = request.form.get('repo', '')
    name =  request.form.get('name', '')
    sha = request.form.get('sha', '')

    resp = gapi.delete_query(session['username'], session['access_token'], repo, name, sha)

    return resp

if __name__ == "__main__":
    app.run(debug=True, host=static.DEFAULT_HOST, port=static.DEFAULT_PORT)
