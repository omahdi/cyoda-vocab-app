import logging
from typing import Any, Dict

from quart import Blueprint
from quart.typing import ResponseReturnValue
from quart_schema import operation_id, tag, validate

from application.entity.vocabulary_item.version_1 import VocabularyItem
from services.services import get_entity_service

logger = logging.getLogger(__name__)


def _to_entity_dict(data: Any) -> Dict[str, Any]:
    result = data.model_dump(by_alias=True) if hasattr(data, "model_dump") else data
    # Handle nested structure: {'type': 'ENTITY', 'data': {...}, 'meta': {...}}
    if isinstance(result, dict) and 'data' in result and 'type' in result:
        return result['data']
    return result


vocabulary_items_bp = Blueprint(
    "vocabulary_items", __name__, url_prefix="/api/vocabulary-items"
)


@vocabulary_items_bp.route("", methods=["POST"])
@tag(["vocabulary-items"])
@operation_id("create_vocabulary_item")
@validate(request=VocabularyItem, responses={201: (Dict[str, Any], None), 400: (Dict[str, str], None)})
async def create_vocabulary_item(data: VocabularyItem) -> ResponseReturnValue:
    try:
        service = get_entity_service()
        entity_data = data.model_dump(by_alias=True)
        response = await service.save(
            entity=entity_data,
            entity_class=VocabularyItem.ENTITY_NAME,
            entity_version=str(VocabularyItem.ENTITY_VERSION),
        )
        logger.info("Created VocabularyItem with ID: %s", response.metadata.id)
        return {**_to_entity_dict(response.data), "id": response.metadata.id}, 201
    except ValueError as e:
        logger.warning("Validation error: %s", str(e))
        return {"error": str(e)}, 400
    except Exception as e:
        logger.exception("Error creating VocabularyItem: %s", str(e))
        return {"error": str(e)}, 500


@vocabulary_items_bp.route("/<entity_id>", methods=["GET"])
@tag(["vocabulary-items"])
@operation_id("get_vocabulary_item")
@validate(responses={200: (Dict[str, Any], None), 404: (Dict[str, str], None)})
async def get_vocabulary_item(entity_id: str) -> ResponseReturnValue:
    try:
        if not entity_id or len(entity_id.strip()) == 0:
            return {"error": "Entity ID is required"}, 400
        service = get_entity_service()
        response = await service.get_by_id(
            entity_id=entity_id,
            entity_class=VocabularyItem.ENTITY_NAME,
            entity_version=str(VocabularyItem.ENTITY_VERSION),
        )
        if not response:
            return {"error": "VocabularyItem not found"}, 404
        return {**_to_entity_dict(response.data), "id": entity_id}, 200
    except Exception as e:
        logger.exception("Error getting VocabularyItem: %s", str(e))
        return {"error": str(e)}, 500


@vocabulary_items_bp.route("", methods=["GET"])
@tag(["vocabulary-items"])
@operation_id("list_vocabulary_items")
@validate(responses={200: (Dict[str, Any], None), 500: (Dict[str, str], None)})
async def list_vocabulary_items() -> ResponseReturnValue:
    try:
        service = get_entity_service()
        entities = await service.find_all(
            entity_class=VocabularyItem.ENTITY_NAME,
            entity_version=str(VocabularyItem.ENTITY_VERSION),
        )
        entity_list = [{**_to_entity_dict(r.data), "id": r.metadata.id} for r in entities]
        return {"entities": entity_list, "total": len(entity_list)}, 200
    except Exception as e:
        logger.exception("Error listing VocabularyItems: %s", str(e))
        return {"error": str(e)}, 500


@vocabulary_items_bp.route("/<entity_id>", methods=["PUT"])
@tag(["vocabulary-items"])
@operation_id("update_vocabulary_item")
@validate(request=VocabularyItem, responses={200: (Dict[str, Any], None), 404: (Dict[str, str], None)})
async def update_vocabulary_item(
    entity_id: str, data: VocabularyItem
) -> ResponseReturnValue:
    try:
        if not entity_id or len(entity_id.strip()) == 0:
            return {"error": "Entity ID is required"}, 400
        service = get_entity_service()
        entity_data: Dict[str, Any] = data.model_dump(by_alias=True)
        response = await service.update(
            entity_id=entity_id,
            entity=entity_data,
            entity_class=VocabularyItem.ENTITY_NAME,
            entity_version=str(VocabularyItem.ENTITY_VERSION),
        )
        logger.info("Updated VocabularyItem %s", entity_id)
        return {**_to_entity_dict(response.data), "id": entity_id}, 200
    except Exception as e:
        logger.exception("Error updating VocabularyItem: %s", str(e))
        return {"error": str(e)}, 500


@vocabulary_items_bp.route("/<entity_id>", methods=["DELETE"])
@tag(["vocabulary-items"])
@operation_id("delete_vocabulary_item")
@validate(responses={200: (Dict[str, Any], None), 404: (Dict[str, str], None)})
async def delete_vocabulary_item(entity_id: str) -> ResponseReturnValue:
    try:
        if not entity_id or len(entity_id.strip()) == 0:
            return {"error": "Entity ID is required"}, 400
        service = get_entity_service()
        await service.delete_by_id(
            entity_id=entity_id,
            entity_class=VocabularyItem.ENTITY_NAME,
            entity_version=str(VocabularyItem.ENTITY_VERSION),
        )
        logger.info("Deleted VocabularyItem %s", entity_id)
        return {"success": True, "message": "VocabularyItem deleted"}, 200
    except Exception as e:
        logger.exception("Error deleting VocabularyItem: %s", str(e))
        return {"error": str(e)}, 500
