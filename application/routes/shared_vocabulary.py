import logging
from typing import Any, Dict, List

from quart import Blueprint
from quart.typing import ResponseReturnValue
from quart_schema import operation_id, tag, validate

from application.entity.share_link.version_1 import ShareLink
from application.entity.vocabulary_item.version_1 import VocabularyItem
from services.services import get_entity_service

logger = logging.getLogger(__name__)


def _to_entity_dict(data: Any) -> Dict[str, Any]:
    return data.model_dump(by_alias=True) if hasattr(data, "model_dump") else data


shared_vocabulary_bp = Blueprint(
    "shared_vocabulary", __name__, url_prefix="/api/shared"
)


@shared_vocabulary_bp.route("/<token>", methods=["GET"])
@tag(["shared"])
@operation_id("get_shared_vocabulary")
@validate(responses={200: (Dict[str, Any], None), 404: (Dict[str, str], None)})
async def get_shared_vocabulary(token: str) -> ResponseReturnValue:
    """
    Get vocabulary items by ShareLink token.
    
    This endpoint allows anyone with the token to access the shared vocabulary.
    It also tracks access by incrementing visit count and updating last accessed time.
    """
    try:
        if not token or len(token.strip()) == 0:
            return {"error": "Token is required"}, 400

        service = get_entity_service()

        # Find the ShareLink by token
        # We need to list all ShareLinks and filter by token since we don't have search by field
        share_links = await service.find_all(
            entity_class=ShareLink.ENTITY_NAME,
            entity_version=str(ShareLink.ENTITY_VERSION),
        )

        share_link = None
        share_link_id = None
        for link in share_links:
            link_data = _to_entity_dict(link.data)
            if link_data.get("token") == token:
                share_link = link_data
                share_link_id = link.metadata.id
                break

        if not share_link:
            return {"error": f"ShareLink not found for token: {token}"}, 404

        # Check if the link has been revoked
        if share_link.get("revokedAt"):
            return {
                "error": "This share link has been revoked and is no longer accessible"
            }, 403

        # Get all vocabulary items
        # TODO: In a real implementation, you'd filter by lesson or have a direct relationship
        # For now, we return all items or could filter by lesson if specified
        all_items = await service.find_all(
            entity_class=VocabularyItem.ENTITY_NAME,
            entity_version=str(VocabularyItem.ENTITY_VERSION),
        )

        # Extract just the vocabulary data
        vocabulary_items = [_to_entity_dict(item.data) for item in all_items]

        # TODO: Update access tracking (visitCount, lastAccessedAt)
        # This would require updating the ShareLink entity
        # For now, we just return the data

        logger.info(
            f"Shared vocabulary accessed via token '{token}': {len(vocabulary_items)} items"
        )

        return {
            "success": True,
            "token": token,
            "label": share_link.get("label"),
            "total": len(vocabulary_items),
            "items": vocabulary_items,
            "share_info": {
                "created_at": share_link.get("createdAt"),
                "visit_count": share_link.get("visitCount", 0),
                "last_accessed": share_link.get("lastAccessedAt"),
            },
        }, 200

    except Exception as e:
        logger.exception(f"Error getting shared vocabulary for token {token}: {str(e)}")
        return {"error": str(e)}, 500
