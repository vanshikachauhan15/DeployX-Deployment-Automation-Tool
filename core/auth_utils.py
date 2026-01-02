from functools import wraps
from flask import session, redirect, url_for, request, jsonify

def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            if request.is_json:
                return jsonify({"error": "Login required"}), 401
            return redirect(url_for("auth.login"))
        return fn(*args, **kwargs)
    return wrapper

