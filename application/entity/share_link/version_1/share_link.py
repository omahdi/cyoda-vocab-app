from datetime import datetime, timezone
from typing import ClassVar, Optional

from pydantic import ConfigDict, Field, field_validator

from common.entity.cyoda_entity import CyodaEntity


class ShareLink(CyodaEntity):
    """
    ShareLink represents a shareable public link for read-only access to vocabulary items.
    """

    ENTITY_NAME: ClassVar[str] = "ShareLink"
    ENTITY_VERSION: ClassVar[int] = 1

    token: str = Field(..., description="Unique URL-safe token for the share link")
    label: Optional[str] = Field(
        default=None, description="Optional label for the share link"
    )
    created_at: Optional[str] = Field(
        default_factory=lambda: datetime.now(timezone.utc)
        .isoformat()
        .replace("+00:00", "Z"),
        alias="createdAt",
        description="Timestamp when the link was created",
    )
    revoked_at: Optional[str] = Field(
        default=None,
        alias="revokedAt",
        description="Timestamp when the link was revoked",
    )
    last_accessed_at: Optional[str] = Field(
        default=None,
        alias="lastAccessedAt",
        description="Timestamp of last access",
    )
    visit_count: int = Field(
        default=0, alias="visitCount", description="Number of times the link was accessed"
    )

    @field_validator("token")
    @classmethod
    def validate_token(cls, v: str) -> str:
        if not v or len(v.strip()) == 0:
            raise ValueError("Token must be non-empty")
        return v.strip()

    def update_access(self) -> None:
        self.last_accessed_at = (
            datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        )
        self.visit_count += 1

    def revoke(self) -> None:
        self.revoked_at = (
            datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        )

    model_config = ConfigDict(
        populate_by_name=True,
        use_enum_values=True,
        validate_assignment=True,
        extra="allow",
    )

