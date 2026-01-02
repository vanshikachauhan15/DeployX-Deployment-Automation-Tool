# Changelog

All notable changes to the Deployment Automation Tool project.

## [2.0.0] - 2024 (Current Version)

### 🔒 Security Improvements
- **Moved all secrets to environment variables** - No more hardcoded credentials in config.yaml
- **Added input validation and sanitization** - Prevents injection attacks and path traversal
- **Path traversal protection** - All file paths are validated before access
- **GitHub URL validation** - Validates GitHub URLs before processing
- **Created .gitignore** - Prevents accidental commit of sensitive files

### ✨ New Features
- **Health check endpoint** (`/health`) - Monitor application status
- **Project status endpoint** (`/status`) - Get list of all deployed projects
- **Comprehensive logging** - All actions are logged with timestamps
- **Better error messages** - User-friendly error messages throughout
- **Port validation** - Checks for free ports before assignment

### 🛠️ Code Improvements
- **Refactored utility functions** - Moved common functions to `core/utils.py`
- **Improved error handling** - Try-catch blocks with proper error logging
- **Better code organization** - Separated concerns and reduced duplication
- **Enhanced logging** - Structured logging with different log levels
- **Input sanitization** - All user inputs are sanitized before processing

### 📚 Documentation
- **Comprehensive README** - Complete setup and usage instructions
- **Environment variable template** - `.env.example` file for easy setup
- **Setup script** - Automated setup script for quick installation
- **Code comments** - Added docstrings and comments throughout

### 🐛 Bug Fixes
- **Fixed subprocess execution** - Improved subprocess handling with proper error capture
- **Fixed port finding** - Better port detection and assignment
- **Fixed environment variable loading** - Proper loading order and fallbacks
- **Fixed process management** - Better handling of running processes

### 🔧 Configuration
- **Environment-based config** - Configuration loaded from environment variables
- **Fallback to config.yaml** - Non-sensitive config still in YAML
- **Default environment** - Centralized default.env for all projects

## [1.0.0] - Initial Release

### Features
- Basic GitHub repository deployment
- Support for Python, Node.js, MERN, and Streamlit projects
- Web dashboard interface
- Dependency installation
- Project execution

---

## Upgrade Guide

### From 1.0.0 to 2.0.0

1. **Backup your configuration**:
   ```bash
   cp config.yaml config.yaml.backup
   cp core/default.env core/default.env.backup
   ```

2. **Create .env file**:
   ```bash
   cp .env.example .env
   ```

3. **Move secrets to .env**:
   - Copy `github_token` from `config.yaml` to `.env` as `GITHUB_TOKEN`
   - Copy `github_username` from `config.yaml` to `.env` as `GITHUB_USERNAME`
   - Remove these from `config.yaml`

4. **Update dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

5. **Test the application**:
   ```bash
   python app/routes.py
   ```

---

## Migration Notes

- Old `config.yaml` with hardcoded tokens will still work but is deprecated
- Environment variables take precedence over config.yaml
- All new deployments should use environment variables
- Log files location can be configured via `LOG_FILE` environment variable

