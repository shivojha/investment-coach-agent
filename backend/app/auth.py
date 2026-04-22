from fastapi import HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import settings

bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(bearer),
) -> str:
    # Local dev: skip auth entirely — return a fixed test user
    if settings.use_local_secrets:
        return "local-dev-user"

    if not credentials:
        raise HTTPException(status_code=401, detail="Missing token")

    # Production: ASWA validates the token before the request reaches us.
    # We trust the X-MS-CLIENT-PRINCIPAL-ID header injected by ASWA.
    raise HTTPException(status_code=401, detail="Configure ASWA auth for production")
