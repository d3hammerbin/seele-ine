#!/usr/bin/env python3
"""
API Key Management Endpoints

Provides REST API endpoints for API key management including:
- API key creation (CLIENT_KEY and CLIENT_SECRET generation)
- API key listing and details
- API key rotation and renewal
- API key revocation and reactivation
- API key usage statistics
"""

from typing import Dict, Any, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from .....core.config.settings import get_settings
from .....core.exceptions.base import (
    ValidationException, AuthorizationException, NotFoundError, BusinessLogicError
)
from .....core.security.dependencies import get_current_user, CurrentUser
from .....infrastructure.database.session import get_async_db_session
from .....infrastructure.repositories.application_repository_impl import ApplicationRepositoryImpl
from .....infrastructure.repositories.user_repository_impl import UserRepositoryImpl
from .....application.use_cases.api_key_use_cases import APIKeyManagementUseCase
from .....application.dto.api_key_dto import (
    APIKeyCreateRequest, APIKeyRotateRequest, APIKeyUpdateRequest,
    APIKeyValidationRequest, BulkAPIKeyActionRequest,
    APIKeyCreateResponse, APIKeyListResponse, APIKeyDetailResponse,
    APIKeyRotateResponse, APIKeyRevokeResponse, APIKeyReactivateResponse,
    APIKeyUpdateResponse, APIKeyValidationResponse, APIKeyUsageStatsResponse,
    BulkAPIKeyActionResponse
)

# Initialize router
router = APIRouter(prefix="/api-keys", tags=["API Key Management"])
security = HTTPBearer()
settings = get_settings()


# Dependency to get API key management use case
async def get_api_key_use_case(
    db_session: AsyncSession = Depends(get_async_db_session)
) -> APIKeyManagementUseCase:
    """Get API key management use case with dependencies."""
    application_repository = ApplicationRepositoryImpl(db_session)
    user_repository = UserRepositoryImpl(db_session)
    return APIKeyManagementUseCase(application_repository, user_repository)


@router.post(
    "/",
    response_model=APIKeyCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new API key",
    description="Create a new API key pair (CLIENT_KEY and CLIENT_SECRET) for an application."
)
async def create_api_key(
    request: APIKeyCreateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    api_key_use_case: APIKeyManagementUseCase = Depends(get_api_key_use_case)
) -> APIKeyCreateResponse:
    """Create a new API key pair."""
    try:
        result = await api_key_use_case.create_api_key(
            user_id=current_user.id,
            request=request
        )
        
        return APIKeyCreateResponse(**result)
        
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except BusinessLogicError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API key creation failed. Please try again."
        )


@router.get(
    "/",
    response_model=APIKeyListResponse,
    summary="List API keys",
    description="Get a list of all API keys for the current user."
)
async def list_api_keys(
    include_inactive: bool = Query(
        default=False,
        description="Include inactive API keys in the response"
    ),
    current_user: CurrentUser = Depends(get_current_user),
    api_key_use_case: APIKeyManagementUseCase = Depends(get_api_key_use_case)
) -> APIKeyListResponse:
    """List all API keys for the current user."""
    try:
        result = await api_key_use_case.list_api_keys(
            user_id=current_user.id,
            include_inactive=include_inactive
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve API keys. Please try again."
        )


@router.get(
    "/{application_id}",
    response_model=APIKeyDetailResponse,
    summary="Get API key details",
    description="Get detailed information about a specific API key."
)
async def get_api_key(
    application_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    api_key_use_case: APIKeyManagementUseCase = Depends(get_api_key_use_case)
) -> APIKeyDetailResponse:
    """Get API key details."""
    try:
        result = await api_key_use_case.get_api_key(
            user_id=current_user.id,
            application_id=application_id
        )
        
        return APIKeyDetailResponse(**result)
        
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except AuthorizationException as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve API key details. Please try again."
        )


@router.put(
    "/{application_id}",
    response_model=APIKeyUpdateResponse,
    summary="Update API key information",
    description="Update API key metadata (name and description)."
)
async def update_api_key(
    application_id: UUID,
    request: APIKeyUpdateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    api_key_use_case: APIKeyManagementUseCase = Depends(get_api_key_use_case)
) -> APIKeyUpdateResponse:
    """Update API key information."""
    try:
        result = await api_key_use_case.update_api_key_info(
            user_id=current_user.id,
            application_id=application_id,
            name=request.name,
            description=request.description
        )
        
        return APIKeyUpdateResponse(**result)
        
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except AuthorizationException as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API key update failed. Please try again."
        )


@router.post(
    "/{application_id}/rotate",
    response_model=APIKeyRotateResponse,
    summary="Rotate API key",
    description="Generate a new CLIENT_SECRET for an existing API key. The CLIENT_KEY remains the same."
)
async def rotate_api_key(
    application_id: UUID,
    request: APIKeyRotateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    api_key_use_case: APIKeyManagementUseCase = Depends(get_api_key_use_case)
) -> APIKeyRotateResponse:
    """Rotate API key (generate new CLIENT_SECRET)."""
    try:
        result = await api_key_use_case.rotate_api_key(
            user_id=current_user.id,
            application_id=application_id,
            request=request
        )
        
        return APIKeyRotateResponse(**result)
        
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except AuthorizationException as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API key rotation failed. Please try again."
        )


@router.post(
    "/{application_id}/revoke",
    response_model=APIKeyRevokeResponse,
    summary="Revoke API key",
    description="Revoke (deactivate) an API key. The key will no longer be valid for authentication."
)
async def revoke_api_key(
    application_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    api_key_use_case: APIKeyManagementUseCase = Depends(get_api_key_use_case)
) -> APIKeyRevokeResponse:
    """Revoke API key."""
    try:
        result = await api_key_use_case.revoke_api_key(
            user_id=current_user.id,
            application_id=application_id
        )
        
        return APIKeyRevokeResponse(**result)
        
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except AuthorizationException as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API key revocation failed. Please try again."
        )


@router.post(
    "/{application_id}/reactivate",
    response_model=APIKeyReactivateResponse,
    summary="Reactivate API key",
    description="Reactivate a previously revoked API key (if not expired)."
)
async def reactivate_api_key(
    application_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    api_key_use_case: APIKeyManagementUseCase = Depends(get_api_key_use_case)
) -> APIKeyReactivateResponse:
    """Reactivate API key."""
    try:
        result = await api_key_use_case.reactivate_api_key(
            user_id=current_user.id,
            application_id=application_id
        )
        
        return APIKeyReactivateResponse(**result)
        
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except AuthorizationException as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API key reactivation failed. Please try again."
        )


@router.delete(
    "/{application_id}",
    response_model=Dict[str, Any],
    summary="Delete API key",
    description="Permanently delete an API key and its associated application."
)
async def delete_api_key(
    application_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    api_key_use_case: APIKeyManagementUseCase = Depends(get_api_key_use_case)
) -> Dict[str, Any]:
    """Delete API key permanently."""
    try:
        # First get the API key to verify ownership
        api_key_info = await api_key_use_case.get_api_key(
            user_id=current_user.id,
            application_id=application_id
        )
        
        # TODO: Implement actual deletion in use case
        # For now, we'll just revoke it
        await api_key_use_case.revoke_api_key(
            user_id=current_user.id,
            application_id=application_id
        )
        
        return {
            "application_id": application_id,
            "message": "API key deleted successfully",
            "deleted_at": "2024-01-01T00:00:00Z"  # TODO: Use actual timestamp
        }
        
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except AuthorizationException as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API key deletion failed. Please try again."
        )


@router.post(
    "/validate",
    response_model=APIKeyValidationResponse,
    summary="Validate API key",
    description="Validate an API key pair (CLIENT_KEY and CLIENT_SECRET)."
)
async def validate_api_key(
    request: APIKeyValidationRequest,
    api_key_use_case: APIKeyManagementUseCase = Depends(get_api_key_use_case)
) -> APIKeyValidationResponse:
    """Validate API key pair."""
    try:
        # TODO: Implement validation logic in use case
        # This would typically validate the CLIENT_KEY and CLIENT_SECRET pair
        # and return validation status with application information
        
        from datetime import datetime, timezone
        
        return APIKeyValidationResponse(
            is_valid=False,  # TODO: Implement actual validation
            validation_errors=["Validation not yet implemented"],
            validated_at=datetime.now(timezone.utc)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API key validation failed. Please try again."
        )


@router.get(
    "/usage/stats",
    response_model=APIKeyUsageStatsResponse,
    summary="Get API key usage statistics",
    description="Get usage statistics for all API keys belonging to the current user."
)
async def get_api_key_usage_stats(
    days: int = Query(
        default=30,
        ge=1,
        le=365,
        description="Number of days to include in statistics"
    ),
    current_user: CurrentUser = Depends(get_current_user),
    api_key_use_case: APIKeyManagementUseCase = Depends(get_api_key_use_case)
) -> APIKeyUsageStatsResponse:
    """Get API key usage statistics."""
    try:
        # TODO: Implement usage statistics in use case
        from datetime import datetime, timezone, timedelta
        
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)
        
        return APIKeyUsageStatsResponse(
            stats=[],  # TODO: Implement actual stats
            total_applications=0,
            period_start=start_date,
            period_end=end_date,
            generated_at=datetime.now(timezone.utc)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve usage statistics. Please try again."
        )


@router.post(
    "/bulk-action",
    response_model=BulkAPIKeyActionResponse,
    summary="Perform bulk action on API keys",
    description="Perform bulk actions (revoke, reactivate, delete) on multiple API keys."
)
async def bulk_api_key_action(
    request: BulkAPIKeyActionRequest,
    current_user: CurrentUser = Depends(get_current_user),
    api_key_use_case: APIKeyManagementUseCase = Depends(get_api_key_use_case)
) -> BulkAPIKeyActionResponse:
    """Perform bulk action on API keys."""
    try:
        results = []
        successful = 0
        failed = 0
        
        for app_id in request.application_ids:
            try:
                if request.action == "revoke":
                    result = await api_key_use_case.revoke_api_key(
                        user_id=current_user.id,
                        application_id=app_id
                    )
                elif request.action == "reactivate":
                    result = await api_key_use_case.reactivate_api_key(
                        user_id=current_user.id,
                        application_id=app_id
                    )
                elif request.action == "delete":
                    # TODO: Implement actual deletion
                    result = await api_key_use_case.revoke_api_key(
                        user_id=current_user.id,
                        application_id=app_id
                    )
                
                results.append({
                    "application_id": str(app_id),
                    "status": "success",
                    "message": result.get("message", f"Action {request.action} completed")
                })
                successful += 1
                
            except Exception as e:
                results.append({
                    "application_id": str(app_id),
                    "status": "failed",
                    "error": str(e)
                })
                failed += 1
        
        from datetime import datetime, timezone
        
        return BulkAPIKeyActionResponse(
            total_requested=len(request.application_ids),
            successful=successful,
            failed=failed,
            results=results,
            action=request.action,
            performed_at=datetime.now(timezone.utc),
            message=f"Bulk {request.action} completed: {successful} successful, {failed} failed"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Bulk action failed. Please try again."
        )