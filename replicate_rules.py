import requests
import json

GITHUB_TOKEN = "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"   # replace with your token
ORG = "sivabalaji1995"
PARENT_REPO = "mainrepo"
BRANCH = "main"
CHILD_REPO = "test1"   # single child repo name

headers = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}

# Step 1: Get parent repo protection
url = f"https://api.github.com/repos/{ORG}/{PARENT_REPO}/branches/{BRANCH}/protection"
resp = requests.get(url, headers=headers)

if resp.status_code == 404:
    print(f"⚠️ Parent repo '{PARENT_REPO}' branch '{BRANCH}' is NOT protected.")
    exit(0)

if resp.status_code != 200:
    print(f"❌ Failed to fetch parent protection: {resp.json()}")
    exit(1)

parent_rules = resp.json()

print(f"🔍 Fetched protection rules from {PARENT_REPO}/{BRANCH}")
print(json.dumps(parent_rules, indent=2))

# Step 2: Extract only the valid fields
protection_payload = {
    "required_status_checks": {
        "strict": parent_rules.get("required_status_checks", {}).get("strict", False),
        "contexts": parent_rules.get("required_status_checks", {}).get("contexts", [])
    },
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

print("🔧 Prepared protection payload:")
print(json.dumps(protection_payload, indent=2))

# Step 3: Apply to child repo
put_url = f"https://api.github.com/repos/{ORG}/{CHILD_REPO}/branches/{BRANCH}/protection"
resp = requests.put(put_url, headers=headers, json=protection_payload)

if resp.status_code == 200:
    print(f"✅ Applied rules to {CHILD_REPO}")
else:
    print(f"❌ Failed for {CHILD_REPO}: {resp.json()}")
