from fastapi import APIRouter, Depends, Request

from app.schemas import PlatformStatus, PostingRequest, PostingResponse, PostStatus, ValidationErrorResponse
from app.services.posting_service import PostingService

router = APIRouter(tags=["Posting"])


def get_posting_service(request: Request) -> PostingService:
    return request.app.state.posting_service


@router.post(
    "/posting",
    response_model=PostingResponse,
    summary="Publish a message to every supported platform",
    responses={422: {"model": ValidationErrorResponse, "description": "The message failed validation."}},
)
async def create_posting(
    payload: PostingRequest,
    service: PostingService = Depends(get_posting_service),
) -> PostingResponse:
    results = await service.publish_everywhere(payload.message, payload.link)
    return PostingResponse(
        success=any(result.status == PostStatus.SUCCESS for result in results),
        results=results,
    )


@router.get(
    "/platforms",
    response_model=list[PlatformStatus],
    summary="List the platforms and whether their credentials are set",
)
async def list_platforms(service: PostingService = Depends(get_posting_service)) -> list[PlatformStatus]:
    return service.platform_statuses()
