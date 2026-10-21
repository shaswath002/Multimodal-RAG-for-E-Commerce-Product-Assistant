"""
UrbanPick Backend — Comprehensive End-to-End Test Suite.

Covers:
  - Schema validation (valid and invalid inputs)
  - Agent reasoning service (Ollama path + fallback)
  - Encoder and retriever unit tests
  - FastAPI endpoints via TestClient
    * Health checks
    * Product ingestion (success, duplicate, invalid)
    * Product retrieval (get, not found)
    * Product deletion
    * Text search (relevance, price filter, category filter)
    * Image search
    * Multimodal (text + image) search
    * Empty result handling
    * Error handling

Run:
    python -m pytest test_backend.py -v
    # or directly:
    python test_backend.py
"""

import io
import json
import sys
from typing import Dict, Any

import pytest
from PIL import Image
from fastapi.testclient import TestClient

from main import app
from schemas import ProductIngestSchema, StorePrice, SearchResponseSchema
from rag.encoder import MultimodalEncoder
from rag.retriever import VectorRetriever, get_retriever
from services.agent_reasoning import generate_grounded_response


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_image_bytes(color=(255, 0, 0), size=(100, 100), fmt="JPEG") -> bytes:
    img = Image.new("RGB", size, color=color)
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    return buf.getvalue()


SAMPLE_PRODUCT: Dict[str, Any] = {
    "product_id": "test-sony-xm5",
    "title": "Sony WH-1000XM5 Wireless Noise Cancelling Headphones",
    "brand": "Sony",
    "category": "Over-Ear Headphones",
    "specs": "30hr battery, LDAC, Multipoint, over-ear noise cancelling",
    "image_url": None,  # skip image download in tests
    "current_price": 24990.0,
    "original_price": 34990.0,
    "rating": 4.7,
    "availability": "In Stock",
    "store": "Amazon",
    "store_availability": [
        {"store": "Amazon", "price": 24990.0, "url": "https://amazon.in/test"}
    ],
    "price_history": [{"date": "2024-10-01", "price": 24990.0}],
}

SAMPLE_PRODUCT_2: Dict[str, Any] = {
    "product_id": "test-boat-rockerz",
    "title": "boAt Rockerz 450 Wireless Bluetooth Over-Ear Headphones",
    "brand": "boAt",
    "category": "Over-Ear Headphones",
    "specs": "40mm drivers, 15hr battery, Bluetooth 5.0, foldable, built-in mic",
    "image_url": None,
    "current_price": 999.0,
    "original_price": 3990.0,
    "rating": 4.1,
    "availability": "In Stock",
    "store": "Flipkart",
    "store_availability": [],
    "price_history": [],
}

SAMPLE_EARBUDS: Dict[str, Any] = {
    "product_id": "test-airpods-pro",
    "title": "Apple AirPods Pro 2nd Generation TWS Earbuds",
    "brand": "Apple",
    "category": "In-Ear Earbuds",
    "specs": "ANC, Transparency mode, H2 chip, in-ear TWS earbuds, 30hr total",
    "image_url": None,
    "current_price": 19900.0,
    "original_price": 24900.0,
    "rating": 4.8,
    "availability": "In Stock",
    "store": "Apple Store",
    "store_availability": [],
    "price_history": [],
}


# ---------------------------------------------------------------------------
# 0. Schema Validation Tests
# ---------------------------------------------------------------------------


def test_schema_valid_product():
    print("\n--- 0a. Schema: valid product ---")
    p = ProductIngestSchema(**SAMPLE_PRODUCT)
    assert p.product_id == "test-sony-xm5"
    assert p.current_price == 24990.0
    # Auto-computed discount
    expected_discount = round((34990 - 24990) / 34990 * 100, 2)
    assert abs(p.discount - expected_discount) < 0.01
    print(f"[OK] Valid product, auto-discount={p.discount}%")


def test_schema_rejects_placeholder_title():
    print("\n--- 0b. Schema: rejects placeholder title ---")
    with pytest.raises(Exception):
        ProductIngestSchema(**{**SAMPLE_PRODUCT, "title": "string"})
    print("[OK] 'string' title rejected")


def test_schema_rejects_negative_price():
    print("\n--- 0c. Schema: rejects negative price ---")
    with pytest.raises(Exception):
        ProductIngestSchema(**{**SAMPLE_PRODUCT, "current_price": -1})
    print("[OK] negative price rejected")


def test_schema_rejects_rating_above_5():
    print("\n--- 0d. Schema: rejects rating > 5 ---")
    with pytest.raises(Exception):
        ProductIngestSchema(**{**SAMPLE_PRODUCT, "rating": 6.0})
    print("[OK] rating > 5 rejected")


def test_schema_rejects_discount_above_100():
    print("\n--- 0e. Schema: rejects discount > 100 ---")
    with pytest.raises(Exception):
        ProductIngestSchema(**{**SAMPLE_PRODUCT, "discount": 150})
    print("[OK] discount > 100 rejected")


def test_schema_invalid_image_url():
    print("\n--- 0f. Schema: rejects non-HTTP image URL ---")
    with pytest.raises(Exception):
        ProductIngestSchema(**{**SAMPLE_PRODUCT, "image_url": "ftp://bad-url.com/image.jpg"})
    print("[OK] FTP image URL rejected")


def test_schema_none_image_url_ok():
    print("\n--- 0g. Schema: None image_url accepted ---")
    p = ProductIngestSchema(**{**SAMPLE_PRODUCT, "image_url": None})
    assert p.image_url is None
    print("[OK] None image_url accepted")


# ---------------------------------------------------------------------------
# 1. Agent Reasoning Tests
# ---------------------------------------------------------------------------


def test_agent_reasoning_fallback_no_products():
    print("\n--- 1a. Agent reasoning: fallback, no products ---")
    res = generate_grounded_response("earphones", [])
    assert "summary" in res
    assert "comparison_table" in res
    assert res["comparison_table"] == []
    print(f"[OK] Empty fallback: '{res['summary'][:80]}'")


def test_agent_reasoning_fallback_with_products():
    print("\n--- 1b. Agent reasoning: fallback with product list ---")
    mock = [
        {
            "product_id": "P1",
            "title": "Bose QC45",
            "brand": "Bose",
            "current_price": 22900,
            "specs": "ANC, 24hr battery",
            "rating": 4.6,
            "similarity_score": 0.92,
        }
    ]
    res = generate_grounded_response("noise cancelling headphones", mock)
    assert "summary" in res
    assert isinstance(res["comparison_table"], list)
    assert len(res["comparison_table"]) >= 1
    print(f"[OK] Summary: '{res['summary'][:80]}'")
    print(f"[OK] Table rows: {len(res['comparison_table'])}")


# ---------------------------------------------------------------------------
# 2. Encoder and Retriever Unit Tests
# ---------------------------------------------------------------------------


def test_encoder_text():
    print("\n--- 2a. Encoder: text embedding ---")
    enc = MultimodalEncoder()
    vec = enc.encode_text("Wireless noise cancelling headphones")
    assert len(vec) > 0, "Vector must not be empty"
    # Check L2 norm ≈ 1
    import math
    norm = math.sqrt(sum(x * x for x in vec))
    assert abs(norm - 1.0) < 1e-3, f"Vector not normalized: norm={norm}"
    print(f"[OK] Text vector dim={len(vec)}, norm≈{norm:.6f}")


def test_encoder_image():
    print("\n--- 2b. Encoder: image embedding ---")
    enc = MultimodalEncoder()
    img_bytes = make_image_bytes()
    vec = enc.encode_image(img_bytes)
    assert len(vec) > 0
    import math
    norm = math.sqrt(sum(x * x for x in vec))
    assert abs(norm - 1.0) < 1e-3
    print(f"[OK] Image vector dim={len(vec)}, norm≈{norm:.6f}")


def test_encoder_text_image_same_dim():
    print("\n--- 2c. Encoder: text and image share same dimension ---")
    enc = MultimodalEncoder()
    text_vec = enc.encode_text("headphones")
    img_vec = enc.encode_image(make_image_bytes())
    assert len(text_vec) == len(img_vec), (
        f"Dimension mismatch: text={len(text_vec)}, image={len(img_vec)}"
    )
    print(f"[OK] Both vectors have dim={len(text_vec)}")


def test_retriever_upsert_and_retrieve():
    print("\n--- 2d. Retriever: upsert and retrieve ---")
    enc = MultimodalEncoder()
    retriever = VectorRetriever()

    headphone_vec = enc.encode_text("wireless noise cancelling headphones Sony")
    mouse_vec = enc.encode_text("ergonomic wireless mouse Logitech")

    # Use unique IDs to avoid polluting the main index
    headphone_data = {**SAMPLE_PRODUCT, "product_id": "unit-test-headphone"}
    mouse_data = {
        "product_id": "unit-test-mouse",
        "title": "Logitech MX Master 3S Wireless Mouse",
        "brand": "Logitech",
        "category": "Mouse",
        "specs": "Ergonomic 8K DPI sensor, quiet click",
        "current_price": 9999.0,
        "original_price": 9999.0,
        "rating": 4.8,
        "availability": "In Stock",
        "store": "Amazon",
        "store_availability": [],
        "price_history": [],
    }

    retriever.add_product(headphone_data, headphone_vec)
    retriever.add_product(mouse_data, mouse_vec)

    results = retriever.retrieve(query_vector=headphone_vec, top_k=5)
    assert len(results) >= 1
    # Top result should be the headphone
    assert results[0]["product_id"] == "unit-test-headphone", (
        f"Expected headphone on top, got: {results[0]['product_id']}"
    )
    print(
        f"[OK] Top result: '{results[0]['title']}' "
        f"score={results[0]['similarity_score']}"
    )


def test_retriever_price_filter():
    print("\n--- 2e. Retriever: price filter ---")
    retriever = VectorRetriever()
    enc = MultimodalEncoder()

    retriever.add_product(
        {**SAMPLE_PRODUCT, "product_id": "pf-expensive", "current_price": 50000.0},
        enc.encode_text("premium headphones"),
    )
    retriever.add_product(
        {**SAMPLE_PRODUCT_2, "product_id": "pf-cheap", "current_price": 500.0},
        enc.encode_text("budget headphones"),
    )

    query_vec = enc.encode_text("headphones")
    results = retriever.retrieve(query_vector=query_vec, top_k=10, max_price=5000.0)

    # Expensive product must be filtered out
    ids = [r["product_id"] for r in results]
    assert "pf-expensive" not in ids, "Product above max_price must be excluded"
    print(f"[OK] Price filter ≤5000: returned IDs={ids}")


def test_retriever_similarity_scores_positive():
    print("\n--- 2f. Retriever: similarity scores ≥ 0 ---")
    retriever = VectorRetriever()
    enc = MultimodalEncoder()

    retriever.add_product(
        {**SAMPLE_PRODUCT, "product_id": "score-test"},
        enc.encode_text("test headphone product"),
    )

    query_vec = enc.encode_image(make_image_bytes(color=(0, 128, 255)))
    results = retriever.retrieve(query_vector=query_vec, top_k=5)

    for r in results:
        score = r["similarity_score"]
        assert 0.0 <= score <= 1.0, f"Score out of [0,1]: {score} for {r['product_id']}"
    print(f"[OK] All {len(results)} scores in [0,1]: {[r['similarity_score'] for r in results]}")


def test_retriever_store_availability_roundtrip():
    print("\n--- 2g. Retriever: store_availability JSON roundtrip ---")
    retriever = VectorRetriever()
    enc = MultimodalEncoder()

    product_with_stores = {
        **SAMPLE_PRODUCT,
        "product_id": "roundtrip-test",
        "store_availability": [
            {"store": "Amazon", "price": 24990, "url": "https://amazon.in"},
            {"store": "Flipkart", "price": 25490, "url": "https://flipkart.com"},
        ],
    }
    vec = enc.encode_text("roundtrip test product")
    retriever.add_product(product_with_stores, vec)

    results = retriever.retrieve(query_vector=vec, top_k=5)
    matching = [r for r in results if r["product_id"] == "roundtrip-test"]
    assert matching, "Roundtrip product not found in results"

    stores = matching[0].get("store_availability", [])
    assert isinstance(stores, list), f"store_availability should be a list, got {type(stores)}"
    assert len(stores) == 2
    print(f"[OK] store_availability roundtrip: {stores}")


# ---------------------------------------------------------------------------
# 3. FastAPI Endpoint Tests (TestClient)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_health_root(client):
    print("\n--- 3a. GET / ---")
    resp = client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert "indexed_products" in data
    print(f"[OK] {data}")


def test_health_detailed(client):
    print("\n--- 3b. GET /api/v1/health ---")
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    data = resp.json()
    assert "encoder" in data
    assert "chromadb" in data
    assert "ollama" in data
    print(f"[OK] Health: encoder_loaded={data['encoder']['loaded']}, "
          f"ollama_reachable={data['ollama']['reachable']}")


def test_ingest_product(client):
    print("\n--- 3c. POST /api/v1/ingest ---")
    resp = client.post("/api/v1/ingest", json=SAMPLE_PRODUCT)
    assert resp.status_code == 201, f"Ingest failed: {resp.text}"
    data = resp.json()
    assert data["status"] == "success"
    assert data["product_id"] == SAMPLE_PRODUCT["product_id"]
    assert data["vector_dimension"] > 0
    print(f"[OK] Ingested: {data}")


def test_ingest_updates_existing(client):
    print("\n--- 3d. POST /api/v1/ingest (update via upsert) ---")
    updated = {**SAMPLE_PRODUCT, "current_price": 22000.0}
    resp = client.post("/api/v1/ingest", json=updated)
    assert resp.status_code == 201

    # Verify update
    resp2 = client.get(f"/api/v1/products/{SAMPLE_PRODUCT['product_id']}")
    assert resp2.status_code == 200
    meta = resp2.json()
    assert meta["current_price"] == 22000.0, f"Price not updated: {meta['current_price']}"
    print(f"[OK] Price updated to {meta['current_price']}")

    # Restore original price
    client.post("/api/v1/ingest", json=SAMPLE_PRODUCT)


def test_ingest_invalid_placeholder_rejected(client):
    print("\n--- 3e. POST /api/v1/ingest (placeholder title rejected) ---")
    bad = {**SAMPLE_PRODUCT, "product_id": "invalid-test", "title": "string"}
    resp = client.post("/api/v1/ingest", json=bad)
    assert resp.status_code == 422, f"Expected 422, got {resp.status_code}: {resp.text}"
    print(f"[OK] Placeholder title rejected with 422")


def test_ingest_negative_price_rejected(client):
    print("\n--- 3f. POST /api/v1/ingest (negative price rejected) ---")
    bad = {**SAMPLE_PRODUCT, "product_id": "neg-price-test", "current_price": -100}
    resp = client.post("/api/v1/ingest", json=bad)
    assert resp.status_code == 422
    print(f"[OK] Negative price rejected with 422")


def test_ingest_second_product(client):
    print("\n--- 3g. Ingest second product (budget) ---")
    resp = client.post("/api/v1/ingest", json=SAMPLE_PRODUCT_2)
    assert resp.status_code == 201
    print(f"[OK] {resp.json()['message']}")


def test_ingest_earbuds(client):
    print("\n--- 3h. Ingest earbuds product ---")
    resp = client.post("/api/v1/ingest", json=SAMPLE_EARBUDS)
    assert resp.status_code == 201
    print(f"[OK] {resp.json()['message']}")


def test_get_product_exists(client):
    print("\n--- 3i. GET /api/v1/products/{id} ---")
    pid = SAMPLE_PRODUCT["product_id"]
    resp = client.get(f"/api/v1/products/{pid}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["product_id"] == pid
    assert isinstance(data.get("store_availability"), list)
    print(f"[OK] Product '{pid}' retrieved, store_availability={data['store_availability']}")


def test_get_product_not_found(client):
    print("\n--- 3j. GET /api/v1/products/{id} (not found) ---")
    resp = client.get("/api/v1/products/nonexistent-product-xyz-123")
    assert resp.status_code == 404
    print(f"[OK] 404 returned for non-existent product")


def test_text_search_returns_results(client):
    print("\n--- 3k. POST /api/v1/search (text only) ---")
    resp = client.post(
        "/api/v1/search",
        data={"text_prompt": "wireless noise cancelling headphones", "top_k": "3"},
    )
    assert resp.status_code == 200, f"Search failed: {resp.text}"
    data = resp.json()
    assert len(data["recommended_products"]) > 0
    assert data["search_type"] == "text"
    assert data["total_results"] == len(data["recommended_products"])
    top = data["recommended_products"][0]
    print(
        f"[OK] Text search: {data['total_results']} result(s). "
        f"Top: '{top['title']}' score={top['similarity_score']}"
    )


def test_text_search_price_filter(client):
    print("\n--- 3l. POST /api/v1/search (text + price filter ≤1500) ---")
    resp = client.post(
        "/api/v1/search",
        data={"text_prompt": "headphones", "max_price": "1500", "top_k": "10"},
    )
    assert resp.status_code == 200
    data = resp.json()
    for product in data["recommended_products"]:
        price = product["current_price"]
        assert price <= 1500.0, (
            f"Product '{product['title']}' with price {price} "
            f"should have been filtered out (max_price=1500)"
        )
    print(
        f"[OK] Price filter ≤1500: {data['total_results']} result(s) "
        f"with prices: {[p['current_price'] for p in data['recommended_products']]}"
    )


def test_text_search_category_filter(client):
    print("\n--- 3m. POST /api/v1/search (text + category filter) ---")
    resp = client.post(
        "/api/v1/search",
        data={
            "text_prompt": "earphones",
            "category": "In-Ear Earbuds",
            "top_k": "5",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    for product in data["recommended_products"]:
        cat = product.get("category", "").lower()
        assert "in-ear" in cat or "earbud" in cat, (
            f"Product '{product['title']}' has category '{product['category']}' "
            "which doesn't match 'In-Ear Earbuds' filter"
        )
    print(
        f"[OK] Category filter 'In-Ear Earbuds': {data['total_results']} result(s)"
    )


def test_text_search_no_input_rejected(client):
    print("\n--- 3n. POST /api/v1/search (no input) ---")
    resp = client.post("/api/v1/search", data={"top_k": "5"})
    assert resp.status_code == 400
    print(f"[OK] 400 returned: {resp.json()['detail']}")


def test_text_search_whitespace_prompt_rejected(client):
    print("\n--- 3o. POST /api/v1/search (whitespace prompt) ---")
    resp = client.post("/api/v1/search", data={"text_prompt": "   ", "top_k": "5"})
    assert resp.status_code == 400
    print(f"[OK] 400 returned for whitespace-only prompt")


def test_image_search(client):
    print("\n--- 3p. POST /api/v1/search (image only) ---")
    img_bytes = make_image_bytes(color=(200, 100, 50))
    resp = client.post(
        "/api/v1/search",
        data={"top_k": "3"},
        files={"image_file": ("test.jpg", img_bytes, "image/jpeg")},
    )
    assert resp.status_code == 200, f"Image search failed: {resp.text}"
    data = resp.json()
    assert data["search_type"] == "image"
    print(f"[OK] Image search: {data['total_results']} result(s)")
    for r in data["recommended_products"]:
        assert 0.0 <= r["similarity_score"] <= 1.0, (
            f"Score out of range: {r['similarity_score']}"
        )
    print(f"[OK] All scores in [0, 1]")


def test_multimodal_search(client):
    print("\n--- 3q. POST /api/v1/search (text + image) ---")
    img_bytes = make_image_bytes(color=(0, 200, 100))
    resp = client.post(
        "/api/v1/search",
        data={"text_prompt": "noise cancelling headphones", "top_k": "3"},
        files={"image_file": ("product.jpg", img_bytes, "image/jpeg")},
    )
    assert resp.status_code == 200, f"Multimodal search failed: {resp.text}"
    data = resp.json()
    assert data["search_type"] == "multimodal"
    assert "ai_analysis" in data
    assert "comparison_table" in data
    print(
        f"[OK] Multimodal search: {data['total_results']} result(s). "
        f"AI analysis snippet: '{data['ai_analysis'][:80]}'"
    )


def test_image_upload_wrong_format_rejected(client):
    print("\n--- 3r. POST /api/v1/search (unsupported image format) ---")
    resp = client.post(
        "/api/v1/search",
        data={"top_k": "3"},
        files={"image_file": ("file.pdf", b"%PDF-1.4 fake pdf content", "application/pdf")},
    )
    assert resp.status_code == 400
    print(f"[OK] Unsupported format rejected: {resp.json()['detail']}")


def test_ai_analysis_not_empty(client):
    print("\n--- 3s. Search: AI analysis not empty ---")
    resp = client.post(
        "/api/v1/search",
        data={"text_prompt": "Sony headphones", "top_k": "2"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["ai_analysis"], "ai_analysis must not be empty"
    assert len(data["ai_analysis"]) > 10
    print(f"[OK] AI analysis: '{data['ai_analysis'][:100]}'")


def test_delete_product(client):
    print("\n--- 3t. DELETE /api/v1/products/{id} ---")
    # Ingest a temporary product
    temp = {
        **SAMPLE_PRODUCT,
        "product_id": "temp-delete-test",
        "title": "Temporary Delete Test Product",
    }
    ingest_resp = client.post("/api/v1/ingest", json=temp)
    assert ingest_resp.status_code == 201

    # Delete it
    del_resp = client.delete(f"/api/v1/products/{temp['product_id']}")
    assert del_resp.status_code == 200
    assert del_resp.json()["status"] == "success"

    # Confirm it's gone
    get_resp = client.get(f"/api/v1/products/{temp['product_id']}")
    assert get_resp.status_code == 404
    print(f"[OK] Product deleted and confirmed gone")


def test_delete_nonexistent_returns_404(client):
    print("\n--- 3u. DELETE /api/v1/products/{id} (not found) ---")
    resp = client.delete("/api/v1/products/definitely-does-not-exist-xyz")
    assert resp.status_code == 404
    print(f"[OK] 404 for non-existent product delete")


# ---------------------------------------------------------------------------
# 4. Relevance smoke tests (requires ingested catalog)
# ---------------------------------------------------------------------------


def test_sony_query_ranks_sony_first(client):
    print("\n--- 4a. Relevance: 'Sony headphones' → Sony product first ---")
    resp = client.post(
        "/api/v1/search",
        data={"text_prompt": "Sony WH-1000XM5 headphones", "top_k": "5"},
    )
    assert resp.status_code == 200
    results = resp.json()["recommended_products"]
    assert len(results) > 0
    top = results[0]
    # Be lenient: Sony should appear in top 2
    top_brands = [r["brand"].lower() for r in results[:2]]
    assert "sony" in top_brands, (
        f"Expected Sony in top 2, got brands: {[r['brand'] for r in results[:2]]}"
    )
    print(f"[OK] Top result: '{top['title']}' (score={top['similarity_score']})")


def test_budget_query_returns_cheap_products(client):
    print("\n--- 4b. Relevance: price filter ≤1500 returns budget products ---")
    resp = client.post(
        "/api/v1/search",
        data={"text_prompt": "budget wireless headphones", "max_price": "1500", "top_k": "5"},
    )
    assert resp.status_code == 200
    results = resp.json()["recommended_products"]
    for r in results:
        assert r["current_price"] <= 1500.0, (
            f"'{r['title']}' at ₹{r['current_price']} should be filtered"
        )
    print(
        f"[OK] Budget filter: {len(results)} result(s), "
        f"prices: {[r['current_price'] for r in results]}"
    )


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    print("=" * 60)
    print("UrbanPick Backend — End-to-End Test Suite")
    print("=" * 60)

    tests = [
        # Schema
        test_schema_valid_product,
        test_schema_rejects_placeholder_title,
        test_schema_rejects_negative_price,
        test_schema_rejects_rating_above_5,
        test_schema_rejects_discount_above_100,
        test_schema_invalid_image_url,
        test_schema_none_image_url_ok,
        # Reasoning
        test_agent_reasoning_fallback_no_products,
        test_agent_reasoning_fallback_with_products,
        # Encoder + retriever
        test_encoder_text,
        test_encoder_image,
        test_encoder_text_image_same_dim,
        test_retriever_upsert_and_retrieve,
        test_retriever_price_filter,
        test_retriever_similarity_scores_positive,
        test_retriever_store_availability_roundtrip,
    ]

    with TestClient(app) as client_instance:
        api_tests = [
            lambda: test_health_root(client_instance),
            lambda: test_health_detailed(client_instance),
            lambda: test_ingest_product(client_instance),
            lambda: test_ingest_updates_existing(client_instance),
            lambda: test_ingest_invalid_placeholder_rejected(client_instance),
            lambda: test_ingest_negative_price_rejected(client_instance),
            lambda: test_ingest_second_product(client_instance),
            lambda: test_ingest_earbuds(client_instance),
            lambda: test_get_product_exists(client_instance),
            lambda: test_get_product_not_found(client_instance),
            lambda: test_text_search_returns_results(client_instance),
            lambda: test_text_search_price_filter(client_instance),
            lambda: test_text_search_category_filter(client_instance),
            lambda: test_text_search_no_input_rejected(client_instance),
            lambda: test_text_search_whitespace_prompt_rejected(client_instance),
            lambda: test_image_search(client_instance),
            lambda: test_multimodal_search(client_instance),
            lambda: test_image_upload_wrong_format_rejected(client_instance),
            lambda: test_ai_analysis_not_empty(client_instance),
            lambda: test_delete_product(client_instance),
            lambda: test_delete_nonexistent_returns_404(client_instance),
            lambda: test_sony_query_ranks_sony_first(client_instance),
            lambda: test_budget_query_returns_cheap_products(client_instance),
        ]

        passed = 0
        failed = 0
        errors = []

        all_tests = tests + api_tests

        for test_fn in all_tests:
            name = getattr(test_fn, "__name__", str(test_fn))
            try:
                test_fn()
                passed += 1
            except Exception as exc:
                failed += 1
                errors.append((name, str(exc)))
                print(f"  [FAIL] {name}: {exc}")

    print(f"\n{'=' * 60}")
    print(f"Results: {passed} passed, {failed} failed out of {len(all_tests)} tests")
    if errors:
        print("\nFailed tests:")
        for name, err in errors:
            print(f"  • {name}: {err}")
        sys.exit(1)
    else:
        print("\n✓ ALL TESTS PASSED")
