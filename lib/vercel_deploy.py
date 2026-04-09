"""Deploy static files to Vercel using their API."""
import base64
import requests


def deploy_to_vercel(token, project_name, files, team_id=None):
    """
    Deploy files to Vercel.

    Args:
        token: Vercel API token
        project_name: Name for the Vercel project (lowercase, hyphens ok)
        files: dict of {filename: bytes_content}
        team_id: Optional Vercel team ID

    Returns:
        dict with deployment info (url, id, readyState, etc.)
    """
    file_list = []
    for name, content in files.items():
        if isinstance(content, str):
            content = content.encode("utf-8")
        file_list.append({
            "file": name,
            "data": base64.b64encode(content).decode("utf-8"),
        })

    payload = {
        "name": project_name,
        "files": file_list,
        "target": "production",
        "projectSettings": {
            "framework": None,
        },
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    params = {}
    if team_id:
        params["teamId"] = team_id

    response = requests.post(
        "https://api.vercel.com/v13/deployments",
        headers=headers,
        json=payload,
        params=params,
        timeout=60,
    )

    result = response.json()

    if response.status_code >= 400:
        error_msg = result.get("error", {}).get("message", str(result))
        raise RuntimeError(f"Vercel API error ({response.status_code}): {error_msg}")

    return {
        "url": f"https://{result.get('url', '')}",
        "alias": [f"https://{a}" for a in result.get("alias", [])],
        "id": result.get("id", ""),
        "readyState": result.get("readyState", ""),
        "project_name": project_name,
    }


def add_domain(token, project_name, domain, team_id=None):
    """Add a custom domain to a Vercel project."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    params = {}
    if team_id:
        params["teamId"] = team_id

    response = requests.post(
        f"https://api.vercel.com/v10/projects/{project_name}/domains",
        headers=headers,
        json={"name": domain},
        params=params,
        timeout=30,
    )

    result = response.json()
    if response.status_code >= 400:
        error_msg = result.get("error", {}).get("message", str(result))
        raise RuntimeError(f"Failed to add domain: {error_msg}")

    return result
