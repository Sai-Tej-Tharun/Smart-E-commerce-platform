"""
core/permissions.py
---------------------
Role-based access control (RBAC).

Usage in a route:
    @router.post("/products", dependencies=[Depends(require_role("admin"))])
    def create_product(...): ...

require_role() returns a FastAPI dependency that:
  1. Resolves the current authenticated user (via get_current_user)
  2. Checks their .role against the allowed roles passed in
  3. Raises 403 Forbidden if they don't match
"""

from fastapi import Depends, HTTPException, status

from core.security import get_current_user
from models.user import User


def require_role(*allowed_roles: str):
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of roles: {', '.join(allowed_roles)}",
            )
        return current_user

    return role_checker
