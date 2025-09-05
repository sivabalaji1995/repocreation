import requests
import json
import sys
import os

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")  # replace with your token
ORG = os.getenv("ORG")
PARENT_REPO = os.getenv("PARENT_REPO")
CHILD_REPO = os.getenv("CHILD_REPO")

headers = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}

def get_branch_protection(repo, branch):
    """Fetch branch protection rules for a repo/branch"""
    url = f"https://api.github.com/repos/{ORG}/{repo}/branches/{branch}/protection"
    resp = requests.get(url, headers=headers)
    if resp.status_code == 404:
        return None  # no protection
    if resp.status_code != 200:
        raise Exception(f"❌ Failed to fetch protection for {repo}/{branch}: {resp.json()}")
    return resp.json()

def prepare_payload(parent_rules):
    """Extract only valid fields for protection payload"""
    return {
        "required_status_checks": {
            "strict": parent_rules.get("required_status_checks", {}).get("strict", False),
            "contexts": parent_rules.get("required_status_checks", {}).get("contexts", [])
        } if parent_rules.get("required_status_checks") else None,
        "enforce_admins": parent_rules.get("enforce_admins", {}).get("enabled", False),
        "required_pull_request_reviews": {
            "dismiss_stale_reviews": parent_rules.get("required_pull_request_reviews", {}).get("dismiss_stale_reviews", False),
            "require_code_owner_reviews": parent_rules.get("required_pull_request_reviews", {}).get("require_code_owner_reviews", False),
            "require_last_push_approval": parent_rules.get("required_pull_request_reviews", {}).get("require_last_push_approval", False),
            "required_approving_review_count": parent_rules.get("required_pull_request_reviews", {}).get("required_approving_review_count", 0),
        } if parent_rules.get("required_pull_request_reviews") else None,
        "restrictions": None,
        "required_linear_history": parent_rules.get("required_linear_history", {}).get("enabled", False),
        "allow_force_pushes": parent_rules.get("allow_force_pushes", {}).get("enabled", False),
        "allow_deletions": parent_rules.get("allow_deletions", {}).get("enabled", False),
        "block_creations": parent_rules.get("block_creations", {}).get("enabled", False),
        "required_conversation_resolution": parent_rules.get("required_conversation_resolution", {}).get("enabled", False),
        "lock_branch": parent_rules.get("lock_branch", {}).get("enabled", False),
        "allow_fork_syncing": parent_rules.get("allow_fork_syncing", {}).get("enabled", False),
    }

def apply_protection(child_repo, branch, payload):
    """Apply branch protection rules to child repo"""
    url = f"https://api.github.com/repos/{ORG}/{child_repo}/branches/{branch}/protection"
    resp = requests.put(url, headers=headers, json=payload)
    if resp.status_code == 200:
        print(f"✅ Applied rules to {child_repo}/{branch}")
    else:
        print(f"❌ Failed for {child_repo}/{branch}: {resp.json()}")

# Step 1: Get all branches in child repo
branches_url = f"https://api.github.com/repos/{ORG}/{CHILD_REPO}/branches?per_page=100"
resp = requests.get(branches_url, headers=headers)
if resp.status_code != 200:
    raise Exception(f"❌ Failed to fetch branches for {CHILD_REPO}: {resp.json()}")

branches = [b["name"] for b in resp.json()]
print(f"🔍 Found branches in {CHILD_REPO}: {branches}")

# Step 2: For each branch, check if parent has protection and apply if exists
for branch in branches:
    parent_rules = get_branch_protection(PARENT_REPO, branch)
    if parent_rules:
        payload = prepare_payload(parent_rules)
        print(f"🔧 Applying rules from {PARENT_REPO}/{branch} → {CHILD_REPO}/{branch}")
        apply_protection(CHILD_REPO, branch, payload)
    else:
        print(f"⚠️ No protection rules found for {PARENT_REPO}/{branch}, skipping...")
