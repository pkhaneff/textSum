import os
import requests
from log import Log
from dotenv import load_dotenv

load_dotenv()

class EnvVars:
    def __init__(self):
        self.owner = os.getenv('REPO_OWNER')
        self.repo = os.getenv('REPO_NAME')
        self.token = os.getenv('GITHUB_TOKEN')
        
        self.pull_number = os.getenv('PULL_NUMBER')
        if not self.pull_number:
            self.pull_number = self.get_latest_pull_number()
        
        self.base_ref = os.getenv('GITHUB_BASE_REF') 
        self.head_ref = os.getenv('GITHUB_HEAD_REF') 

        self.chat_gpt_token = os.getenv('CHATGPT_KEY') 
        self.chat_gpt_model = os.getenv('CHATGPT_MODEL') 

        self.target_extensions = os.getenv('TARGET_EXTENSIONS')
        self.target_extensions = [lang.strip() for lang in self.target_extensions.split(",")] if self.target_extensions else []

        self.commit_id = os.getenv('GITHUB_SHA') 

        if len(self.target_extensions) == 0:
            raise ValueError(f"Please specify TARGET_EXTENSIONS. Comma separated, could be: kt,java,py,js,swift,c,h. Only these files will be reviewed")

        self.env_vars = {
            "owner": self.owner,
            "repo": self.repo,
            "token": self.token,
            "base_ref": self.base_ref,
            "pull_number": self.pull_number,
            "chat_gpt_token": self.chat_gpt_token,
            "chat_gpt_model": self.chat_gpt_model,
            "commit_id": self.commit_id,  
        }

    def get_latest_pull_number(self):
        """Tự động lấy PR mới nhất nếu không có PULL_NUMBER"""
        url = f"https://api.github.com/repos/{self.owner}/{self.repo}/pulls?state=open"
        headers = {"Authorization": f"token {self.token}", "Accept": "application/vnd.github.v3+json"}

        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            pull_requests = response.json()
            if pull_requests:
                latest_pr = pull_requests[0] 
                return str(latest_pr["number"]) 
            else:
                raise ValueError("No open pull requests found.")
        else:
            raise ValueError(f"Failed to fetch PRs: {response.status_code}, {response.text}")

    def check_vars(self):
        missing_vars = [var for var, value in self.env_vars.items() if not value]
        if missing_vars:
            missing_vars_str = ", ".join(missing_vars)
            raise ValueError(f"The following environment variables are missing or empty: {missing_vars_str}")
        else:
            Log.print_green("All required environment variables are set.")
