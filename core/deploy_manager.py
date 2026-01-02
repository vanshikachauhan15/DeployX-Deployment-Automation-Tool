import subprocess
import os
import psutil
import socket
import time
import glob
from dotenv import dotenv_values

class DeploymentManager:
    def __init__(self, project_path):
        self.project_path = project_path
        self.processes = []
        self.port = None

        # ✅ Ensure Node.js in PATH (Windows only)
        if os.name == "nt":  # Windows
            os.environ["PATH"] += os.pathsep + r"C:\Program Files\nodejs"

        # ✅ Always load environment variables only from core/default.env (initial load)
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        default_env_path = os.path.join(BASE_DIR, "core", "default.env")

        if os.path.exists(default_env_path):
            dotenv_vars = dotenv_values(default_env_path)
            for key, val in dotenv_vars.items():
                if val is not None:
                    os.environ[key.strip()] = str(val).strip()
            print(f"✅ Loaded environment only from {default_env_path}")
        else:
            print("⚠️ core/default.env not found — environment may be incomplete.")

    # ============================================================
    # Helper: Load env before backend run
    # ============================================================
    def _load_core_env(self):
        """Force load environment variables from core/default.env right before run."""
        env_path = os.path.join(self.project_path, "core", "default.env")
        if os.path.exists(env_path):
            print(f"🔧 Reloading environment from {env_path}")
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        if "=" in line:
                            key, value = line.split("=", 1)
                            os.environ[key.strip()] = value.strip().strip('"').strip("'")
            print("✅ Environment refreshed successfully before run.")
        else:
            print("⚠️ core/default.env missing during reload")

    # ============================================================
    # (NEW) Helper to return env dict for subprocess (guarantees .env loading)
    # ============================================================
    def _prepare_env(self):
        """Combine system env + core/default.env → ready for subprocess."""
        env = os.environ.copy()
        env_path = os.path.join(self.project_path, "core", "default.env")
        if os.path.exists(env_path):
            dotenv_vars = dotenv_values(env_path)
            for key, val in dotenv_vars.items():
                if val is not None:
                    env[key.strip()] = str(val).strip()
            print("🧩 Merged environment from core/default.env for subprocess.")
        else:
            print("⚠️ core/default.env not found during prepare_env.")
        return env

    # ============================================================
    # Find free port
    # ============================================================
    def find_free_port(self, start=5000, end=5100):
        for port in range(start, end):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                try:
                    s.bind(("", port))
                    return port
                except OSError:
                    continue
        raise RuntimeError("❌ No available ports found!")

    # ============================================================
    # Install dependencies (Python + Node + ML)
    # ============================================================
    def install_dependencies(self):
        repo = self.project_path
        output_logs = []

        def run_cmd(cmd, cwd=None):
            try:
                subprocess.check_call(cmd, cwd=cwd, shell=True)
                return True
            except subprocess.CalledProcessError:
                return False

        # ---------- Python ----------
        req_file = os.path.join(repo, "requirements.txt")
        if os.path.exists(req_file):
            output_logs.append("📦 Detected Python project.")
            if run_cmd(f'pip install -r "{req_file}"'):
                output_logs.append("✅ Python dependencies installed.")
            else:
                output_logs.append("❌ Failed to install Python dependencies.")
            return "\n".join(output_logs)

        # ---------- Node / MERN ----------
        subfolders = self._find_package_json_dirs(repo)
        if subfolders:
            output_logs.append("📂 Detected Node.js / MERN project.")
            for path in subfolders:
                output_logs.append(f"📦 Installing Node dependencies in {path}...")

                try:
                    if os.path.exists(os.path.join(path, "package-lock.json")):
                        if not run_cmd("npm ci", cwd=path):
                            output_logs.append("⚠️ npm ci failed, falling back to npm install")
                            run_cmd("npm install", cwd=path)
                    else:
                        run_cmd("npm install", cwd=path)

                    output_logs.append(f"✅ Node dependencies installed in {path}")
                except Exception as e:
                    output_logs.append(f"❌ Failed to install dependencies in {path}: {e}")

            return "\n".join(output_logs)

        # ---------- Machine Learning / Notebook ----------
        notebooks = glob.glob(os.path.join(repo, "*.ipynb"))
        if notebooks:
            output_logs.append("🧠 Detected Machine Learning project.")
            run_cmd("pip install notebook pandas numpy scikit-learn matplotlib seaborn", cwd=repo)
            output_logs.append("✅ Notebook environment ready.")
            return "\n".join(output_logs)

        return "⚠️ No requirements.txt or package.json found.\n✅ Nothing to install."


    # ============================================================
    # Find package.json directories
    # ============================================================
    def _find_package_json_dirs(self, repo):
        package_dirs = []
        for root, dirs, files in os.walk(repo):
            if "node_modules" in root or root.startswith("."):
                continue
            if "package.json" in files:
                package_dirs.append(root)
        return package_dirs

    # ============================================================
    # Run project (Streamlit / Python / MERN / ML / server.js)
    # ============================================================
    def run_project(self):
        repo = self.project_path
        env = self._prepare_env()  # ✅ Combine system + default.env

        self.port = self.find_free_port()
        env["PORT"] = str(self.port)

        # ✅ Absolute path of default.env (core/default.env)
        default_env_path = os.path.join(repo, "core", "default.env")
        if os.path.exists(default_env_path):
            env["DOTENV_CONFIG_PATH"] = default_env_path
            print(f"🟢 Using default environment file: {default_env_path}")
        else:
            print("⚠️ No default.env found in /core, skipping.")

        # ============================
        # ✅ Auto-detect server.js
        # ============================
        server_file = None
        if os.path.exists(os.path.join(repo, "server", "server.js")):
            server_file = os.path.join(repo, "server", "server.js")
        elif os.path.exists(os.path.join(repo, "server.js")):
            server_file = os.path.join(repo, "server.js")

        if server_file:
            print(f"⚙️ Detected Node backend file: {server_file}")
            self._update_env_file(os.path.dirname(server_file), self.port)
            proc = subprocess.Popen(
                ["node", server_file],
                cwd=repo,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )
            self.processes.append(proc)
            print(f"🚀 Backend started successfully at http://localhost:{self.port}")
            return f"http://127.0.0.1:{self.port}"

        # ============================
        # ✅ Detect Python/Streamlit projects
        # ============================
        python_files = [f for f in os.listdir(repo) if f.endswith(".py")]
        package_dirs = self._find_package_json_dirs(repo)
        notebooks = glob.glob(os.path.join(repo, "*.ipynb"))

        if python_files:
            for file in python_files:
                file_path = os.path.join(repo, file)
                content = open(file_path, "r", encoding="utf-8", errors="ignore").read().lower()
                if "streamlit" in content:
                    print(f"⚙️ Detected Streamlit project: {file}")
                    proc = subprocess.Popen(
                        ["streamlit", "run", file],
                        cwd=repo,
                        env=env,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True
                    )
                    self.processes.append(proc)
                    return "http://127.0.0.1:8501"
                elif "flask" in content or "fastapi" in content:
                    print(f"⚙️ Detected Python Flask/FastAPI app: {file}")
                    proc = subprocess.Popen(
                        ["python", file],
                        cwd=repo,
                        env=env,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True
                    )
                    self.processes.append(proc)
                    return f"http://127.0.0.1:{self.port}"

        # ============================
        # ✅ Detect MERN projects
        # ============================
        package_dirs = self._find_package_json_dirs(repo)
        notebooks = glob.glob(os.path.join(repo, "*.ipynb"))

        if package_dirs:
            server_dir, client_dir = None, None
            for path in package_dirs:
                lower = path.lower()
                folder = os.path.basename(path).lower()
                if folder == "server":
                    server_dir = path
                elif folder == "client":
                    client_dir = path

            if not server_dir and not client_dir:
                return "⚠️ Node project found, but missing client/server structure."

            # 🟢 Frontend (Vite)
            if client_dir:
                print(f"⚙️ Starting frontend (Vite) from {client_dir}")
                client_proc = subprocess.Popen(
                    ["npm", "run", "dev"],
                    cwd=client_dir,
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True
                )
                self.processes.append(client_proc)
                print("🕐 Waiting for frontend to start...")
                time.sleep(8)

            # 🟢 Backend (Express)
            if server_dir:
                print(f"⚙️ Starting backend (Express) from {server_dir}")
                self._update_env_file(server_dir, self.port)
                backend_proc = subprocess.Popen(
                    ["npm", "run", "start"],
                    cwd=server_dir,
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True
                )
                self.processes.append(backend_proc)
                print("🕐 Waiting for backend to start...")
                time.sleep(5)

            print("\n🚀 MERN project running successfully!")
            print("🟢 Frontend: http://localhost:5173")
            print(f"🟢 Backend: http://localhost:{self.port}")
            return "http://127.0.0.1:5173"

        # ============================
        # ✅ Detect ML / Jupyter
        # ============================
        if notebooks:
            print(f"🧠 Detected Machine Learning project with {len(notebooks)} notebook(s).")
            port = self.find_free_port()
            print(f"⚙️ Launching Jupyter Notebook on port {port}...")
            subprocess.Popen(
                [
                    "jupyter", "notebook",
                    "--no-browser",
                    f"--port={port}",
                    "--NotebookApp.token=''",
                    "--NotebookApp.password=''"
                ],
                cwd=repo,
                env=env,
                shell=True
            )
            print(f"💻 Notebook running at http://localhost:{port}")
            return f"http://127.0.0.1:{port}"

        return "❌ No main file or valid start configuration found."

    # ============================================================
    # Update .env file PORT
    # ============================================================
        
    def _update_env_file(self, folder, new_port):
       
        env_path = os.path.join(folder, ".env")
        try:
            # Ensure .env exists — if not, create minimal
            if not os.path.exists(env_path):
                with open(env_path, "w") as f:
                    f.write(f"PORT={new_port}\n")
                return

            updated = False
            new_lines = []

            # ✅ Read existing lines safely
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip().startswith("PORT="):
                        new_lines.append(f"PORT={new_port}\n")
                        updated = True
                    else:
                        new_lines.append(line)

            # ✅ Append if no PORT found
            if not updated:
                new_lines.append(f"\nPORT={new_port}\n")

            # ✅ Rewrite file safely
            with open(env_path, "w", encoding="utf-8") as f:
                f.writelines(new_lines)

            print(f"✅ Updated only PORT in {env_path}, rest of .env preserved.")
        except Exception as e:
            print(f"⚠️ Failed to update .env file safely: {e}")

    # ============================================================
    # Stop all processes
    # ============================================================
    def stop_project(self):
        for proc in self.processes:
            if proc.poll() is None:
                try:
                    proc.terminate()
                    proc.wait(timeout=5)
                except Exception:
                    pass
        self.processes.clear()
        for p in psutil.process_iter(attrs=["pid", "name", "cmdline"]):
            try:
                cmd = " ".join(p.info["cmdline"])
                if any(word in cmd for word in ["main", "app", "server.js", "index.js", "jupyter"]) and (
                    "python" in cmd or "node" in cmd
                ):
                    os.kill(p.info["pid"], 9)
            except Exception:
                continue
        return "🛑 All running projects stopped successfully!"
