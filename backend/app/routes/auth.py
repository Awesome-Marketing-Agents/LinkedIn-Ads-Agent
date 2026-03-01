"""Auth routes: OAuth status, URL, health check, and callback."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse

from app.core.config import settings
from app.core.deps import get_auth
from app.core.security import AuthManager
from app.utils.logging import get_logger, log_auth_event

logger = get_logger(__name__)
router = APIRouter()


@router.get("/status")
async def auth_status(auth: AuthManager = Depends(get_auth)):
    return auth.token_status()


@router.get("/url")
async def auth_url(auth: AuthManager = Depends(get_auth)):
    return {"url": auth.get_authorization_url()}


@router.get("/health")
async def auth_health(auth: AuthManager = Depends(get_auth)):
    healthy = await auth.check_token_health()
    return {"healthy": healthy}


@router.get("/callback", response_class=HTMLResponse)
async def auth_callback(request: Request, auth: AuthManager = Depends(get_auth)):
    state = request.query_params.get("state")
    if state != settings.OAUTH_STATE:
        raise HTTPException(status_code=400, detail="Invalid state parameter.")

    code = request.query_params.get("code")
    if not code:
        error = request.query_params.get("error", "unknown")
        desc = request.query_params.get("error_description", "No error description")
        raise HTTPException(status_code=400, detail=f"{error}: {desc}")

    log_auth_event("Authorization code received", code[:15] + "...")
    await auth.exchange_code_for_token(code)
    log_auth_event("Full authentication flow complete")

    return """
    <html>
      <head><title>Authentication Successful</title></head>
      <body style="font-family: sans-serif; text-align: center; padding-top: 50px;">
        <h1 style="color: #0077B5;">Authentication Successful!</h1>
        <p>You can now close this tab and return to the application.</p>
        <script>setTimeout(() => window.close(), 3000);</script>
      </body>
    </html>
    """
