import os
import requests
import traceback
from dotenv import load_dotenv
from collections.abc import Sequence
from requests.exceptions import RequestException, HTTPError
from logger_config import get_logger

# Load environment variables
load_dotenv()

GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
logger = get_logger(__name__)

def fetch_user_repos() -> Sequence | None:
    """Return all repositories visible to the authenticated user."""
    logger.info("Fetching repositories for the authenticated user")

    try:
        repos_url = "https://api.github.com/user/repos"
        headers = {'Authorization': f'token {GITHUB_TOKEN}'} if GITHUB_TOKEN else {}
        response = requests.get(repos_url, headers=headers)
        response.raise_for_status()
        repos = response.json()

        names = [repo['full_name'] for repo in repos]
        return names
    except Exception as exc:
        logger.error(f"Failed to fetch repositories: {exc}")
        return None


def fetch_pr_changes(repo_owner: str, repo_name: str, pr_number: int) -> Sequence | None:
    """Fetch changes from a GitHub pull request.

    Args:
        repo_owner: The owner of the GitHub repository
        repo_name: The name of the GitHub repository
        pr_number: The number of the pull request to analyze

    Returns:
        A list of file changes with detailed information about each change
    """
    logger.info(f"Fetching PR changes for {repo_owner}/{repo_name}#{pr_number}")

    # Fetch PR details
    pr_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/pulls/{pr_number}"
    files_url = f"{pr_url}/files"
    headers = {'Authorization': f'token {GITHUB_TOKEN}'}

    try:
        # Get PR metadata
        pr_response = requests.get(pr_url, headers=headers)
        pr_response.raise_for_status()
        pr_data = pr_response.json()

        # Get file changes
        files_response = requests.get(files_url, headers=headers)
        files_response.raise_for_status()
        files_data = files_response.json()

        # Combine PR metadata with file changes
        changes = []
        for file in files_data:
            change = {
                'filename': file['filename'],
                'status': file['status'],  # added, modified, removed
                'additions': file['additions'],
                'deletions': file['deletions'],
                'changes': file['changes'],
                'patch': file.get('patch', ''),  # The actual diff
                'raw_url': file.get('raw_url', ''),
                'contents_url': file.get('contents_url', '')
            }
            changes.append(change)

        # Add PR metadata
        pr_info = {
            'title': pr_data['title'],
            'description': pr_data['body'],
            'author': pr_data['user']['login'],
            'created_at': pr_data['created_at'],
            'updated_at': pr_data['updated_at'],
            'state': pr_data['state'],
            'total_changes': len(changes),
            'changes': changes
        }

        logger.info(f"Successfully fetched {len(changes)} changes")
        return pr_info
    except HTTPError as e:
        logger.error(f"HTTP Error fetching PR changes: {str(e)}")
    except RequestException as req_err:
        logger.error(f"A network/connection error occurred: {str(req_err)}")
    except Exception as e:
        logger.error(f"Error fetching PR changes: {str(e)}")
        traceback.print_exc()

if __name__ == '__main__':
    # Example usage for debugging
    repos = fetch_user_repos()
    logger.debug(repos)
