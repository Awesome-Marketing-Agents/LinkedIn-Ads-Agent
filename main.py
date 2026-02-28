import bootstrap  # noqa: F401  — adds src/ to sys.path

from flask import Flask
from linkedin_action_center.auth.manager import AuthManager
from ui import register_routes

app = Flask(__name__)
auth_manager = AuthManager()

register_routes(app, auth_manager)

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5001)
