"""
Persistent Vector Retriever using ChromaDB.

Design notes:
- Uses cosine distance space ("hnsw:space": "cosine").
- ChromaDB cosine distance is in [0, 2]:
    0 = identical vectors, 1 = orthogonal, 2 = opposite.
- similarity_score = 1 - distance, then clamped to [0.0, 1.0] so
  users never see confusing negative numbers.
- Complex fields (store_availability, price_history) are serialized to
  JSON strings because ChromaDB metadata only supports flat types.
"""

import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

import chromadb

from config import settings

logger = logging.getLogger(__name__)

# Fetch extra results before applying post-query filters.
OVER_FETCH_MULTIPLIER = 5
OVER_FETCH_MIN = 25


class VectorRetriever:

    def __init__(self):
        self.client = chromadb.PersistentClient(path=settings.CHROMA_DB_PATH)

        # Cosine distance space — all embeddings must be normalized.
        self.collection = self.client.get_or_create_collection(
            name="products",
            metadata={"hnsw:space": "cosine"},
        )

        logger.info(
            "VectorRetriever ready. Indexed products: %d",
            self.collection.count(),
        )

    # ------------------------------------------------------------------
    # Add / update
    # ------------------------------------------------------------------

    def add_product(self, product_data: Dict[str, Any], vector: List[float]) -> None:
        """Insert or update (upsert) a product in ChromaDB."""

        product_id = str(product_data["product_id"]).strip()

        # Serialize complex fields to JSON strings for ChromaDB compatibility.
        store_availability_json = json.dumps(
            product_data.get("store_availability") or [], ensure_ascii=False
        )
        price_history_json = json.dumps(
            product_data.get("price_history") or [], ensure_ascii=False
        )

        metadata = {
            "product_id": product_id,
            "title": str(product_data.get("title", "") or ""),
            "brand": str(product_data.get("brand", "") or ""),
            "category": str(product_data.get("category", "") or ""),
            "specs": str(product_data.get("specs", "") or ""),
            "current_price": float(product_data.get("current_price", 0) or 0),
            "original_price": float(product_data.get("original_price", 0) or 0),
            "discount": float(product_data.get("discount", 0) or 0),
            "rating": float(product_data.get("rating", 0) or 0),
            "availability": str(product_data.get("availability", "In Stock") or "In Stock"),
            "store": str(product_data.get("store", "") or ""),
            "image_url": str(product_data.get("image_url", "") or ""),
            "store_availability": store_availability_json,
            "price_history": price_history_json,
            "indexed_at": datetime.utcnow().isoformat(),
        }

        # Human-readable document text used by ChromaDB for BM25 fallback.
        document = (
            f"Product: {metadata['title']}\n"
            f"Brand: {metadata['brand']}\n"
            f"Category: {metadata['category']}\n"
            f"Price: {metadata['current_price']}\n"
            f"Specifications: {metadata['specs']}\n"
            f"Availability: {metadata['availability']}"
        )

        self.collection.upsert(
            ids=[product_id],
            embeddings=[vector],
            metadatas=[metadata],
            documents=[document],
        )

        logger.info(
            "Upserted product '%s' (%s). Total indexed: %d",
            product_id,
            metadata["title"],
            self.collection.count(),
        )

    # ------------------------------------------------------------------
    # Retrieve
    # ------------------------------------------------------------------

    def retrieve(
        self,
        query_vector: List[float],
        top_k: int = 5,
        max_price: Optional[float] = None,
        category: Optional[str] = None,
        query_text: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant products with semantic similarity + optional filters.

        Filters applied (post-query):
        - max_price: exclude products whose current_price > max_price
        - category: substring match (case-insensitive)
        - query_text: keyword guards for over-ear / in-ear form factors

        Returns products sorted by descending similarity_score (best first).
        """

        total = self.collection.count()

        if total == 0 or top_k <= 0:
            logger.info("Retrieve called on empty collection or top_k=0.")
            return []

        # Detect form-factor constraints from the query text.
        query_lower = (query_text or "").casefold().replace("-", " ")
        requires_over_ear = "over ear" in query_lower
        requires_in_ear = any(
            kw in query_lower for kw in ("in ear", "earbuds", "earphones", "tws")
        )

        needs_filtering = (
            max_price is not None
            or bool(category and category.strip())
            or requires_over_ear
            or requires_in_ear
        )

        # Over-fetch before filtering.
        n_results = min(
            total,
            max(top_k * OVER_FETCH_MULTIPLIER, OVER_FETCH_MIN)
            if needs_filtering
            else top_k,
        )

        raw = self.collection.query(
            query_embeddings=[query_vector],
            n_results=n_results,
            include=["metadatas", "distances"],
        )

        metadatas: List[Dict] = raw.get("metadatas", [[]])[0]
        distances: List[float] = raw.get("distances", [[]])[0]

        products: List[Dict[str, Any]] = []

        for meta, dist in zip(metadatas, distances):
            if meta is None:
                continue

            # --- price filter ---
            try:
                price = float(meta.get("current_price", 0) or 0)
            except (TypeError, ValueError):
                price = 0.0

            if max_price is not None and price > max_price:
                continue

            # --- category filter ---
            product_category = str(meta.get("category", "")).casefold()
            if category and category.strip():
                if category.strip().casefold() not in product_category:
                    continue

            # --- form-factor keyword filters ---
            title = str(meta.get("title", "")).casefold().replace("-", " ")
            specs = str(meta.get("specs", "")).casefold().replace("-", " ")
            details = f"{title} {specs}"

            if requires_over_ear and "over ear" not in details:
                continue

            if requires_in_ear and not any(
                kw in details for kw in ("in ear", "earbud", "earphone", "tws")
            ):
                continue

            # --- similarity score ---
            # ChromaDB cosine distance ∈ [0, 2]; clamp score to [0, 1].
            similarity = max(0.0, min(1.0, 1.0 - float(dist)))

            product = dict(meta)
            product["similarity_score"] = round(similarity, 4)

            # Deserialize JSON fields back to Python structures.
            for field in ("store_availability", "price_history"):
                raw_val = product.get(field, "[]")
                try:
                    product[field] = json.loads(raw_val) if isinstance(raw_val, str) else raw_val
                except (json.JSONDecodeError, TypeError):
                    product[field] = []

            products.append(product)

            if len(products) >= top_k:
                break

        logger.info(
            "Retrieve: %d product(s) returned (top_k=%d, indexed=%d, "
            "max_price=%s, category=%s).",
            len(products),
            top_k,
            total,
            max_price,
            category,
        )

        return products

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    def delete_product(self, product_id: str) -> bool:
        """
        Delete one product by ID.

        Returns True if deleted, False if not found.
        """
        product_id = str(product_id).strip()

        if not product_id:
            raise ValueError("product_id cannot be empty.")

        existing = self.collection.get(ids=[product_id], include=["metadatas"])

        if not existing.get("ids"):
            logger.info("Delete requested for '%s' — not found.", product_id)
            return False

        self.collection.delete(ids=[product_id])
        logger.info(
            "Deleted product '%s'. Remaining: %d",
            product_id,
            self.collection.count(),
        )
        return True

    # ------------------------------------------------------------------
    # Clear (dangerous)
    # ------------------------------------------------------------------

    def _clear_for_tests(self) -> None:
        """
        Delete the entire products collection and recreate it empty.

        **Private — do not call from application code.**
        This exists solely for test teardown. The public API surface for
        clearing the catalog is ``DELETE /api/v1/admin/clear``.

        WARNING: Irreversible. Only use to reset the catalog deliberately.
        """
        self.client.delete_collection(name="products")
        self.collection = self.client.get_or_create_collection(
            name="products",
            metadata={"hnsw:space": "cosine"},
        )
        logger.warning("Products collection cleared and recreated empty.")


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_retriever: Optional[VectorRetriever] = None


def get_retriever() -> VectorRetriever:
    """Return the shared singleton VectorRetriever instance."""
    global _retriever
    if _retriever is None:
        _retriever = VectorRetriever()
    return _retriever
