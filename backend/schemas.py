"""
Pydantic Schemas for Multimodal Agentic RAG E-Commerce Platform.

Validation rules:
- Required fields: product_id, title, brand, specs, current_price
- Numeric ranges: price >= 0, rating 0–5, discount 0–100
- String guards: no empty / placeholder values for critical fields
- image_url: optional (download may fail gracefully)
"""

import re
from typing import List, Optional, Dict, Any

from pydantic import BaseModel, Field, field_validator, model_validator


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_PLACEHOLDER_PATTERNS = re.compile(
    r"^(string|none|null|undefined|test|placeholder|example|sample|n/a|na)$",
    re.IGNORECASE,
)


def _reject_placeholder(value: str, field_name: str) -> str:
    """Reject obviously invalid placeholder strings."""
    stripped = value.strip()
    if not stripped:
        raise ValueError(f"'{field_name}' must not be empty.")
    if _PLACEHOLDER_PATTERNS.match(stripped):
        raise ValueError(
            f"'{field_name}' looks like a placeholder value ('{stripped}'). "
            "Please provide a real value."
        )
    return stripped


# ---------------------------------------------------------------------------
# Sub-schemas
# ---------------------------------------------------------------------------


class StorePrice(BaseModel):
    store: str = Field(..., description="Store name (Amazon, Flipkart, Nykaa, etc.)")
    price: float = Field(..., ge=0, description="Current price at the store")
    url: str = Field(..., description="Product URL at the store")

    @field_validator("store")
    @classmethod
    def validate_store(cls, v: str) -> str:
        return _reject_placeholder(v, "store")


# ---------------------------------------------------------------------------
# Product Ingest Schema
# ---------------------------------------------------------------------------


class ProductIngestSchema(BaseModel):

    # ── Basic Info ──────────────────────────────────────────────────────────

    product_id: str = Field(..., description="Unique Product ID (UUID or slug)")
    title: str = Field(..., min_length=3, description="Product title")
    brand: str = Field(..., min_length=1, description="Brand name")
    category: Optional[str] = Field(default="", description="Product category")
    specs: str = Field(..., min_length=5, description="Product specifications")

    # ── Image ───────────────────────────────────────────────────────────────

    image_url: Optional[str] = Field(
        default=None,
        description="Main product image URL (optional; image download is best-effort)",
    )

    # ── Pricing ─────────────────────────────────────────────────────────────

    current_price: float = Field(..., ge=0, description="Current selling price (>= 0)")
    original_price: Optional[float] = Field(default=None, ge=0, description="Original / MRP price")
    discount: Optional[float] = Field(
        default=None,
        ge=0,
        le=100,
        description="Discount percentage (0–100)",
    )

    # ── Rating & Availability ───────────────────────────────────────────────

    rating: Optional[float] = Field(
        default=None,
        ge=0,
        le=5,
        description="Average rating (0–5)",
    )
    availability: Optional[str] = Field(
        default="In Stock",
        description="Stock status (In Stock / Out of Stock / etc.)",
    )
    store: Optional[str] = Field(default="", description="Primary store name")

    # ── Multi-store prices ──────────────────────────────────────────────────

    store_availability: List[StorePrice] = Field(
        default_factory=list,
        description="Prices and links from multiple stores",
    )

    # ── Price history ───────────────────────────────────────────────────────

    price_history: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Historical price records [{date, price}]",
    )

    # ── Validators ──────────────────────────────────────────────────────────

    @field_validator("product_id")
    @classmethod
    def validate_product_id(cls, v: str) -> str:
        return _reject_placeholder(v, "product_id")

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        return _reject_placeholder(v, "title")

    @field_validator("brand")
    @classmethod
    def validate_brand(cls, v: str) -> str:
        return _reject_placeholder(v, "brand")

    @field_validator("specs")
    @classmethod
    def validate_specs(cls, v: str) -> str:
        return _reject_placeholder(v, "specs")

    @field_validator("image_url")
    @classmethod
    def validate_image_url(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v.strip() == "":
            return None
        v = v.strip()
        if not (v.startswith("http://") or v.startswith("https://")):
            raise ValueError("image_url must be a valid HTTP/HTTPS URL.")
        return v

    @model_validator(mode="after")
    def derive_discount(self) -> "ProductIngestSchema":
        """Auto-compute discount if original_price is given but discount is not."""
        if (
            self.discount is None
            and self.original_price is not None
            and self.original_price > 0
            and self.current_price < self.original_price
        ):
            self.discount = round(
                (self.original_price - self.current_price) / self.original_price * 100,
                2,
            )
        return self


# ---------------------------------------------------------------------------
# Search Response Schema
# ---------------------------------------------------------------------------


class SearchResponseSchema(BaseModel):
    query: str = Field(..., description="Original user query or description")
    recommended_products: List[Dict[str, Any]] = Field(
        ..., description="Retrieved & ranked product list"
    )
    ai_analysis: str = Field(..., description="AI-generated grounded recommendation")
    comparison_table: List[Dict[str, Any]] = Field(
        ..., description="Structured side-by-side comparison"
    )
    total_results: int = Field(default=0, description="Number of products returned")
    search_type: str = Field(
        default="text",
        description="Search modality: 'text', 'image', or 'multimodal'",
    )