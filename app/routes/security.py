# app/routes/security.py
from functools import wraps
from flask import session, jsonify, request, redirect, url_for, flash

def login_required(fn):
    """Ensure the user is authenticated; redirects or returns 401."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            if request.path.startswith("/api/") or request.is_json:
                return jsonify({"error": "Unauthorized. Authentication required."}), 401
            flash("Please sign in to access this page.", "warning")
            return redirect(url_for("web.login"))
        return fn(*args, **kwargs)
    return wrapper

def require_permission(required_permission: str):
    """
    Enforces fine-grained permission authorization.
    Admins automatically bypass all permission checks.
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            user_id = session.get("user_id")
            if not user_id:
                if request.path.startswith("/api/") or request.is_json:
                    return jsonify({"error": "Unauthorized. Authentication required."}), 401
                flash("Please sign in to continue.", "warning")
                return redirect(url_for("web.login"))

            user_roles = session.get("roles", [])
            user_permissions = session.get("permissions", [])

            # Admin automatically bypasses all permission checks
            is_admin = any(r.lower() == "admin" for r in user_roles)
            has_perm = required_permission in user_permissions

            if not (is_admin or has_perm):
                if request.path.startswith("/api/") or request.is_json:
                    return jsonify({
                        "error": "Forbidden. Missing required permission.",
                        "required_permission": required_permission
                    }), 403
                flash(f"Access Denied: You do not have permission ('{required_permission}') to perform this action.", "danger")
                return redirect(url_for("web.list_quizzes"))

            return fn(*args, **kwargs)
        return wrapper
    return decorator