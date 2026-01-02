# Setting Up Environment Variables

## Quick Setup

1. **Create a `.env` file** in the project root:
   ```bash
   touch .env
   ```

2. **Add your GitHub credentials** to `.env`:
   ```env
   GITHUB_USERNAME=your_github_username
   GITHUB_TOKEN=your_github_personal_access_token
   ```

3. **Get a GitHub Token** (if you don't have one):
   - Go to: https://github.com/settings/tokens
   - Click "Generate new token (classic)"
   - Select `repo` scope
   - Copy the token and add it to `.env`

4. **Restart the application**

## Example .env file:
```env
GITHUB_USERNAME=vanshikachauhan15
GITHUB_TOKEN=ghp_your_token_here
DEPLOY_BASE_PATH=deployments
LOG_FILE=logs/deployment.log
```

## Note
The `.env` file is gitignored, so your credentials won't be committed to version control.
