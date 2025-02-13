import requests
from repository.repository import Repository, RepositoryError

class GitHub(Repository):
    def __init__(self, token: str, repo_owner: str, repo_name: str, pull_number: str = None):
        self.token = token
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.pull_number = pull_number
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }

    def _get_open_pull_requests(self):
        url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/pulls?state=open"
        response = requests.get(url, headers=self.headers)
        if response.status_code != 200:
            raise RepositoryError(f"Error fetching pull requests {response.status_code}: {response.text}")
        return response.json()
    
    def _get_matching_pr(self):
        pull_requests = self._get_open_pull_requests()
        return next((pr for pr in pull_requests if pr["number"] == int(self.pull_number)), None)
    
    def get_latest_commit_id(self) -> str:
        matching_pr = self._get_matching_pr()
        if not matching_pr:
            raise RepositoryError(f"No matching open PR found for {self.pull_number}.")

        commits_response = requests.get(matching_pr["commits_url"], headers=self.headers)
        if commits_response.status_code != 200:
            raise RepositoryError(f"Error fetching commits {commits_response.status_code}: {commits_response.text}")

        commits = commits_response.json()
        if not commits:
            raise RepositoryError("No commits found in this pull request.")
        return commits[-1]["sha"]
    
    def post_comment(self, text: str, commit_id: str = None, file_path: str = None, line: int = None):
        if not self.pull_number or not self._get_matching_pr():
            raise RepositoryError("No open PR found. Cannot post comment.")
        
        url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/issues/{self.pull_number}/comments"
        body = {"body": text}
        
        if commit_id and file_path and line is not None:
            url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/pulls/{self.pull_number}/comments"
            body.update({
                "commit_id": commit_id,
                "path": file_path,
                "position": line
            })
        
        response = requests.post(url, json=body, headers=self.headers)
        if response.status_code not in [200, 201]:
            raise RepositoryError(f"Error posting comment {response.status_code}: {response.text}")
        return response.json()
