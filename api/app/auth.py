"""JWT Bearer authentication for api-news."""

import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from fastapi import HTTPException, Header, Request
from pydantic import BaseModel, Field


class AuthConfig(BaseModel):
    """Authentication configuration from environment."""

    jwt_secret: str = Field(description="JWT secret for bearer token verification")
    jwt_algorithm: str = Field(default="HS256")
    jwt_expiry_hours: int = Field(default=24)

    @classmethod
    def from_env(cls) -> "AuthConfig":
        """Load JWT-only configuration from environment variables."""
        jwt_secret = os.getenv("AUTH_JWT_SECRET", "")
        jwt_algorithm = os.getenv("AUTH_JWT_ALGORITHM", "HS256")
        jwt_expiry_hours = int(os.getenv("AUTH_JWT_EXPIRY_HOURS", "24"))

        if len(jwt_secret) < 32:
            raise RuntimeError(
                "AUTH_JWT_SECRET must be configured with at least 32 characters "
                "when JWT bearer authentication is enabled."
            )

        return cls(
            jwt_secret=jwt_secret,
            jwt_algorithm=jwt_algorithm,
            jwt_expiry_hours=jwt_expiry_hours,
        )


def generate_jwt_token(secret: str, algorithm: str = "HS256", expiry_hours: int = 24) -> str:
    """Generate a JWT token for testing/demo."""
    payload = {
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(hours=expiry_hours),
        "scope": "news:read",
    }
    return jwt.encode(payload, secret, algorithm=algorithm)


async def verify_jwt_token(authorization: Optional[str] = Header(None), config: Optional[AuthConfig] = None) -> bool:
    """Verify JWT bearer token authentication."""
    if config is None:
        raise HTTPException(status_code=500, detail="Authentication configuration is not loaded")

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header (format: 'Bearer <token>')")

    token = authorization[7:]
    try:
        jwt.decode(token, config.jwt_secret, algorithms=[config.jwt_algorithm])
        return True
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail="Invalid token") from e


async def verify_auth(request: Request, config: AuthConfig) -> bool:
    """JWT bearer authentication dispatcher."""
    auth_header = request.headers.get("authorization")
    return await verify_jwt_token(authorization=auth_header, config=config)
