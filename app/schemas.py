from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.utils.text import find_links, link_error

MAX_MESSAGE_LENGTH = 200

EXAMPLE_MESSAGE = "Check out our latest business platform and grow your online visibility. https://example.com"


class PostingRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        json_schema_extra={"examples": [{"message": EXAMPLE_MESSAGE}]},
    )

    message: str = Field(
        min_length=1,
        max_length=MAX_MESSAGE_LENGTH,
        description="Text to publish. Up to 200 characters, with exactly one CTA link.",
    )

    @field_validator("message")
    @classmethod
    def must_contain_exactly_one_valid_link(cls, value: str) -> str:
        links = find_links(value)

        if not links:
            raise ValueError("Message must include one CTA link starting with http:// or https://.")
        if len(links) > 1:
            raise ValueError(f"Message must include exactly one CTA link, but {len(links)} were found.")

        problem = link_error(links[0])
        if problem:
            raise ValueError(problem)

        return value

    @property
    def link(self) -> str:
        return find_links(self.message)[0]


class PostStatus(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"


class PlatformResult(BaseModel):
    platform: str
    status: PostStatus
    posted_url: str | None = None
    public_access: bool = False
    date: str | None = Field(default=None, examples=["2026-11-22"])
    time: str | None = Field(default=None, examples=["10:30:00"])
    error: str | None = None


class PostingResponse(BaseModel):
    success: bool = Field(description="True when at least one platform published the message.")
    results: list[PlatformResult]


class PlatformStatus(BaseModel):
    platform: str
    configured: bool
    missing_settings: list[str] = Field(description="Environment variables that still need a value.")


class ValidationErrorDetail(BaseModel):
    field: str
    message: str


class ValidationErrorResponse(BaseModel):
    success: bool = False
    errors: list[ValidationErrorDetail]
