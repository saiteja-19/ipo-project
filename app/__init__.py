from flask import Flask

def create_app():
    """Application factory function."""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'a_very_secret_and_complex_key_for_ipo_portal'

    # ✅ Initialize database
    from . import db
    db.init_app(app)  # This registers init-db command

    # ✅ Register Blueprints
    from .main.routes import main_bp
    from .company.routes import company_bp
    from .candidate.routes import candidate_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(company_bp, url_prefix='/company')
    app.register_blueprint(candidate_bp, url_prefix='/candidate')

    return app
