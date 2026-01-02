from flask import session
from core.models import Project, Log,db
from core.models import db
from core.auth import auth
from core.auth_utils import login_required
from flask import render_template, request, jsonify, session,redirect
from datetime import datetime
import subprocess, os, yaml, signal, sys, socket, requests, time, logging, threading, queue, json

# Add parent directory to Python path to allow imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.deploy_manager import DeploymentManager
from core.log_manager import LogManager
from core.utils import sanitize_repo_name, validate_github_url, validate_path_safety, find_free_port
from dotenv import load_dotenv, dotenv_values
from core.repo_analyzer import analyze_repo
from flask import Blueprint

main = Blueprint("main", __name__)


#test code


# Load environment variables from .env file
load_dotenv()

# ---------------- AUTH + DB CONFIG ---------------
os.environ["FLASK_RUN_FROM_CLI"] = "false"

# Custom template filter for timestamp conversion
@main.app_template_filter('timestamp_to_date')
def timestamp_to_date(timestamp):
    try:
        return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M')
    except:
        return 'Unknown'

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def save_user_log(message):
    if "user_id" not in session:
        return
    log = Log(
        user_id=session["user_id"],
        message=message
    )
    db.session.add(log)
    db.session.commit()


# ---------------- LOAD CONFIG ---------------- 
# Get the base directory (parent of app directory)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
config_path = os.path.join(BASE_DIR, "config.yaml")

try:
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
except FileNotFoundError:
    logger.error(f"config.yaml not found at {config_path}!")
    config = {}
except yaml.YAMLError as e:
    logger.error(f"Error parsing config.yaml: {e}")
    config = {}

# Load from environment variables with fallback to config.yaml
deployments_dir = os.getenv("DEPLOY_BASE_PATH", config.get("deploy_base_path", "deployments"))
log_file = os.getenv("LOG_FILE", config.get("log_file", "logs/deployment.log"))
github_username = os.getenv("GITHUB_USERNAME", config.get("github_username", ""))
github_token = os.getenv("GITHUB_TOKEN", config.get("github_token", ""))

# Make paths absolute relative to BASE_DIR
if not os.path.isabs(deployments_dir):
    deployments_dir = os.path.join(BASE_DIR, deployments_dir)
if not os.path.isabs(log_file):
    log_file = os.path.join(BASE_DIR, log_file)

os.makedirs(deployments_dir, exist_ok=True)
os.makedirs(os.path.dirname(log_file), exist_ok=True)

# Initialize log manager
log_manager = LogManager(log_file)

manager = None
current_processes = []

# ---------------- FETCH GITHUB REPOS ---------------- 
def get_github_repos(username=None, token=None):
    """Fetch GitHub repositories for a given username."""
    # Use provided username/token or fall back to configured values
    target_username = username or github_username
    target_token = token or github_token
    
    if not target_username:
        logger.warning("GitHub username not provided")
        return []
    
    if not target_token:
        logger.warning("GitHub token not provided - API requests require authentication")
        return []
    
    try:
        url = f"https://api.github.com/users/{target_username}/repos"
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f"token {target_token}"
        }
        
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            repos_data = r.json()
            repos = [{"name": repo["name"], "full_name": repo["full_name"], "clone_url": repo["clone_url"]} for repo in repos_data]
            logger.info(f"Fetched {len(repos)} repositories from GitHub user: {target_username}")
            return repos
        elif r.status_code == 401:
            logger.error("GitHub authentication failed - check your GITHUB_TOKEN")
            logger.error("Token may be invalid or expired")
            return []
        elif r.status_code == 404:
            logger.error(f"GitHub user '{target_username}' not found")
            return []
        elif r.status_code == 403:
            logger.error("GitHub API rate limit exceeded - set GITHUB_TOKEN to increase limits")
            return []
        else:
            logger.warning(f"GitHub API returned status {r.status_code}: {r.text[:200]}")
            return []
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching GitHub repos: {e}")
        logger.error("Check your internet connection and GitHub API status")
        return []
    except Exception as e:
        logger.error(f"Unexpected error fetching repos: {e}")
        return []

@main.route("/")
def index():
    """Render the home/landing page."""
    return render_template("index.html")

@main.route("/dashboard")
@login_required
def dashboard():
    user_projects = Project.query.filter_by(
        user_id=session["user_id"]
    ).order_by(Project.created_at.desc()).all()
    deployed_repos = [p.name for p in user_projects]
    return render_template(
        "dashboard.html",
        deployed_repos=deployed_repos
    )

@main.route("/projects")
@login_required
def projects():
    user_projects = Project.query.filter_by(
        user_id=session["user_id"]
    ).all()

    return render_template("projects.html", projects=user_projects)

def get_folder_size(folder_path):
    """Get total size of a folder."""
    total = 0
    try:
        for dirpath, dirnames, filenames in os.walk(folder_path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if os.path.exists(fp):
                    total += os.path.getsize(fp)
    except:
        pass
    return total

@main.route("/logs")
@login_required
def logs_page():
    user_logs = Log.query.filter_by(
        user_id=session["user_id"]
    ).order_by(Log.timestamp.desc()).all()

    return render_template("logs.html", logs=user_logs)

@main.route("/fetch_repos", methods=["POST"])
def fetch_repos():
    """Fetch GitHub repositories for a given username."""
    try:
        data = request.get_json() or {}
        username = data.get("username", "").strip()
        token = data.get("token", "").strip()
        
        if not username:
            return jsonify({"error": "GitHub username is required", "repos": []}), 400
        
        if not token:
            return jsonify({
                "error": "GitHub Token is required! Please provide your GitHub Personal Access Token to fetch repositories.",
                "repos": []
            }), 400
        
        # Basic token format validation
        if not (token.startswith("ghp_") or token.startswith("github_pat_")):
            return jsonify({
                "error": "Invalid token format. GitHub tokens should start with 'ghp_' or 'github_pat_'",
                "repos": []
            }), 400
        
        # Extract username from URL if provided (e.g., https://github.com/username)
        if "github.com" in username:
            parts = username.split("github.com/")
            if len(parts) > 1:
                username = parts[-1].split("/")[0].strip()
        
        repos = get_github_repos(username=username, token=token)
        
        if repos:
            return jsonify({
                "repos": repos,
                "username": username,
                "count": len(repos)
            })
        else:
            return jsonify({
                "error": f"No repositories found for user '{username}' or API error occurred",
                "repos": [],
                "username": username
            }), 404
            
    except Exception as e:
        logger.error(f"Error in fetch_repos endpoint: {e}")
        return jsonify({"error": str(e), "repos": []}), 500

@main.route("/status", methods=["GET"])
@login_required
def project_status():
    user_projects = Project.query.filter_by(
        user_id=session["user_id"]
    ).all()

    return jsonify({
        "projects": [
            {"name": p.name, "path": p.path}
            for p in user_projects
        ],
        "total": len(user_projects)
    })

@main.route("/delete_project", methods=["POST"])
@login_required
def delete_project():
    data = request.get_json() or {}
    repo_name = data.get("repo", "").strip()   # ❌ sanitize HATA DIYA

    if not repo_name:
        return jsonify({"output": "❌ Invalid project name"}), 400

    project = Project.query.filter(
        Project.user_id == session["user_id"],
        Project.name == repo_name               # ✅ EXACT MATCH
    ).first()

    if not project:
        return jsonify({"output": "❌ Project not found"}), 404

    # 🧹 Delete folder
    try:
        if project.path and os.path.exists(project.path):
            import shutil
            shutil.rmtree(project.path)
    except Exception as e:
        logger.error(f"Folder delete failed: {e}")

    # 🧹 Delete DB entry
    db.session.delete(project)
    db.session.commit()

    save_user_log(f"Project deleted: {repo_name}")

    return jsonify({
        "output": f"🗑️ Project '{repo_name}' deleted successfully"
    })

@main.route("/session-check")
def session_check():
    if "user_id" in session:
        return render_template("session_choice.html")
    return redirect("/login")

# ---------------- DEPLOY REPO ---------------- 
@main.route("/deploy_repo", methods=["POST"])
@login_required
def deploy_repo():
    """Deploy a repository from GitHub."""
    try:
        data = request.get_json() or {}
        custom_url = data.get("custom_url", "").strip()
        repo_name = data.get("repo", "").strip()

        if custom_url:
            # Validate GitHub URL
            if not validate_github_url(custom_url):
                return jsonify({"output": "❌ Invalid GitHub URL format!"}), 400

            # Extract repo name
            local_folder = custom_url.rstrip("/").split("/")[-1].replace(".git", "")
            local_folder = sanitize_repo_name(local_folder)

            if not local_folder:
                return jsonify({"output": "❌ Invalid repository name!"}), 400

            user_folder = f"user_{session['user_id']}"
            user_base_path = os.path.join(deployments_dir, user_folder)
            os.makedirs(user_base_path, exist_ok=True)

            local_path = os.path.join(user_base_path, local_folder)

            # Safety check
            if not validate_path_safety(deployments_dir, local_path):
                return jsonify({"output": "❌ Invalid path!"}), 400

            # SAME USER duplicate check
            existing_project = Project.query.filter_by(
                user_id=session["user_id"],
                name=local_folder
            ).first()

            if existing_project:
                return jsonify({
                    "output": "⚠️ You have already deployed this project!"
                })

            # Clone repo
            log_manager.log(f"Cloning repository: {custom_url}")
            result = subprocess.run(
                ["git", "clone", custom_url, local_path],
                capture_output=True,
                text=True,
                timeout=300
            )

            # ❌ CLONE FAILED
            if result.returncode != 0:
                error_msg = result.stderr or result.stdout or "Unknown error"
                return jsonify({
                    "output": f"❌ Git clone failed:<br><pre>{error_msg}</pre>"
                }), 500

            # ✅ CLONE SUCCESS → SAVE TO DB
            project = Project(
                user_id=session["user_id"],
                name=local_folder,
                path=local_path,
                created_at=datetime.utcnow()
            )
            db.session.add(project)
            db.session.commit()

            save_user_log(f"Repository deployed: {local_folder}")

            return jsonify({
                "output": f"✅ Repo '{local_folder}' deployed successfully!"
            })

        if not repo_name:
            return jsonify({"output": "❌ Repo name missing!"}), 400

        # Sanitize repo name
        repo_name = sanitize_repo_name(repo_name)
        # 🔒 Check if SAME USER already deployed this repo
        existing_project = Project.query.filter_by(
            user_id=session["user_id"],
            name=repo_name
        ).first()

        if existing_project:
            return jsonify({
                "output": "⚠️ You have already deployed this project!"
            })

        if not repo_name:
            return jsonify({"output": "❌ Invalid repository name!"}), 400

        # Get GitHub username from request or use configured one
        request_username = data.get("github_username", "").strip()
        target_username = request_username or github_username
        
        if not target_username:
            return jsonify({"output": "❌ GitHub username not provided! Please enter a GitHub username."}), 400

        user_folder = f"user_{session['user_id']}"
        user_base_path = os.path.join(deployments_dir, user_folder)
        os.makedirs(user_base_path, exist_ok=True)

        local_path = os.path.join(user_base_path, repo_name)
        
        # Prevent path traversal
        if not validate_path_safety(deployments_dir, local_path):
            logger.error(f"Path traversal attempt detected: {local_path}")
            return jsonify({"output": "❌ Invalid path!"}), 400

        repo_url = f"https://github.com/{target_username}/{repo_name}.git"
        log_manager.log(f"Cloning repository: {repo_url}")
        
        result = subprocess.run(
            ["git", "clone", repo_url, local_path],
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode == 0:
            logger.info(f"Successfully cloned repository: {repo_name}")
            log_manager.log(f"Repository deployed: {repo_name}")
            project = Project(
                user_id=session["user_id"],
                name=repo_name,
                path=local_path,
                created_at=datetime.utcnow()
            )
            db.session.add(project)
            db.session.commit()
            save_user_log(f"Repository deployed: {repo_name}")
            return jsonify({"output": f"✅ Repo '{repo_name}' deployed successfully!"})
        else:
            error_msg = result.stderr or "Unknown error"
            logger.error(f"Git clone failed: {error_msg}")
            return jsonify({"output": f"❌ Failed to clone repository: {error_msg[:200]}"}), 500

    except subprocess.TimeoutExpired:
        logger.error("Git clone timed out")
        return jsonify({"output": "❌ Clone operation timed out!"}), 500
    except Exception as e:
        logger.error(f"Error deploying repo: {e}")
        log_manager.log(f"Error deploying repo: {e}")
        return jsonify({"output": f"❌ Error: {str(e)[:200]}"}), 500

# ---------------- INSTALL DEPENDENCIES ---------------- 
@main.route("/install_deps", methods=["POST"])
@login_required
def install_dependencies():
    """Install dependencies for a deployed project."""
    try:
        data = request.get_json() or {}
        repo_name = data.get("repo", "").strip()
        
        if not repo_name:
            return jsonify({"output": "❌ Repo name missing!"}), 400

        # Sanitize and validate repo name
        repo_name = sanitize_repo_name(repo_name)
        if not repo_name:
            return jsonify({"output": "❌ Invalid repository name!"}), 400
        project = Project.query.filter_by(
            user_id=session["user_id"],
            name=repo_name
        ).first()

        if not project:
            return jsonify({"output": "❌ Unauthorized project access"}), 403

        project_path = project.path
        
        # Prevent path traversal
        if not validate_path_safety(deployments_dir, project_path):
            logger.error(f"Path traversal attempt detected: {project_path}")
            return jsonify({"output": "❌ Invalid path!"}), 400
        
        if not os.path.exists(project_path):
            logger.warning(f"Project path not found: {project_path}")
            return jsonify({"output": "❌ Project not found! Deploy it first."}), 404

        logger.info(f"Installing dependencies for: {repo_name}")
        log_manager.log(f"Installing dependencies for: {repo_name}")
        
        manager = DeploymentManager(project_path)
        output = manager.install_dependencies()
        save_user_log(f"Dependencies installed for project: {repo_name}")
        return jsonify({"output": output})
        
    except Exception as e:
        logger.error(f"Error installing dependencies: {e}")
        log_manager.log(f"Error installing dependencies: {e}")
        return jsonify({"output": f"❌ Error: {str(e)[:200]}"}), 500

# ---------------- RUN PROJECT ----------------
@main.route("/run_project", methods=["POST"])
@login_required
def run_project():
    try:
        data = request.get_json() or {}
        repo_name = sanitize_repo_name(data.get("repo", "").strip())
        project = Project.query.filter_by(
            user_id=session["user_id"],
            name=repo_name
        ).first()

        if not project:
            return jsonify({"output": "❌ Unauthorized project access"}), 403

        if not repo_name:
            return jsonify({"output": "❌ Repo name missing / invalid"}), 400

        project_path = project.path

        if not validate_path_safety(deployments_dir, project_path):
            return jsonify({"output": "❌ Invalid path"}), 400

        if not os.path.exists(project_path):
            return jsonify({"output": "❌ Project not found"}), 404

        logger.info(f"Running project: {repo_name}")
        log_manager.log(f"Starting project: {repo_name}")
        save_user_log(f"Project started: {repo_name}")

        # =====================================================
        # 🧠 STEP 0: ANALYZE PROJECT BEFORE RUN (AI-READY)
        # =====================================================
        analysis = analyze_repo(project_path)

        if not analysis["auto_runnable"]:
            ai_text = None

            if os.getenv("ENABLE_AI") == "true" and os.getenv("OPENAI_API_KEY"):
                try:
                    from core.ai_analyzer import ai_explain_repo
                    ai_text = ai_explain_repo(analysis, repo_name)
                except Exception as e:
                    logger.warning(f"AI explanation failed: {e}")

            output = (
                "❌ Project cannot be auto-run<br><br>"
                "<b>Issues:</b><br>" +
                "<br>".join(f"- {i}" for i in analysis["issues"]) +
                "<br><br><b>Solutions:</b><br>" +
                "<br>".join(f"- {s}" for s in analysis["solutions"])
            )

            if ai_text:
                output += (
                    "<br><br><b>🤖 AI Explanation:</b><br>"
                    f"<pre>{ai_text}</pre>"
                )
            save_user_log(f"Auto-run failed for project: {repo_name}")
            return jsonify({"output": output}), 400

        # =====================================================
        # 1️⃣ PYTHON / STREAMLIT PROJECT
        # =====================================================
        python_exec = sys.executable
        python_files = [
            f for f in os.listdir(project_path)
            if f.endswith(".py") and os.path.isfile(os.path.join(project_path, f))
        ]

        for py_file in python_files:
            file_path = os.path.join(project_path, py_file)
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read().lower()

            # STREAMLIT
            if "streamlit" in content:
                env = os.environ.copy()
                env["STREAMLIT_SERVER_HEADLESS"] = "true"
                env["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"

                proc = subprocess.Popen(
                    [python_exec, "-m", "streamlit", "run", py_file, "--server.headless", "true"],
                    cwd=project_path,
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True
                )
                current_processes.append(proc)

                return jsonify({
                    "output": (
                        "✅ Streamlit app running<br>"
                        "🌐 <a href='http://localhost:8501' target='_blank'>http://localhost:8501</a>"
                    )
                })

        # NORMAL PYTHON APP
        if python_files:
            port = find_free_port()
            env = os.environ.copy()
            env["PORT"] = str(port)

            proc = subprocess.Popen(
                [python_exec, python_files[0]],
                cwd=project_path,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )
            current_processes.append(proc)

            return jsonify({
                "output": f"✅ Python app running at http://localhost:{port}"
            })

        # =====================================================
        # 2️⃣ MERN / NODE PROJECT
        # =====================================================
        server_dir = None
        client_dir = None

        for root, dirs, files in os.walk(project_path):
            if "package.json" in files and "node_modules" not in root:
                folder = os.path.basename(root).lower()
                if folder == "server" and not server_dir:
                    server_dir = root
                elif folder == "client" and not client_dir:
                    client_dir = root
                elif not server_dir:
                    server_dir = root

        if not server_dir:
            return jsonify({"output": "❌ No Node / MERN backend detected"}), 400

        backend_port = find_free_port()

        env = os.environ.copy()
        env["PORT"] = str(backend_port)

        env_file = os.path.join(server_dir, ".env")
        if os.path.exists(env_file):
            for k, v in dotenv_values(env_file).items():
                if v:
                    env[k] = str(v)

        # -----------------------------------------------------
        # Detect start command
        # -----------------------------------------------------
        with open(os.path.join(server_dir, "package.json"), "r") as f:
            pkg = json.load(f)

        scripts = pkg.get("scripts", {})

        if "dev" in scripts:
            start_cmd = ["npm", "run", "dev"]
        elif "start" in scripts:
            start_cmd = ["npm", "start"]
        else:
            return jsonify({
                "output": "❌ No start/dev script found in backend package.json"
            }), 400

        # -----------------------------------------------------
        # START BACKEND
        # -----------------------------------------------------
        backend_proc = subprocess.Popen(
            start_cmd,
            cwd=server_dir,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        current_processes.append(backend_proc)

        time.sleep(5)

        # -----------------------------------------------------
        # FRONTEND (OPTIONAL)
        # -----------------------------------------------------
        frontend_url = ""
        if client_dir:
            frontend_proc = subprocess.Popen(
                ["npm", "run", "dev"],
                cwd=client_dir,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )
            current_processes.append(frontend_proc)
            frontend_url = "http://localhost:5173"

        return jsonify({
            "output": (
                "🚀 MERN Project Running<br>"
                f"🟢 Backend: <a href='http://localhost:{backend_port}' target='_blank'>http://localhost:{backend_port}</a><br>"
                + (f"🟢 Frontend: <a href='{frontend_url}' target='_blank'>{frontend_url}</a>" if frontend_url else "")
            )
        })

    except Exception as e:
        logger.error(f"Error running project: {e}")
        log_manager.log(f"Error running project: {e}")
        return jsonify({
            "output": f"❌ Error running project: {str(e)[:200]}"
        }), 500
   

# ---------------- STOP PROJECT ---------------- 
@main.route("/stop_project", methods=["POST"])
@login_required
def stop_project():
    """Stop all running projects."""
    try:
        stopped_count = 0
        for proc in current_processes:
            try:
                if proc.poll() is None:
                    os.kill(proc.pid, signal.SIGTERM)
                    stopped_count += 1
            except ProcessLookupError:
                # Process already terminated
                pass
            except Exception as e:
                logger.warning(f"Error stopping process {proc.pid}: {e}")
        
        current_processes.clear()
        logger.info(f"Stopped {stopped_count} processes")
        log_manager.log(f"Stopped {stopped_count} running projects")
        save_user_log("Stopped all running projects")        
        return jsonify({"output": f"🛑 All projects stopped successfully! ({stopped_count} processes)"})
    except Exception as e:
        logger.error(f"Error stopping projects: {e}")
        return jsonify({"output": f"❌ Error stopping projects: {str(e)[:200]}"}), 500

@main.app_errorhandler(404)
def not_found(error):
    return jsonify({"output": "❌ Endpoint not found"}), 404

@main.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "deployments_dir": deployments_dir,
        "running_processes": len([p for p in current_processes if p.poll() is None])
    })

@main.app_errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return jsonify({"output": "❌ Internal server error"}), 500


