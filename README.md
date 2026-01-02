# 🚀 DeployX – Deployment Automation Tool


DeployX is a full-stack Flask-based deployment automation platform that allows users to deploy, manage, and run GitHub repositories through a modern web dashboard.
It supports Python, Streamlit, Node.js, MERN, and custom GitHub repositories with automatic dependency installation, project detection, and process management.

## ✨ Features

- User Authentication (Signup / Login / Logout)
- Session handling with account switching
- Deploy repositories from GitHub
- Deploy using custom GitHub repository URLs
- Automatic project type detection
- Automatic dependency installation (pip / npm)
- One-click run & stop projects
- Auto free-port detection
- Project dashboard with logs
- Secure environment variable handling
- Clean and modern UI (Glassmorphism design)

## 🧠 Supported Project Types

- Python Applications  
- Streamlit Dashboards  
- Node.js Backends  
- MERN Stack Applications  
- React Frontend Projects  
- Custom GitHub Repositories  

---

## 🛠 Tech Stack

- Backend: Flask, SQLAlchemy
- Frontend: Jinja2, TailwindCSS
- Authentication: Session-based auth
- Database: SQLite
- Deployment: Subprocess management
- Security: Environment variables & path validation

## 📁 Project Structure

```
deployment_automation_tool/
├── app/
│   ├── routes.py          # Flask routes and web interface
│   └── templates/
│       
├── core/
│ ├── auth.py
│ ├── auth_utils.py
│ ├── models.py
│ ├── deploy_manager.py
│ ├── repo_analyzer.py
│ ├── utils.py
│ └── default.env
│
├── instance/
│ └── app.db
│
├── deployments/
├── logs/
│
├── .env.example
├── SETUP_ENV.md
├── requirements.txt
├── run.py
└── README.md
```

## 🔐 Authentication Flow
Signup → Login → Home
Home → Dashboard / Projects
Login (while logged in) → Session Check
Logout → Login
This flow prevents accidental session override and allows smooth account switching.
---

## ⚙️ Environment Setup

### 1. Create `.env` file

```bash
cp .env.example .env
```

### 2. Add credentials

GITHUB_USERNAME=your_github_username
GITHUB_TOKEN=your_github_personal_access_token
DEPLOY_BASE_PATH=deployments
LOG_FILE=logs/deployment.log
OPENAI_API_KEY=your_openai_key_here
ENABLE_AI=false

.env is ignored by Git for security reasons.

🚀 How to Run
Start the application
```bash
python run.py
```

Open in browser:
```bash
http://localhost:5000
```

How It Works (Web UI)

Signup or Login
Fetch GitHub repositories OR paste a custom GitHub repo URL
Deploy the project
Install dependencies
Run the project
Access the live URL
Stop or delete the project anytime

Security Practices

Secrets stored only in .env
.env and config.yaml are git-ignored
Input validation & sanitization
Path traversal protection
User-scoped deployments

Logs & Monitoring

Logs stored in logs/deployment.log
User activity stored in database
Console + file logging enabled

Reset Database (For Demo)
```bash
rm instance/app.db
python run.py
```
A fresh database will be created automatically.

Future Enhancements

 **Docker Support**  
  Run deployed projects inside Docker containers for better isolation and consistency.

- **Better AI Suggestions**  
  Improve AI explanations for failed runs with clearer fixes and commands.

- **Auto Deploy on GitHub Push**  
  Automatically redeploy projects when new code is pushed to GitHub.

- **Role-Based Access Control**  
  Add roles like Admin and User for better access management.

License

This project is open-source and intended for learning and demonstration purposes.
