# app/__init__.py
from flask import Flask, jsonify, session
from config import Config

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Health check
    @app.route("/api/health", methods=["GET"])
    def health_check():
        return jsonify({"service": "Quiz Engine API", "status": "online"}), 200

    # Context processors for templates
    @app.context_processor
    def inject_auth_context():
        roles = session.get("roles", [])
        return {
            "session_user_id": session.get("user_id"),
            "session_username": session.get("username"),
            "session_roles": roles,
            "session_permissions": session.get("permissions", []),
            "is_admin": any(r.lower() == "admin" for r in roles),
            "is_teacher": any(r.lower() in ("teacher", "instructor") for r in roles),
            "is_student": any(r.lower() == "student" for r in roles),
        }

    # Register Blueprints
    from app.routes.web_bp import web_bp
    from app.routes.auth_bp import auth_bp
    from app.routes.quiz_bp import quiz_bp

    app.register_blueprint(web_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(quiz_bp)

    return app