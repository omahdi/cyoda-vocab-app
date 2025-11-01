import logging
from typing import Any, Dict

from quart import Blueprint
from quart.typing import ResponseReturnValue
from quart_schema import operation_id, tag, validate

from application.entity.share_link.version_1 import ShareLink
from common.entity.entity_casting import cast_entity
from services.services import get_entity_service

logger = logging.getLogger(__name__)


def _to_entity_dict(data: Any) -> Dict[str, Any]:
    result = data.model_dump(by_alias=True) if hasattr(data, "model_dump") else data
    # Handle nested structure: {'type': 'ENTITY', 'data': {...}, 'meta': {...}}
    if isinstance(result, dict) and 'data' in result and 'type' in result:
        return result['data']
    return result


share_links_bp = Blueprint("share_links", __name__, url_prefix="/api/share-links")


@share_links_bp.route("", methods=["POST"])
@tag(["share-links"])
@operation_id("create_share_link")
@validate(request=ShareLink, responses={201: (Dict[str, Any], None), 400: (Dict[str, str], None)})
async def create_share_link(data: ShareLink) -> ResponseReturnValue:
    try:
        service = get_entity_service()
        entity_data = data.model_dump(by_alias=True)
        response = await service.save(
            entity=entity_data,
            entity_class=ShareLink.ENTITY_NAME,
            entity_version=str(ShareLink.ENTITY_VERSION),
        )
        logger.info("Created ShareLink with ID: %s", response.metadata.id)
        return {**_to_entity_dict(response.data), "id": response.metadata.id}, 201
    except ValueError as e:
        logger.warning("Validation error: %s", str(e))
        return {"error": str(e)}, 400
    except Exception as e:
        logger.exception("Error creating ShareLink: %s", str(e))
        return {"error": str(e)}, 500


@share_links_bp.route("/<entity_id>", methods=["GET"])
@tag(["share-links"])
@operation_id("get_share_link")
@validate(responses={200: (Dict[str, Any], None), 404: (Dict[str, str], None)})
async def get_share_link(entity_id: str) -> ResponseReturnValue:
    try:
        if not entity_id or len(entity_id.strip()) == 0:
            return {"error": "Entity ID is required"}, 400
        service = get_entity_service()
        response = await service.get_by_id(
            entity_id=entity_id,
            entity_class=ShareLink.ENTITY_NAME,
            entity_version=str(ShareLink.ENTITY_VERSION),
        )
        if not response:
            return {"error": "ShareLink not found"}, 404
        return {**_to_entity_dict(response.data), "id": entity_id}, 200
    except Exception as e:
        logger.exception("Error getting ShareLink: %s", str(e))
        return {"error": str(e)}, 500


@share_links_bp.route("", methods=["GET"])
@tag(["share-links"])
@operation_id("list_share_links")
@validate(responses={200: (Dict[str, Any], None), 500: (Dict[str, str], None)})
async def list_share_links() -> ResponseReturnValue:
    try:
        service = get_entity_service()
        entities = await service.find_all(
            entity_class=ShareLink.ENTITY_NAME,
            entity_version=str(ShareLink.ENTITY_VERSION),
        )
        entity_list = [{**_to_entity_dict(r.data), "id": r.metadata.id} for r in entities]
        return {"entities": entity_list, "total": len(entity_list)}, 200
    except Exception as e:
        logger.exception("Error listing ShareLinks: %s", str(e))
        return {"error": str(e)}, 500


@share_links_bp.route("/<entity_id>", methods=["DELETE"])
@tag(["share-links"])
@operation_id("revoke_share_link")
@validate(responses={200: (Dict[str, Any], None), 404: (Dict[str, str], None)})
async def revoke_share_link(entity_id: str) -> ResponseReturnValue:
    try:
        if not entity_id or len(entity_id.strip()) == 0:
            return {"error": "Entity ID is required"}, 400
        service = get_entity_service()
        response = await service.get_by_id(
            entity_id=entity_id,
            entity_class=ShareLink.ENTITY_NAME,
            entity_version=str(ShareLink.ENTITY_VERSION),
        )
        if not response:
            return {"error": "ShareLink not found"}, 404
        share_link = cast_entity(response.data, ShareLink)
        share_link.revoke()
        updated_response = await service.update(
            entity_id=entity_id,
            entity=_to_entity_dict(share_link),
            entity_class=ShareLink.ENTITY_NAME,
            transition="revoke",
            entity_version=str(ShareLink.ENTITY_VERSION),
        )
        logger.info("Revoked ShareLink %s", entity_id)
        return _to_entity_dict(updated_response.data), 200
    except Exception as e:
        logger.exception("Error revoking ShareLink: %s", str(e))
        return {"error": str(e)}, 500
