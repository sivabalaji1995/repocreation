import requests
import os
import sys

# --- Config from environment variables ---
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")  # PAT with 'repo' and 'admin:org' scopes
ORG = os.getenv("ORG")                     # org or user account
PARENT_REPO = os.getenv("PARENT_REPO")     # template repo
CHILD_REPO = os.getenv("CHILD_REPO")       # new repo name

if not all([GITHUB_TOKEN, ORG, PARENT_REPO, CHILD_REPO]):
    print("Missing required environment variables: GITHUB_TOKEN, ORG, PARENT_REPO, CHILD_REPO")
    sys.exit(1)

headers = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}

# --- Step 1: Check if repo already exists ---
check_url = f"https://api.github.com/repos/{ORG}/{CHILD_REPO}"
check_resp = requests.get(check_url, headers=headers)

if check_resp.status_code == 200:
    print(f"Repo '{CHILD_REPO}' already exists. Skipping creation.")
    sys.exit(0)  # Exit successfully so the workflow proceeds to next task

# --- Step 2: Create repo from template ---
print(f"Creating repo '{CHILD_REPO}' from template '{PARENT_REPO}'...")

url = f"https://api.github.com/repos/{ORG}/{PARENT_REPO}/generate"
payload = {
    "owner": ORG,
    "name": CHILD_REPO,
    "private": False,   # set to True if you want private repo
    "include_all_branches": True
}

resp = requests.post(url, headers=headers, json=payload)

if resp.status_code not in [200, 201]:
    print(f"Failed to create repo: {resp.status_code}, {resp.text}")
    sys.exit(1)

print(f"Repo '{CHILD_REPO}' created successfully!")
