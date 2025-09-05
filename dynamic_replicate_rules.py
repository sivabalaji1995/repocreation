import requests
import json

# --- CONFIG ---
GITHUB_TOKEN = "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"   # replace with your token
ORG = "sivabalaji280"
PARENT_REPO = "mainrepo"

headers = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}


def get_all_branches(repo):
    """Fetch all branches of a repo"""
    url = f"https://api.github.com/repos/{ORG}/{repo}/branches"
    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
        print(f"❌ Failed to fetch branches for {repo}: {resp.json()}")
        return []
    return [b["name"] for b in resp.json()]


def get_child_repos_from_template():
    """Fetch repos created from parent template"""
    url = f"https://api.github.com/orgs/{ORG}/repos?per_page=100"
    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
        print(f"❌ Failed to fetch repos: {resp.json()}")
        return []

    repos = resp.json()
    children = [
        r["name"] for r in repos
        if r.get("template_repository") and r["template_repository"]["name"] == PARENT_REPO
    ]
    return children


def get_branch_protection(repo, branch):
    """Fetch protection rules for a branch"""
    url = f"https://api.github.com/repos/{ORG}/{repo}/branches/{branch}/protection"
    resp = requests.get(url, headers=headers)
    if resp.status_code == 404:
        return None
    if resp.status_code != 200:
        print(f"❌ Error fetching protection for {repo}/{branch}: {resp.json()}")
        return None
    return resp.json()


def build_protection_payload(rules):
    """Clean payload with only supported fields"""
    return {
        "required_status_checks": {
            "strict": rules.get("required_status_checks", {}).get("strict", False),
            "contexts": rules.get("required_status_checks", {}).get("contexts", [])
        } if rules.get("required_status_checks") else None,
        "enforce_admins": rules.get("enforce_admins", {}).get("enabled", False),
        "required_pull_request_reviews": {
            "dismiss_stale_reviews": rules.get("required_pull_request_reviews", {}).get("dismiss_stale_reviews", False),
            "require_code_owner_reviews": rules.get("required_pull_request_reviews", {}).get("require_code_owner_reviews", False),
            "require_last_push_approval": rules.get("required_pull_request_reviews", {}).get("require_last_push_approval", False),
            "required_approving_review_count": rules.get("required_pull_request_reviews", {}).get("required_approving_review_count", 0),
        } if rules.get("required_pull_request_reviews") else None,
        "restrictions": None,
    }


def apply_protection(repo, branch, payload):
    """Apply protection rules to child repo branch"""
    url = f"https://api.github.com/repos/{ORG}/{repo}/branches/{branch}/protection"
    resp = requests.put(url, headers=headers, json=payload)
    if resp.status_code == 200:
        print(f"✅ Applied protection to {repo}/{branch}")
    else:
        print(f"❌ Failed for {repo}/{branch}: {resp.status_code} {resp.text}")


# --- MAIN FLOW ---
print(f"🔍 Fetching all branches of parent repo '{PARENT_REPO}'...")
branches = get_all_branches(PARENT_REPO)
print(f"📌 Found branches: {branches}")

print(f"🔍 Fetching child repos created from parent template '{PARENT_REPO}'...")
child_repos = get_child_repos_from_template()
print(f"📌 Child repos: {child_repos}")

for branch in branches:
    print(f"\n--- Checking branch '{branch}' in {PARENT_REPO} ---")
    rules = get_branch_protection(PARENT_REPO, branch)
    if not rules:
        print(f"⚠️ No protection rules found for {PARENT_REPO}/{branch}. Skipping...")
        continue

    payload = build_protection_payload(rules)
    print(f"🔧 Protection rules to apply:\n{json.dumps(payload, indent=2)}")

    for repo in child_repos:
        apply_protection(repo, branch, payload)
