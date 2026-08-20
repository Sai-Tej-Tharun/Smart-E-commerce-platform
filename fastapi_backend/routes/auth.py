"""
routes/auth.py
----------------
POST /auth/register  - email/password signup
POST /auth/login     - email/password login, returns access + refresh tokens
POST /auth/refresh   - exchange a valid refresh token for a new access token
GET  /auth/me        - return the current authenticated user
POST /auth/social    - Auth0 social login (Google / Facebook)
"""

from fastapi import APIRouter, Depends, HTTPException, status
from jose import jwt
from jose.exceptions import JWTError
from sqlalchemy.orm import Session

import requests

from core.config import settings
from core.database import get_db
from core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_user,
    hash_password,
    verify_password,
)
from models.user import User, UserRole
from schemas.user import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    SocialLoginRequest,
    TokenResponse,
    UserOut,
)

router = APIRouter(prefix="/auth", tags=["Auth"])


def _issue_tokens(user: User) -> TokenResponse:
    return TokenResponse(
        access_token=create_access_token(subject=user.email),
        refresh_token=create_refresh_token(subject=user.email),
    )


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    user = User(
        name=payload.name,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        role=UserRole.CUSTOMER,  # every self-registered user starts as a customer
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not user.hashed_password or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled")
    return _issue_tokens(user)


@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)):
    email = decode_token(payload.refresh_token, expected_type="refresh")
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    # Issue a brand new access AND refresh token pair (refresh token rotation) —
    # this limits how long any single refresh token stays valid if it leaked.
    return _issue_tokens(user)


@router.get("/me", response_model=UserOut)
def read_current_user(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/social", response_model=TokenResponse)
def social_login(payload: SocialLoginRequest, db: Session = Depends(get_db)):
    """
    Verifies an ID token issued by Auth0 after the FRONTEND completed a
    Google/Facebook login via Auth0's hosted login page. This endpoint never
    talks to Google/Facebook directly — Auth0 already did that and handed
    the frontend a signed ID token, which we verify here using Auth0's
    public signing keys (JWKS) before trusting any of its claims.
    """
    if not settings.AUTH0_DOMAIN:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Auth0 is not configured on this server (AUTH0_DOMAIN missing in .env)",
        )

    try:
        jwks = requests.get(settings.AUTH0_JWKS_URL, timeout=5).json()
        unverified_header = jwt.get_unverified_header(payload.auth0_id_token)
        rsa_key = next(
            (
                {"kty": k["kty"], "kid": k["kid"], "use": k["use"], "n": k["n"], "e": k["e"]}
                for k in jwks["keys"]
                if k["kid"] == unverified_header.get("kid")
            ),
            None,
        )
        if rsa_key is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unable to find matching signing key")

        claims = jwt.decode(
            payload.auth0_id_token,
            rsa_key,
            algorithms=["RS256"],
            audience=settings.AUTH0_CLIENT_ID,
            issuer=settings.AUTH0_ISSUER,
        )
    except JWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid Auth0 token: {exc}")

    auth0_sub = claims["sub"]  # e.g. "google-oauth2|1234567890"
    email = claims.get("email")
    name = claims.get("name", email or "Social User")

    user = db.query(User).filter(User.auth0_sub == auth0_sub).first()
    if not user and email:
        # If they'd previously registered with the same email/password, link accounts
        user = db.query(User).filter(User.email == email).first()

    if not user:
        user = User(name=name, email=email, auth0_sub=auth0_sub, role=UserRole.CUSTOMER, hashed_password=None)
        db.add(user)
    else:
        user.auth0_sub = auth0_sub

    db.commit()
    db.refresh(user)
    return _issue_tokens(user)
