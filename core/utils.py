"""
Utility functions for the deployment automation tool.
"""
import os
import re
import socket
from typing import Optional, Tuple


def sanitize_repo_name(repo_name: str) -> Optional[str]:
    """
    Sanitize repository name to prevent path traversal attacks.
    
    Args:
        repo_name: The repository name to sanitize
        
    Returns:
        Sanitized repository name or None if invalid
    """
    if not repo_name:
        return None
    # Remove any path separators and dangerous characters
    repo_name = re.sub(r'[^a-zA-Z0-9._-]', '', repo_name)
    # Prevent path traversal
    if '..' in repo_name or '/' in repo_name or '\\' in repo_name:
        return None
    return repo_name


def validate_github_url(url: str) -> bool:
    """
    Validate GitHub URL format.
    
    Args:
        url: The GitHub URL to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not url:
        return False
    # Allow GitHub URLs and owner/repo format
    github_pattern = r'^(https?://)?(www\.)?github\.com/[\w\-\.]+/[\w\-\.]+(\.git)?$|^[\w\-\.]+/[\w\-\.]+$'
    return bool(re.match(github_pattern, url.strip()))


def find_free_port(start: int = 5001, end: int = 5200) -> Optional[int]:
    """
    Find a free port in the specified range.
    
    Args:
        start: Starting port number
        end: Ending port number
        
    Returns:
        Free port number or None if none found
    """
    for port in range(start, end):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("", port))
                return port
            except OSError:
                continue
    return None


def validate_path_safety(base_path: str, target_path: str) -> bool:
    """
    Validate that target_path is within base_path to prevent path traversal.
    
    Args:
        base_path: The base directory path
        target_path: The target path to validate
        
    Returns:
        True if safe, False otherwise
    """
    try:
        base_abs = os.path.abspath(base_path)
        target_abs = os.path.abspath(target_path)
        return target_abs.startswith(base_abs)
    except Exception:
        return False


def extract_repo_name_from_url(url: str) -> Optional[str]:
    """
    Extract repository name from GitHub URL.
    
    Args:
        url: GitHub URL or owner/repo format
        
    Returns:
        Repository name or None if invalid
    """
    if not url:
        return None
    
    url = url.strip().rstrip("/")
    
    # Handle owner/repo format
    if "/" in url and not url.startswith("http"):
        parts = url.split("/")
        if len(parts) >= 2:
            return parts[-1].replace(".git", "")
    
    # Handle full GitHub URL
    if "github.com" in url:
        parts = url.split("/")
        if len(parts) >= 2:
            repo_name = parts[-1].replace(".git", "")
            return sanitize_repo_name(repo_name)
    
    return None


def check_port_in_use(port: int) -> bool:
    """
    Check if a port is currently in use.
    
    Args:
        port: Port number to check
        
    Returns:
        True if port is in use, False otherwise
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("", port))
            return False
        except OSError:
            return True


def format_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted size string
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"

