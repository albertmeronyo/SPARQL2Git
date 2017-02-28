#!/usr/bin/env python

import requests
import logging
from flask import jsonify
from grlc.gquery import get_yaml_decorators
import json
from base64 import b64encode

# SPARQL2Git modules
import static

class SPARQL2GitHub():
    def __init__(self):
        self.s2glogger = logging.getLogger(__name__)
        self.sparql_repos = {}

        # self.user_sparql_repos(user_url)

    def auth(self, user_info, access_token, scope):
        self.headers = { 'Accept' : 'application/json', 'Authorization': 'token {}'.format(access_token)}

        self.user_info = user_info
        self.scope = scope

    def user_sparql_repos(self):
        # Gets SPARQL repos of username

        repos_url = requests.get(self.user_info['url'], headers=self.headers).json()['repos_url']
        self.s2glogger.debug("Repos URL: {}".format(repos_url))
        repos_array = requests.get(repos_url, params={'per_page' : "100"}, headers=self.headers).json()

        # for repo in repos_array:
        #     repo_name = repo['name']
        #     repo_html_url = repo['html_url']
        #     contents_url = repo['contents_url'][:repo['contents_url'].rfind('/')]
        #     file_array = requests.get(contents_url, params={'per_page' : "100"}, headers=self.headers).json()
        #     for file_object in file_array:
        #         if 'name' not in file_object: # Repository is empty
        #             break
        #         file_name = file_object['name']
        #         file_sha = file_object['sha']
        #         if '.rq' in file_name or '.sparql' in file_name:
        #             if repo_name not in self.sparql_repos:
        #                 self.sparql_repos[repo_name] = {'html_url' : repo_html_url, 'contents_url' : contents_url, 'files' : [ {'file_name': file_name, 'sha' : file_sha }]}
        #             else:
        #                 if file_name not in [file_str['file_name'] for file_str in self.sparql_repos[repo_name]['files']]:
        #                     self.sparql_repos[repo_name]['files'].append({'file_name': file_name, 'sha': file_sha})

        # self.s2glogger.debug("SPARQL repos: {}".format(self.sparql_repos))
        self.s2glogger.debug("SPARQL repos: {}".format(repos_array))

        return repos_array

    def files_in_repo(self, repo):
        # Gets SPARQL files in repo

        # return self.sparql_repos[repo_name]['files']
        contents_url = 'https://api.github.com/repos/{}/{}/contents'.format(self.user_info['login'], repo)
        file_array = requests.get(contents_url, params={'per_page' : "100"}, headers=self.headers).json()
        files = []
        for file_object in file_array:
            if 'name' not in file_object: # Repository is empty
                break
            file_name = file_object['name']
            # file_sha = file_object['sha']
            if '.rq' in file_name or '.sparql' in file_name:
                files.append(file_object)
                # else:
                #     if file_name not in [file_str['file_name'] for file_str in self.sparql_repos[repo_name]['files']]:
                #         self.sparql_repos[repo_name]['files'].append({'file_name': file_name, 'sha': file_sha})

        return files

    def query_contents(self, repo_name, file_name):
        # JSON object with content of specified query, separating query from metadata

        query_text = requests.get('https://raw.githubusercontent.com/{}/{}/master/{}'.format(self.user_info['login'], repo_name, file_name), headers=self.headers).text
        self.s2glogger.debug("Query text is: {}".format(query_text))

        return jsonify(get_yaml_decorators(query_text))

    def create_repo(self, repo_name, description=None):
        # Creates repo for the authenticated user

        data = { "name": repo_name,
                 "description": description,
                 "homepage": None,
                 "private": False,
                 "has_issues": True,
                 "has_wiki": True }
        self.s2glogger.debug("Requesting new repo with data: {}".format(json.dumps(data)))
        resp = requests.post('https://api.github.com/user/repos', headers=self.headers, data=json.dumps(data)).json()
        self.s2glogger.debug("Request to create SPARQL repository returned status {}".format(resp))

        return jsonify(resp)

    def create_query(self, repo, name):
        # Creates file 'name' for user and repo

        data = { "message": "Created new SPARQL query",
                 "committer": {
                    "name": self.user_info['name'],
                    "email": self.user_info['email']
                 },
                 "content": b64encode("SELECT * WHERE {?s ?p ?o}") }
        self.s2glogger.debug("Requesting new query with data: {}".format(json.dumps(data)))
        resp = requests.put('https://api.github.com/repos/{}/{}/contents/{}'.format(self.user_info['login'], repo, name), headers=self.headers, data=json.dumps(data)).json()
        self.s2glogger.debug("Request to create SPARQL query file returned status {}".format(resp))

        return jsonify(resp)

    def commit_query(self, repo, name, commit, sha, content):
        # Commits file

        data = { "message": commit,
                 "committer": {
                    "name": self.user_info['login'],
                    "email": self.user_info['email']
                 },
                 "content": b64encode(content),
                 "sha": sha }
        self.s2glogger.debug("Requesting new query with data: {}".format(json.dumps(data)))
        resp = requests.put('https://api.github.com/repos/{}/{}/contents/{}'.format(self.user_info['login'], repo, name), headers=self.headers, data=json.dumps(data)).json()
        self.s2glogger.debug("Request to create SPARQL query file returned status {}".format(resp))

        return jsonify(resp)
