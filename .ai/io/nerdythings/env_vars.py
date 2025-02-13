import os
import json
from dotenv import load_dotenv

# Load environment variables
dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path=dotenv_path)

class GitHubEnv:
    def __init__(self):
        self.event_name = os.getenv("GITHUB_EVENT_NAME")
        self.event_path = os.getenv("GITHUB_EVENT_PATH")
        self.chat_gpt_token = os.getenv("CHATGPT_KEY")
        self.chat_gpt_model = os.getenv("CHATGPT_MODEL")
        self.github_token = os.getenv("GITHUB_TOKEN")
        self.target_extensions = os.getenv("TARGET_EXTENSIONS", "kt,java,py,js,ts,swift,c,cpp").split(",")

        if not self.event_path:
            raise ValueError("GITHUB_EVENT_PATH is not set. Make sure this variable is defined.")

        with open(self.event_path, "r") as f:
            self.event_payload = json.load(f)
        
        self.owner, self.repo, self.base_ref, self.head_ref, self.pull_number = self.parse_event()
        
        self.validate_required_vars()
    
    def parse_event(self):
        """Parses the event payload and extracts relevant information."""
        if self.event_name == "pull_request":
            return self.handle_pull_request_event()
        return None, None, None, None, None  # Ignore other event types
    
    def handle_pull_request_event(self):
        """Handles pull request events."""
        pr = self.event_payload.get("pull_request", {})
        owner = pr.get("base", {}).get("repo", {}).get("owner", {}).get("login")
        repo = pr.get("base", {}).get("repo", {}).get("name")
        pull_number = str(pr.get("number"))
        base_ref = pr.get("base", {}).get("ref")
        head_ref = pr.get("head", {}).get("sha")
        
        return owner, repo, base_ref, head_ref, pull_number
    
    def validate_required_vars(self):
        """Validates necessary environment variables."""
        required_vars = ["CHATGPT_KEY", "CHATGPT_MODEL", "GITHUB_TOKEN"]
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
    
    def should_review_code(self):
        """Checks whether code review should be triggered."""
        return self.pull_number is not None

# Usage
github_env = GitHubEnv()
if github_env.should_review_code():
    print("Triggering AI-based code review...")
else:
    print("No open PR detected. Skipping review.")
