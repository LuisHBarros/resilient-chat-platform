"""Authentication API routes - Proxy to auth service."""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr
import httpx
import os

router = APIRouter(prefix="/auth", tags=["authentication"])


class MagicLinkRequest(BaseModel):
    email: EmailStr


@router.post("/magic-link")
async def send_magic_link(request: MagicLinkRequest):
    """
    Send magic link to user's email via auth service.
    
    This endpoint proxies the request to the auth-service microservice.
    """
    auth_service_url = os.getenv("AUTH_SERVICE_URL", "http://localhost:3001")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{auth_service_url}/api/auth/request",
                json={"email": request.email},
                timeout=10.0
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=response.json().get("message", "Failed to send magic link")
                )
                
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Auth service timeout"
        )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Auth service unavailable: {str(e)}"
        )

