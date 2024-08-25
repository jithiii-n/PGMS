from flask import Flask
from config import Config
from routes.auth import auth_bp
from routes.user import user_bp
from routes.admin import admin_bp
from models.model_loader import load_classification_model  # Fixed import
import os

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Ensure the upload folder exists
    uploads_dir = os.path.join(app.root_path, app.config['UPLOAD_FOLDER'])
    if not os.path.exists(uploads_dir):
        os.makedirs(uploads_dir)

    # Load and set the classification model
    app.classification_model = load_classification_model()

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(admin_bp)

    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
