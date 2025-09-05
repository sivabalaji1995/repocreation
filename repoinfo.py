import requests
import json

GITHUB_TOKEN = "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"   # replace with your PAT
USER = "sivabalaji1995"     # your username
PARENT_REPO = "mainrepo"   # template repo name

headers = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}

url = f"https://api.github.com/users/{USER}/repos?per_page=100"
resp = requests.get(url, headers=headers)

if resp.status_code != 200:
    raise Exception(f"GitHub API error: {resp.status_code}, {resp.text}")

repos = resp.json()
print(resp)
for repo in repos:
    print(json.dumps(repo, indent=4))