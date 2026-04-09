"""Deploy static files to Cloudflare Pages using Direct Upload API."""
import hashlib
import json
import requests


BASE_URL = "https://api.cloudflare.com/client/v4"


def _headers(token):
    return {"Authorization": f"Bearer {token}"}


def _create_project(account_id, token, project_name):
    """Create a Cloudflare Pages project (ignores if already exists)."""
    resp = requests.post(
        f"{BASE_URL}/accounts/{account_id}/pages/projects",
        headers={**_headers(token), "Content-Type": "application/json"},
        json={"name": project_name, "production_branch": "main"},
        timeout=30,
    )
    result = resp.json()
    # 8000007 = project already exists, that's fine
    if not result.get("success") and result.get("errors"):
        code = result["errors"][0].get("code", 0)
        if code != 8000007:
            raise RuntimeError(
                f"Failed to create project: {result['errors'][0].get('message', str(result))}"
            )
    return result


def deploy_to_cloudflare(account_id, token, project_name, files):
    """
    Deploy files to Cloudflare Pages via Direct Upload.

    Args:
        account_id: Cloudflare account ID
        token: Cloudflare API token with Pages edit permission
        project_name: Project name (lowercase, hyphens)
        files: dict of {filename: bytes_content}

    Returns:
        dict with url, project_name, id
    """
    # Ensure project exists
    _create_project(account_id, token, project_name)

    # Build manifest (filename -> sha256 hash)
    manifest = {}
    for name, content in files.items():
        if isinstance(content, str):
            content = content.encode("utf-8")
        manifest[name] = hashlib.sha256(content).hexdigest()

    # Build multipart form
    multipart = {
        "branch": (None, "main"),
        "commit_message": (None, "Deploy portfolio site"),
        "manifest": (None, json.dumps(manifest)),
    }

    # Add each file as a form field keyed by its hash
    for name, content in files.items():
        if isinstance(content, str):
            content = content.encode("utf-8")
        file_hash = hashlib.sha256(content).hexdigest()
        multipart[file_hash] = (name, content, "application/octet-stream")

    resp = requests.post(
        f"{BASE_URL}/accounts/{account_id}/pages/projects/{project_name}/deployments",
        headers=_headers(token),
        files=multipart,
        timeout=120,
    )

    result = resp.json()
    if not result.get("success"):
        errors = result.get("errors", [{}])
        msg = errors[0].get("message", str(result)) if errors else str(result)
        raise RuntimeError(f"Cloudflare deploy failed: {msg}")

    deployment = result.get("result", {})
    deploy_url = deployment.get("url", "")
    if deploy_url and not deploy_url.startswith("http"):
        deploy_url = f"https://{deploy_url}"

    return {
        "url": deploy_url,
        "project_url": f"https://{project_name}.pages.dev",
        "id": deployment.get("id", ""),
        "project_name": project_name,
    }


def add_domain(account_id, token, project_name, domain):
    """Add a custom domain to a Cloudflare Pages project."""
    resp = requests.post(
        f"{BASE_URL}/accounts/{account_id}/pages/projects/{project_name}/domains",
        headers={**_headers(token), "Content-Type": "application/json"},
        json={"name": domain},
        timeout=30,
    )
    result = resp.json()
    if not result.get("success"):
        errors = result.get("errors", [{}])
        msg = errors[0].get("message", str(result)) if errors else str(result)
        raise RuntimeError(f"Failed to add domain: {msg}")
    return result.get("result", {})
