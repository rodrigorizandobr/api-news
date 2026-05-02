from datetime import date as date_type

from pydantic import BaseModel, Field, model_validator


class NewsQueryParams(BaseModel):
    q: str = Field(..., description="Comma-separated keywords (required)")
    date: date_type = Field(..., description="Specific UTC date filter in YYYY-MM-DD format (required)")
    language: str = Field(..., description="Language filter (e.g. en, pt) (required)")
    country: str = Field(..., description="Country filter (e.g. US, BR) (required)")

    @model_validator(mode="after")
    def validate_filters(self) -> "NewsQueryParams":
        if not self.q or not self.q.strip():
            raise ValueError("keywords (q) is required: provide at least one keyword")
        if not self.language or not self.language.strip():
            raise ValueError("language is required: provide a language code (e.g. en, pt)")
        if not self.country or not self.country.strip():
            raise ValueError("country is required: provide a country code (e.g. US, BR)")

        return self

    @property
    def keywords(self) -> list[str]:
        return [term.strip() for term in self.q.split(",") if term.strip()]
