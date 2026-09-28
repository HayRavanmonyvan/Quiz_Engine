# app/routes/auth_bp.py
from flask import Blueprint, request, jsonify, session
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")
user_repo = UserRepository()
auth_service = AuthService(user_repo)

@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    try:
        user_id = auth_service.register_user(
            username=data.get("username"),
            email=data.get("email"),
            raw_password=data.get("password"),
            role_name=data.get("role", "Student")
        )
        return jsonify({"message": "User registered successfully.", "user_id": user_id}), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    try:
        user = auth_service.authenticate(data.get("username", ""), data.get("password", ""))
        session["user_id"] = user.id
        session["username"] = user.username
        session["roles"] = user.roles
        session["permissions"] = user.permissions
        return jsonify({
            "message": "Authenticated",
            "user_id": user.id,
            "username": user.username,
            "roles": user.roles,
            "permissions": user.permissions
        }), 200
    except PermissionError as e:
        return jsonify({"error": str(e)}), 401

@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"message": "Logged out successfully."}), 200