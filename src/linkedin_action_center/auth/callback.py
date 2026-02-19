from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from threading import Thread
import uvicorn
import webbrowser
import time

from linkedin_action_center.auth.manager import AuthManager
from linkedin_action_center.core.config import OAUTH_STATE
from linkedin_action_center.utils.logger import logger, log_auth_event

app = FastAPI()
auth_manager = AuthManager()

# Store the auth code globally
auth_code_received = None

@app.get("/callback")
async def callback(request: Request):
    """
    Handles the redirect from LinkedIn after user authorization.
    """
    global auth_code_received

    # Verify the state parameter to prevent CSRF attacks
    state = request.query_params.get("state")
    if state != OAUTH_STATE:
        raise HTTPException(status_code=400, detail="Invalid state parameter.")

    code = request.query_params.get("code")
    if not code:
        error = request.query_params.get("error")
        error_description = request.query_params.get("error_description")
        return HTMLResponse(content=f"<h1>Error: {error}</h1><p>{error_description}</p>", status_code=400)

    log_auth_event("Authorization code received", code[:15] + "...")
    auth_code_received = code

    return HTMLResponse(content="""
        <html>
            <head>
                <title>Authentication Successful</title>
                <style>
                    body { font-family: sans-serif; text-align: center; padding-top: 50px; }
                    h1 { color: #0077B5; }
                    p { color: #333; }
                </style>
            </head>
            <body>
                <h1>Authentication Successful!</h1>
                <p>You can now close this browser tab and return to the application.</p>
            </body>
        </html>
    """)

def run_callback_server():
    """Runs the FastAPI app in a separate thread."""
    uvicorn.run(app, host="localhost", port=5000)

def start_auth_flow():
    """
    Starts the entire 3-legged OAuth flow:
    1. Starts the local callback server.
    2. Opens the authorization URL in the user's browser.
    3. Waits for the authorization code to be received.
    4. Exchanges the code for an access token.
    """
    if auth_manager.is_authenticated():
        log_auth_event("Already authenticated", "Checking token health")
        auth_manager.check_token_health()
        return

    # Start FastAPI server in a background thread
    server_thread = Thread(target=run_callback_server, daemon=True)
    server_thread.start()
    logger.info("Callback server started in background")

    # Generate and open the authorization URL
    auth_url = auth_manager.get_authorization_url()
    logger.info(f"Opening authorization URL in browser: {auth_url}")
    webbrowser.open(auth_url)

    # Wait for the callback to set the auth_code
    logger.info("Waiting for user authorization...")
    while not auth_code_received:
        time.sleep(1)

    log_auth_event("Authorization complete", "Exchanging code for token")
    auth_manager.exchange_code_for_token(auth_code_received)

    log_auth_event("Full authentication flow complete")

if __name__ == "__main__":
    start_auth_flow()
