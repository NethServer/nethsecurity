#!/usr/bin/python3

# Retrieve the list of issues with the "testing" label from the NethSecurity repository and send a message to Mattermost

import requests
import json
from datetime import datetime, timedelta
import sys

# GitHub API endpoint
url = "https://api.github.com/repos/NethServer/nethsecurity/issues"
params = {
    "state": "open",
    "labels": "testing",
    "per_page": 100,
    "page": 1
}

headers = {
    "Accept": "application/json"
}

def get_issues(url, params, headers):
    issues = []
    while True:
        response = requests.get(url, params=params, headers=headers)
        if response.status_code!= 200:
            print(f"Error on issue load: {response.text}")
            break

        data = json.loads(response.text)
        issues.extend(data)

        if len(data) < params["per_page"]:
            break

        params["page"] += 1

    return issues

issues = get_issues(url, params, headers)

# Preparing the message
if len(issues) <= 0:
    print("No QA needed")
    sys.exit(0)
output = "## Call for testing! \n\nCiao a tutti @here! Ci sono alcune issue aperte che richiedono il vostro aiuto per il QA:\n\n"
for issue in issues:
    created_at = datetime.strptime(issue['created_at'], '%Y-%m-%dT%H:%M:%SZ')
    if (datetime.now() - created_at) > timedelta(days=4):
        output += f"* **URGENTE**: {issue['title']} - {issue['html_url']} (aperta da più di 4 giorni)\n"
    else:
        output += f"* {issue['title']} - {issue['html_url']}\n"
output += "\nSe avete un po' di tempo, potreste aiutare a testare queste issue e fornire feedback? Grazie mille!"

# Invio del messaggio a Mattermost tramite webhook
if len(sys.argv)!= 2:
    print("No Mattermost webhook")
    sys.exit(1)

webhook_url = sys.argv[1]

data = {
    "text": output
}

response = requests.post(webhook_url, json=data)

if response.status_code == 200:
    print("Message sent!")
else:
    print(f"Error when sending the message: {response.text}")
    sys.exit(1)
