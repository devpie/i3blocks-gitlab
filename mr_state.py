#!/usr/bin/env python3
import configparser
import json
import os
import urllib.request
from functools import reduce

import keyring
import sys

get_password = keyring.get_password
urlopen = urllib.request.urlopen

class Config:
    def __init__(self, filename):
        with open(filename) as file:
            self.config = configparser.ConfigParser()
            self.config.read_file(file)

        gitlab_section = self.config["gitlab"]
        self.group_id = int(gitlab_section["group_id"])
        self.group_name = gitlab_section["group_name"]
        self.base_url = gitlab_section["base_url"]
        self.user_id = int(gitlab_section["user_id"])
        self.web_browser = gitlab_section["web_browser"]
        self.label = gitlab_section.get("label", "").strip("\"")
        self.approved_merge_requests_label = gitlab_section.get("approved_merge_requests_label", "").strip("\"")
        self.all_merge_requests_label = gitlab_section.get("all_merge_requests_label", "").strip("\"")


class MergeRequestIds:
    def __init__(self, project_id, mr_id):
        self.project_id = project_id
        self.mr_id = mr_id


def get_open_merge_requests_url(config):
    return "%s/api/v4/groups/%s/merge_requests?state=opened" % \
           (config.base_url, config.group_id)


def get_approvals_url(base_url, merge_request_id):
    return "%s/api/v4/projects/%s/merge_requests/%s/approvals" % \
           (base_url, merge_request_id.project_id, merge_request_id.mr_id)


def create_request(url, token):
    request = urllib.request.Request(url)
    request.add_header("Private-Token", token)
    return request


def get_response(request):
    response = urlopen(request)
    return json.loads(response.read().decode("utf-8"))


def get_approved_count(config, auth_token, merge_request_id):
    http_request = create_request(get_approvals_url(config.base_url, merge_request_id), auth_token)
    merge_request_approvals = get_response(http_request)
    return len(list(filter(lambda user: user["user"]["id"] == config.user_id, merge_request_approvals["approved_by"])))


def get_approved_counter(config, auth_token):
    return lambda merge_request_id: get_approved_count(config, auth_token, merge_request_id)


def get_approved_mr_count(config, auth_token, open_merge_requests):
    mr_ids = get_mr_ids(open_merge_requests)
    return reduce(lambda a, b: a + b, map(get_approved_counter(config, auth_token), mr_ids))


def get_mr_ids(open_merge_requests):
    merge_request_ids = [MergeRequestIds(mr["project_id"], mr["iid"]) for mr in open_merge_requests]
    return merge_request_ids


def get_token():
    return get_password('gitlab', 'only-secret')


def get_open_merge_requests_without_wip(open_merge_requests):
    return list(filter(lambda mr: not mr['title'].lower().startswith("wip"), open_merge_requests))


def main():
    config = Config("%s/.i3block-gitlab" % os.environ['HOME'])
    if len(sys.argv) > 1:
        os.system("%s %s/groups/%s/-/merge_requests &" % (config.web_browser, config.base_url, config.group_name))
    auth_token = get_token()
    open_merge_requests_url = get_open_merge_requests_url(config)
    http_request = create_request(open_merge_requests_url, auth_token)
    open_merge_requests = get_response(http_request)
    open_merge_requests_without_wip = get_open_merge_requests_without_wip(open_merge_requests)
    open_mr_count = len(open_merge_requests_without_wip)
    approved_mr_count = get_approved_mr_count(config, auth_token, open_merge_requests_without_wip)
    print("%s%s%s / %s%s" % (config.label, config.approved_merge_requests_label, approved_mr_count, config.all_merge_requests_label, open_mr_count))
    print("MRs: %s / %s" % (approved_mr_count, open_mr_count))
    print("#FF0000" if approved_mr_count < open_mr_count - 2 else "#FFFFFF")


if __name__ == '__main__':
    main()
