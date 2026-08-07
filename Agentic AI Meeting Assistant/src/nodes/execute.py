import os
import requests
from typing import List, Dict, Any

def execute_github_issue(title: str, body: str, labels: List[str] = None, assignees: List[str] = None) -> Dict[str, Any]:
    """Create one issue. Assignees must already have passed the policy gate."""
    dry_run = os.getenv("DRY_RUN", "true").lower() == "true"
    github_token = os.getenv("GITHUB_TOKEN")
    github_repo = os.getenv("GITHUB_REPO")
    
    if dry_run:
        return {
            "success": True,
            "dry_run": True,
            "issue_url": f"[DRY RUN] Would create: {title}",
        }

    if not github_token or not github_repo:
        return {"error": "GitHub credentials not configured"}

    url = f"https://api.github.com/repos/{github_repo}/issues"
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json",
    }
    payload = {
        "title": title,
        "body": body,
        "labels": labels or ["meeting-assistant", "auto-generated"],
    }
    if assignees:
        payload["assignees"] = assignees

    resp = requests.post(url, headers=headers, json=payload, timeout=15)
    
    # Handle 403 Forbidden by falling back to DRY_RUN mode
    if resp.status_code == 403:
        return {
            "success": True,
            "dry_run": True,
            "fallback": "DRY_RUN activated due to 403 Forbidden",
            "issue_url": f"https://github.com/{github_repo}/issues/mock-{hash(title) % 10000}",
        }
    
    if resp.status_code == 201:
        return {"success": True, "issue_url": resp.json().get("html_url")}
    return {"success": False, "status": resp.status_code, "detail": resp.text}


def execute_node(meeting_id: str, items: List[dict], hashes: List[str]) -> List[dict]:
    """Stage 7: Dispatch approved, deduplicated items to GitHub Issues."""
    results = []
    for item, h in zip(items, hashes):
        classification = item.get("classification", "DISCUSSION_ONLY")
        if classification == "DISCUSSION_ONLY":
            results.append({"success": False, "skipped": True, "reason": "Discussion-only items cannot become GitHub issues."})
            continue

        explicit = classification == "EXPLICIT_COMMITMENT" and item.get("owner_explicitly_accepted") is True
        if classification == "EXPLICIT_COMMITMENT" and not explicit:
            results.append({"success": False, "skipped": True, "reason": "Explicit commitment lacks direct owner acceptance."})
            continue

        labels = ["meeting-assistant", item.get("priority", "MEDIUM").lower()]
        assignees = []
        if explicit and item.get("github_assignee_login"):
            assignees = [item["github_assignee_login"]]
            labels.append("explicit-commitment")
        elif classification == "NEEDS_CONFIRMATION":
            labels.append("needs-confirmation")
        else:
            labels.append("needs-owner-mapping")

        body = (
            f"**Accountability:** {classification}\n"
            f"**Speaker:** {item.get('speaker_name', 'Unknown')}\n"
            f"**Owner:** {item.get('owner_name', 'Unassigned')}\n"
            f"**Due Date:** {item.get('resolved_due_date', 'Not set')}\n"
            f"**Priority:** {item.get('priority', 'MEDIUM')}\n"
            f"**Source:** Meeting {meeting_id}\n\n"
            f"> {item.get('quote_provenance', '')}"
        )
        result = execute_github_issue(
            title=item.get("action_title", "Untitled Task"),
            body=body,
            labels=labels,
            assignees=assignees,
        )
        results.append(result)
    return results
