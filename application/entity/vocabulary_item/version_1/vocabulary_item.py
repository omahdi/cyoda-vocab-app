from datetime import datetime, timezone
from typing import ClassVar, Optional

from pydantic import ConfigDict, Field, field_validator

from common.entity.cyoda_entity import CyodaEntity


class VocabularyItem(CyodaEntity):
    """
    VocabularyItem represents a vocabulary entry with front/back translation,
    optional comment and lesson classification.
    """

    ENTITY_NAME: ClassVar[str] = "VocabularyItem"
    ENTITY_VERSION: ClassVar[int] = 1

    front: str = Field(..., description="Front side of the vocabulary item")
    back: str = Field(..., description="Back side of the vocabulary item")
    comment: Optional[str] = Field(
        default=None, description="Optional comment for the vocabulary item"
    )
    lesson: Optional[str] = Field(
        default=None, description="Optional lesson classification"
    )
    created_at: Optional[str] = Field(
        default_factory=lambda: datetime.now(timezone.utc)
        .isoformat()
        .replace("+00:00", "Z"),
        alias="createdAt",
        description="Timestamp when the item was created",
    )
    updated_at: Optional[str] = Field(
        default=None,
        alias="updatedAt",
        description="Timestamp when the item was last updated",
    )

    @field_validator("front")
    @classmethod
    def validate_front(cls, v: str) -> str:
        if not v or len(v.strip()) == 0:
            raise ValueError("Front must be non-empty")
        return v.strip()

    @field_validator("back")
    @classmethod
    def validate_back(cls, v: str) -> str:
        if not v or len(v.strip()) == 0:
            raise ValueError("Back must be non-empty")
        return v.strip()

    def update_timestamp(self) -> None:
        self.updated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    model_config = ConfigDict(
        populate_by_name=True,
        use_enum_values=True,
        validate_assignment=True,
        extra="allow",
    )
