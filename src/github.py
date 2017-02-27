#!/usr/bin/env python

import requests
import logging
from flask import jsonify

# SPARQL2Git modules
import static

class SPARQL2GitHub():
    def __init__(self):
        self.s2glogger = logging.getLogger(__name__)
        self.sparql_repos = {}

        # self.user_sparql_repos(user_url)

    def auth(self, user_info, access_token):
        self.headers = { 'Accept' : 'application/json'}
        self.params = {'access_token' : access_token, 'per_page' : '100'}

        self.user_info = user_info

    def user_sparql_repos(self):
        # Gets SPARQL repos of username

        repos_url = requests.get(self.user_info['url'], params=self.params, headers=self.headers).json()['repos_url']
        self.s2glogger.debug("Repos URL: {}".format(repos_url))
        repos_array = requests.get(repos_url, params=self.params, headers=self.headers).json()

        for repo in repos_array:
            repo_name = repo['name']
            repo_html_url = repo['html_url']
            contents_url = repo['contents_url'][:repo['contents_url'].rfind('/')]
            file_array = requests.get(contents_url, params=self.params, headers=self.headers).json()
            for file_object in file_array:
                file_name = file_object['name']
                if '.rq' in file_name or '.sparql' in file_name:
                    if repo_name not in self.sparql_repos:
                        self.sparql_repos[repo_name] = {'html_url' : repo_html_url, 'contents_url' : contents_url, 'files' : [ file_name ]}
                    else:
                        if file_name not in self.sparql_repos[repo_name]['files']:
                            self.sparql_repos[repo_name]['files'].append(file_name)

        self.s2glogger.debug("SPARQL repos: {}".format(self.sparql_repos))

        return self.sparql_repos

    def files_in_repo(self, repo_name):
        # Gets SPARQL files in repo

        return self.sparql_repos[repo_name]['files']

    def query_raw_content(self, repo_name, file_name):

        query_text = requests.get('https://raw.githubusercontent.com/{}/{}/master/{}'.format(self.user_info['login'], repo_name, file_name), params=self.params, headers=self.headers).text
        self.s2glogger.debug("Query text is: {}".format(query_text))

        return query_text
