import json
import os

def load_org_structure(path):
    with open(path, 'r') as f:
        return json.load(f)

def get_email_by_name(name, org_structure):
    """
    Given a name, return the email from org_structure.
    org_structure should be a dict with name/email mapping.
    """
    # Example assumes org_structure is {"members": [{"name": ..., "email": ...}, ...]}
    for member in org_structure.get("members", []):
        if member["name"].lower() == name.lower():
            return member["email"]
    return None

def get_emails_by_names(names, org_structure):
    emails = []
    for name in names:
        email = get_email_by_name(name, org_structure)
        if email:
            emails.append(email)
    return emails
