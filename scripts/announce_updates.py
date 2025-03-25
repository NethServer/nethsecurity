#!/usr/bin/python3

import os
import sys
import requests
from datetime import datetime, timezone
import ghexplain

# Set environment variable for GitHub token
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# Repository information
REPO = "NethServer/nethsecurity"

# Get today's date in ISO format
today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=1, microsecond=0).isoformat()

# GitHub API URL
GITHUB_API_URL = f"https://api.github.com/repos/{REPO}/issues"


def fetch_closed_issues():
    issues = []
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    response = requests.get(GITHUB_API_URL, headers=headers, params={"state": "closed", "since": today, "per_page": 100})
    response.raise_for_status()
    for issue in response.json():
        # skip pull requests and issues with type name "Design" and "Task"
        if 'pull_request' in issue or issue['type']['name'] in ["Design", "Task"]:
            continue
        issues.append(issue)
    return issues

def create_announcement(issues):
    today_str = datetime.now().strftime("%d %B %Y")
    announcement = f"## Updates released on {today_str}\n\n"
    for issue in issues:
        # log to stderr the processed issue
        print(f"Processing issue {issue['number']}", file=sys.stderr)
        icon = ""
        title = issue["title"]
        url = issue["html_url"]
        if any('milestone goal' in label['name'] for label in issue['labels']):
            icon = f"{title} :crown:"  # Highlight the title
        announcement += f"#### {title} ([{issue['number']}]({issue['url']})) {icon}\n"
        explanation = ghexplain.issue(url)
        announcement += f"{explanation}\n\n"
        if icon:
            announcement += "\nThis feature is a milestone goal.\n\n"
    return announcement

if __name__ == "__main__":
    if len(sys.argv)!= 2:
        print("No Mattermost webhook", file=sys.stderr)
        sys.exit(1)

    closed_issues = fetch_closed_issues()
    if not closed_issues:
        print("No updates today", file=sys.stderr)
        sys.exit(0)
    announcement = create_announcement(closed_issues)

    webhook_url = sys.argv[1]
    data = { "text": announcement }
    response = requests.post(webhook_url, json=data)

    if response.status_code == 200:
        print("Message sent!", file=sys.stderr)
    else:
        print(f"Error when sending the message: {response.text}", file=sys.stderr)
        sys.exit(1)