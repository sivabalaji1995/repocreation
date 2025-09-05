import requests
import re
import hashlib

# ==== CONFIG ====
GITHUB_TOKEN = "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"           # PAT with repo scope for private repos; fine for public too
OWNER = "sivabalaji1995"            # your username (or org name if you switch endpoints accordingly)
PARENT_REPO = "mainrepo"            # template repo name
PARENT_COMMITS_TO_SCAN = 50         # increase if children were created long ago

headers = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}

# ---------- Helpers ----------

def get_user_repos(owner):
    """List repos under a user account (switch to /orgs/{org}/repos for orgs)."""
    url = f"https://api.github.com/users/{owner}/repos?per_page=100&type=all"
    r = requests.get(url, headers=headers)
    r.raise_for_status()
    return r.json()

def get_default_branch(owner, repo):
    r = requests.get(f"https://api.github.com/repos/{owner}/{repo}", headers=headers)
    r.raise_for_status()
    return r.json().get("default_branch") or "main"

def get_oldest_commit_sha(owner, repo, branch):
    """
    Get the oldest commit on a branch by jumping to the last page of commits.
    GitHub's commits API returns newest-first and doesn't support 'direction=asc'.
    """
    first_page = f"https://api.github.com/repos/{owner}/{repo}/commits?sha={branch}&per_page=1"
    r = requests.get(first_page, headers=headers)
    if r.status_code == 409:
        # "Git Repository is empty"
        return None
    r.raise_for_status()
    data = r.json()
    if not isinstance(data, list) or not data:
        return None

    link = r.headers.get("Link", "")
    # If there's a 'last' page, go there
    m = re.search(r'<([^>]+)>;\s*rel="last"', link)
    if m:
        last_url = m.group(1)
        r2 = requests.get(last_url, headers=headers)
        r2.raise_for_status()
        lst = r2.json()
        return lst[0]["sha"] if lst else None
    else:
        # Only one page: the only commit is both newest and oldest
        return data[-1]["sha"]

def tree_fingerprint(owner, repo, commit_sha):
    """
    Build a stable fingerprint of a commit's tree: SHA256 over (path, blob_sha) pairs.
    """
    # Get git commit to retrieve tree SHA
    rc = requests.get(f"https://api.github.com/repos/{owner}/{repo}/git/commits/{commit_sha}", headers=headers)
    if rc.status_code != 200:
        return None
    tree_sha = rc.json()["tree"]["sha"]

    # Get full tree (recursive)
    rt = requests.get(f"https://api.github.com/repos/{owner}/{repo}/git/trees/{tree_sha}?recursive=1", headers=headers)
    if rt.status_code != 200:
        return None
    t = rt.json()

    # If truncated (very large trees), fingerprint may be unreliable
    nodes = t.get("tree", [])
    pairs = [(n["path"], n["sha"]) for n in nodes if n.get("type") == "blob"]
    pairs.sort()

    h = hashlib.sha256()
    for path, sha in pairs:
        h.update(path.encode("utf-8"))
        h.update(sha.encode("utf-8"))
    return h.hexdigest()

def collect_parent_snapshots(owner, repo, branch, limit):
    """
    Build fingerprints for the latest `limit` commits on the parent template.
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/commits?sha={branch}&per_page={limit}"
    r = requests.get(url, headers=headers)
    r.raise_for_status()
    commits = r.json()
    fps = set()
    for c in commits:
        sha = c["sha"]
        fp = tree_fingerprint(owner, repo, sha)
        if fp:
            fps.add(fp)
    return fps

# ---------- Main ----------

def main():
    parent_branch = get_default_branch(OWNER, PARENT_REPO)
    print(f"🔍 Parent: {OWNER}/{PARENT_REPO}@{parent_branch}")

    parent_fps = collect_parent_snapshots(OWNER, PARENT_REPO, parent_branch, PARENT_COMMITS_TO_SCAN)
    print(f"🧩 Collected {len(parent_fps)} parent content snapshots to compare against.")

    repos = get_user_repos(OWNER)

    matches = []
    for r in repos:
        name = r["name"]
        if name == PARENT_REPO:
            continue
        branch = r.get("default_branch") or "main"

        oldest = get_oldest_commit_sha(OWNER, name, branch)
        if not oldest:
            print(f"⏭️  {name}: empty repo or no commits — skipping.")
            continue

        child_fp = tree_fingerprint(OWNER, name, oldest)
        if not child_fp:
            print(f"⚠️  {name}: failed to fingerprint tree — skipping.")
            continue

        if child_fp in parent_fps:
            print(f"✅ {name}: matches a snapshot of {PARENT_REPO} → likely created from the template.")
            matches.append(name)
        else:
            print(f"❌ {name}: no snapshot match found.")

    print("\n📌 Repos likely created from template:", matches)

if __name__ == "__main__":
    main()
