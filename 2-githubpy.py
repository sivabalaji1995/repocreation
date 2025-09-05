from github import Github
import xml.etree.ElementTree as ET

# ----------------------------
# Helper functions
# ----------------------------
def parse_members(xml_content):
    """
    Parse XML content and return a dict: {Member Name: serialized content}
    """
    members_dict = {}
    root = ET.fromstring(xml_content)
    for member in root.findall(".//Member"):
        name = member.attrib.get("Name")
        content = ET.tostring(member, encoding="unicode")
        members_dict[name] = content
    return members_dict

def get_modified_members(old_xml, new_xml):
    """
    Compare old and new XML content and return list of modified Member Names
    """
    old_members = parse_members(old_xml)
    new_members = parse_members(new_xml)
    modified = []
    for name, new_content in new_members.items():
        old_content = old_members.get(name)
        if old_content != new_content:
            modified.append(name)
    return modified

# ----------------------------
# Main logic
# ----------------------------
ACCESS_TOKEN = "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"  # GitHub personal access token
REPO_NAME = "sivabalaji280/apitest"   
g = Github(ACCESS_TOKEN)
repo = g.get_repo(REPO_NAME)
def get_pr_list():
    pr_list = []
    pr = repo.get_pulls(state='open')
    for p in pr:
        pr_list.append(p.number)
    return pr_list

PR_NUMBER_LIST = get_pr_list()   
# print(PR_NUMBER_LIST) 

for pr_number in PR_NUMBER_LIST:
    # print(pr_number)
    pr = repo.get_pull(pr_number)
    for file in pr.get_files():
        # print(file.filename)
        if file.filename.endswith(".xml"):
            # print(file.filename)
            # Fetch old and new content
            old_xml = f"https://raw.githubusercontent.com/{REPO_NAME}/{pr.base.ref}/{file.filename}"
            new_xml = f"https://raw.githubusercontent.com/{REPO_NAME}/{pr.head.ref}/{file.filename}"

            # Simple way to fetch raw XML content
            import requests
            old_resp = requests.get(old_xml)
            new_resp = requests.get(new_xml)
            if old_resp.status_code == 200 and new_resp.status_code == 200:
                print(f"old_resp {old_resp.status_code} and new_resp {new_resp.status_code}")
                modified_names = get_modified_members(old_resp.text, new_resp.text)
                if modified_names:
                    print(f"\nFile: {file.filename}")
                    for name in modified_names:
                        print(f"- {name}")
            else:
                print(f"old_resp {old_resp.status_code} and new_resp {new_resp.status_code}")
                print(f"Could not fetch content for {file.filename}")

