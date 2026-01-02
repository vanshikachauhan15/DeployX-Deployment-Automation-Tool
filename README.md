# 🚀 Deployment Automation Tool

A powerful Flask-based web application that automates the deployment and management of GitHub repositories. Supports Python, Node.js/MERN, Streamlit, and Jupyter projects with automatic dependency installation and project detection.

## ✨ Features

- **Multi-Source Deployment**: Deploy from your GitHub account or custom GitHub URLs
- **Automatic Project Detection**: Automatically detects Python, Streamlit, Node.js, MERN, and Jupyter projects
- **Dependency Management**: Automatically installs dependencies (pip, npm)
- **Port Management**: Automatically finds and assigns free ports
- **Environment Variables**: Centralized environment variable management
- **Web Dashboard**: Beautiful, modern web interface for easy management
- **Process Management**: Start and stop projects with ease
- **Comprehensive Logging**: Track all deployment activities

## 📋 Prerequisites

- Python 3.8+
- Git
- Node.js and npm (for Node.js/MERN projects)
- pip (Python package manager)

## 🛠️ Installation

1. **Clone the repository**:
   ```bash
   git clone <your-repo-url>
   cd deployment_automation_tool
   ```

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and add your configuration:
   ```env
   GITHUB_USERNAME=your_github_username
   GITHUB_TOKEN=your_github_personal_access_token
   DEPLOY_BASE_PATH=deployments
   LOG_FILE=logs/deployment.log
   ```

4. **Configure GitHub Token** (optional but recommended):
   - Go to GitHub Settings → Developer settings → Personal access tokens
   - Generate a new token with `repo` scope
   - Add it to your `.env` file

5. **Set up default environment variables** (for deployed projects):
   - Edit `core/default.env` with your database credentials, API keys, etc.
   - This file will be used by all deployed projects

## 🚀 Usage

### Web Interface (Recommended)

1. **Start the Flask application**:
   ```bash
   python -m app.routes
   # or
   python app/routes.py
   ```

2. **Open your browser**:
   ```
   http://localhost:5000
   ```

3. **Deploy a repository**:
   - Select a repository from your GitHub account, or
   - Enter a custom GitHub URL (e.g., `https://github.com/owner/repo`)
   - Click "Deploy Repo"

4. **Install dependencies**:
   - Click "Install Dependencies" after deployment

5. **Run the project**:
   - Click "Run Project" to start the application
   - The dashboard will show the URLs where your project is running

6. **Stop projects**:
   - Click "Stop Project" to stop all running processes

### Command Line Interface

You can also use the CLI tool:

```bash
python main.py
```

This will:
1. List your GitHub repositories
2. Let you select one to deploy
3. Automatically clone and deploy it

## 📁 Project Structure

```
deployment_automation_tool/
├── app/
│   ├── routes.py          # Flask routes and web interface
│   └── templates/
│       └── dashboard.html  # Web dashboard UI
├── core/
│   ├── deploy_manager.py  # Core deployment logic
│   ├── log_manager.py     # Logging functionality
│   ├── ai_analyzer.py     # AI analysis (future feature)
│   ├── utils.py           # Utility functions
│   └── default.env        # Default environment variables
├── deployments/           # Deployed repositories (created automatically)
├── logs/                  # Log files (created automatically)
├── config.yaml            # Configuration file
├── .env.example           # Environment variables template
├── requirements.txt       # Python dependencies
├── main.py               # CLI entry point
└── README.md             # This file
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the root directory with:

- `GITHUB_USERNAME`: Your GitHub username
- `GITHUB_TOKEN`: Your GitHub personal access token
- `DEPLOY_BASE_PATH`: Directory where repositories will be deployed (default: `deployments`)
- `LOG_FILE`: Path to log file (default: `logs/deployment.log`)

### config.yaml

The `config.yaml` file contains non-sensitive configuration:

```yaml
log_file: "logs/deployment.log"
deploy_base_path: "deployments"
```

**Note**: Sensitive values like GitHub tokens should be set via environment variables, not in `config.yaml`.

### core/default.env

This file contains default environment variables that will be loaded for all deployed projects. Include:

- Database connection strings
- API keys
- JWT secrets
- Port configurations
- Other project-specific variables

## 🎯 Supported Project Types

### Python Projects
- Flask/FastAPI applications
- Detects: `app.py`, `main.py`, `run.py`
- Automatically installs from `requirements.txt`

### Streamlit Projects
- Streamlit applications
- Detects: `streamlit_app.py` or files containing "streamlit"
- Runs on port 8501

### Node.js/MERN Projects
- Full-stack applications with `server`/`backend` and `client`/`frontend` directories
- Automatically installs npm dependencies
- Backend runs on auto-assigned port (5001+)
- Frontend runs on port 5173 (Vite default)

### Jupyter Notebooks
- Machine Learning projects with `.ipynb` files
- Launches Jupyter Notebook server

## 🔒 Security Features

- **Input Validation**: All inputs are sanitized to prevent injection attacks
- **Path Traversal Protection**: Prevents directory traversal attacks
- **Environment Variable Security**: Sensitive credentials stored in `.env` (not in code)
- **Process Isolation**: Projects run in isolated subprocesses

## 📝 Logging

All deployment activities are logged to:
- Console output (with timestamps)
- Log file (configured in `LOG_FILE` environment variable)

Log entries include:
- Deployment start/completion
- Dependency installation
- Project startup/shutdown
- Errors and warnings

## 🐛 Troubleshooting

### GitHub Authentication Issues
- Ensure `GITHUB_TOKEN` is set in `.env`
- Verify token has `repo` scope
- Check token hasn't expired

### Port Already in Use
- The tool automatically finds free ports
- If issues persist, check for processes using ports 5001-5200

### Dependency Installation Fails
- Ensure `pip` and `npm` are installed and in PATH
- Check internet connection
- Verify `requirements.txt` or `package.json` exists

### Project Won't Start
- Check logs in `logs/deployment.log`
- Verify environment variables in `core/default.env`
- Ensure all dependencies are installed

## 🚧 Future Enhancements

- [ ] Docker containerization support
- [ ] Project health monitoring
- [ ] CI/CD integration
- [ ] AI-powered project analysis
- [ ] Multiple concurrent deployments
- [ ] Webhook support for auto-deployment
- [ ] Project status dashboard
- [ ] Log viewing in web interface

## 📄 License

This project is open source and available for use.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## ⚠️ Important Notes

1. **Security**: Never commit `.env` files or `config.yaml` with sensitive data to version control
2. **Ports**: Ensure ports 5000-5200 are available for project deployment
3. **Permissions**: Some projects may require additional system permissions
4. **Resource Usage**: Running multiple projects simultaneously may consume significant resources

## 📞 Support

For issues, questions, or contributions, please open an issue on the GitHub repository.

---

**Made with ❤️ for developers who want to deploy faster**

