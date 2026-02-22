"""
Theme switching route for PROSIM web interface.

Handles setting the user's theme preference via cookie.
"""

from urllib.parse import urlparse

from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse

from web.theme import DEFAULT_THEME, THEME_COOKIE_NAME, VALID_THEMES

router = APIRouter()


@router.post("/theme")
async def set_theme(
    request: Request,
    theme: str = Form(...),
):
    """Set the user's theme preference cookie.

    Accepts form POST (for no-JS fallback) and returns a redirect
    back to the referring page.
    """
    if theme not in VALID_THEMES:
        theme = DEFAULT_THEME

    # Redirect back to referring page, or home
    # Validate referer is a local path to prevent open redirect
    referer = request.headers.get("referer", "/")
    parsed = urlparse(referer)
    if parsed.netloc and parsed.netloc != request.url.netloc:
        referer = "/"
    else:
        referer = parsed.path or "/"
    response = RedirectResponse(url=referer, status_code=303)
    response.set_cookie(
        key=THEME_COOKIE_NAME,
        value=theme,
        max_age=60 * 60 * 24 * 365,  # 1 year
        httponly=False,  # JS needs to read this for instant switching
        samesite="lax",
        path="/",
    )
    return response
