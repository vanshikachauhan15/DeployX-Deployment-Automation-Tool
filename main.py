import yaml
import os
import subprocess
from dotenv import load_dotenv
from github import Github
from core.deploy_manager import DeploymentManager
from core.log_manager import LogManager

# Load environment variables
load_dotenv()

# Get GitHub credentials from environment variables
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
GITHUB_ORG = os.getenv("GITHUB_USERNAME", "")

def select_repo():
    """Interactive repository selection from GitHub."""
    if not GITHUB_TOKEN:
        print("❌ Error: GITHUB_TOKEN not set in environment variables!")
        print("Please set it in your .env file or export it.")
        return None
    
    if not GITHUB_ORG:
        print("❌ Error: GITHUB_USERNAME not set in environment variables!")
        print("Please set it in your .env file or export it.")
        return None
    
    try:
        g = Github(GITHUB_TOKEN)
        org = g.get_user(GITHUB_ORG)
        repos = org.get_repos()

        print("\nAvailable repositories:")
        repo_list = []
        for i, repo in enumerate(repos, start=1):
            print(f"{i}. {repo.name}")
            repo_list.append((repo.name, repo.clone_url))

        if not repo_list:
            print("No repositories found!")
            return None

        choice = int(input("\nSelect repository to deploy (number): "))
        if choice < 1 or choice > len(repo_list):
            print("Invalid selection!")
            return None
        return repo_list[choice - 1]
    except Exception as e:
        print(f"❌ Error fetching repositories: {e}")
        return None

def main():
    """Main CLI entry point."""
    # Load config
    try:
        with open("config.yaml", "r") as file:
            config = yaml.safe_load(file)
    except FileNotFoundError:
        print("⚠️ config.yaml not found, using defaults")
        config = {}
    except yaml.YAMLError as e:
        print(f"❌ Error parsing config.yaml: {e}")
        config = {}

    # Choose repo dynamically
    repo_info = select_repo()
    if not repo_info:
        print("❌ No repository selected. Exiting.")
        return

    repo_name, repo_url = repo_info
    log_file = os.getenv("LOG_FILE", config.get("log_file", "logs/deployment.log"))
    deploy_path = os.getenv("DEPLOY_BASE_PATH", config.get("deploy_base_path", "deployments"))
    
    # Ensure deployment directory exists
    os.makedirs(deploy_path, exist_ok=True)
    
    local_path = os.path.join(deploy_path, repo_name)

    log_manager = LogManager(log_file)
    
    print(f"\n🚀 Starting Deployment Process for {repo_name}...\n")
    log_manager.log(f"Starting deployment for {repo_url}")

    try:
        # Clone repository if it doesn't exist, otherwise pull
        if os.path.exists(local_path):
            print(f"📦 Repository already exists. Pulling latest changes...")
            result = subprocess.run(
                ["git", "pull"],
                cwd=local_path,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                print("✅ Repository updated successfully")
                log_manager.log(f"Repository updated: {repo_name}")
            else:
                print(f"⚠️ Git pull failed: {result.stderr}")
        else:
            print(f"📥 Cloning repository...")
            result = subprocess.run(
                ["git", "clone", repo_url, local_path],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                print("✅ Repository cloned successfully")
                log_manager.log(f"Repository cloned: {repo_name}")
            else:
                print(f"❌ Git clone failed: {result.stderr}")
                return

        # Initialize deployment manager
        deploy_manager = DeploymentManager(local_path)
        
        # Install dependencies
        print("\n📦 Installing dependencies...")
        install_output = deploy_manager.install_dependencies()
        print(install_output)
        log_manager.log(f"Dependencies installation: {repo_name}")

        print("\n✅ Deployment completed successfully!")
        print(f"\n📁 Project location: {os.path.abspath(local_path)}")
        print("\n💡 Tip: Use the web interface (python app/routes.py) to run the project")
        log_manager.log(f"Deployment completed successfully: {repo_name}")
        
    except Exception as e:
        error_msg = f"Deployment failed: {e}"
        print(f"\n❌ {error_msg}")
        log_manager.log(error_msg)

if __name__ == "__main__":
    main()
