"""
UrbanPick — Multimodal Agentic RAG E-Commerce Backend.

Endpoints:
  GET  /                              Health check
  GET  /api/v1/health                 Detailed health check (Ollama, ChromaDB)
  POST /api/v1/ingest                 Ingest a product (API-key protected if configured)
  GET  /api/v1/products/{product_id}  Fetch a single product
  DELETE /api/v1/products/{product_id} Delete a product
  POST /api/v1/search                 Multimodal search (text / image / both)
"""

import logging
import json
import time
from contextlib import asynccontextmanager
from typing import Optional, List

import httpx
import numpy as np
from fastapi import (
    FastAPI,
    HTTPException,
    File,
    UploadFile,
    Form,
    Header,
    Query,
    Depends,
    Request,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from starlette.concurrency import run_in_threadpool

from config import settings
from schemas import ProductIngestSchema, SearchResponseSchema
from rag.encoder import MultimodalEncoder
from rag.retriever import get_retriever
from services.agent_reasoning import generate_grounded_response
from services.ollama_client import check_ollama_health


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("urbanpick")


# ---------------------------------------------------------------------------
# Shared application objects (initialised in lifespan)
# ---------------------------------------------------------------------------

encoder: Optional[MultimodalEncoder] = None
retriever = get_retriever()
http_client: Optional[httpx.AsyncClient] = None


# ---------------------------------------------------------------------------
# Rate limiter (slowapi)
# ---------------------------------------------------------------------------

limiter = Limiter(key_func=get_remote_address, default_limits=[])


async def _rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={"detail": f"Rate limit exceeded: {exc.detail}. Please slow down."},
    )


# ---------------------------------------------------------------------------
# Application lifespan
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI):
    global encoder, http_client

    # Shared HTTP client for all image downloads (ingest).
    http_client = httpx.AsyncClient(
        timeout=httpx.Timeout(10.0, connect=5.0),
        follow_redirects=True,
        limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
    )

    logger.info("Initialising MultimodalEncoder (%s)...", settings.EMBEDDING_MODEL_NAME)
    try:
        encoder = MultimodalEncoder(
            model_name=settings.EMBEDDING_MODEL_NAME,
            cache_maxsize=settings.EMBEDDING_CACHE_MAXSIZE,
            cache_ttl=settings.EMBEDDING_CACHE_TTL,
        )
        logger.info("MultimodalEncoder ready (text cache: maxsize=%d, ttl=%ds).",
                    settings.EMBEDDING_CACHE_MAXSIZE, settings.EMBEDDING_CACHE_TTL)
    except Exception:
        logger.exception("CRITICAL: MultimodalEncoder failed to load.")
        raise

    logger.info("Checking Ollama health...")
    ollama_status = await check_ollama_health(settings.OLLAMA_MODEL)
    if not ollama_status["reachable"]:
        logger.warning(
            "Ollama is NOT reachable at %s. "
            "AI reasoning will fall back to the deterministic template. "
            "Start Ollama with: ollama serve",
            settings.OLLAMA_BASE_URL,
        )
    elif not ollama_status["model_available"]:
        logger.warning(
            "Ollama is running but model '%s' is not pulled. "
            "Run: ollama pull %s",
            settings.OLLAMA_MODEL,
            settings.OLLAMA_MODEL,
        )
    else:
        logger.info("Ollama + model '%s' are ready.", settings.OLLAMA_MODEL)

    yield

    logger.info("UrbanPick backend shutting down.")
    if http_client:
        await http_client.aclose()
        logger.info("Shared HTTP client closed.")


# ---------------------------------------------------------------------------
# Health-check cache (15-second TTL — avoids a fresh blocking Ollama probe on
# every GET /api/v1/health while still surfacing recent status changes).
# ---------------------------------------------------------------------------

_HEALTH_TTL: float = 15.0
_health_cache: dict = {"data": None, "ts": 0.0}


async def _get_cached_ollama_health() -> dict:
    now = time.monotonic()
    if _health_cache["data"] is None or now - _health_cache["ts"] > _HEALTH_TTL:
        _health_cache["data"] = await check_ollama_health(settings.OLLAMA_MODEL)
        _health_cache["ts"] = now
    return _health_cache["data"]


# ---------------------------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------------------------

app = FastAPI(
    title="UrbanPick — Multimodal Agentic RAG E-Commerce API",
    description=(
        "Multimodal product assistant supporting text search, image search, "
        "product filtering, AI-generated comparisons and product ingestion."
    ),
    version="2.0.0",
    lifespan=lifespan,
)

# Wire up the rate-limiter and its 429 handler.
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def normalize_vector(v: List[float]) -> List[float]:
    """L2-normalize a vector to unit length."""
    arr = np.asarray(v, dtype=np.float32)
    norm = float(np.linalg.norm(arr))
    if norm > 1e-9:
        arr = arr / norm
    return arr.tolist()


def _require_encoder() -> MultimodalEncoder:
    """Dependency: raise 503 if encoder not ready."""
    if encoder is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MultimodalEncoder is not yet initialised. Please retry in a moment.",
        )
    return encoder


def _verify_ingest_api_key(x_api_key: Optional[str] = Header(default=None)) -> None:
    """
    Dependency: if INGEST_API_KEY is configured, require it in the X-Api-Key header.
    If the key is not configured, the endpoint is open (development mode).
    """
    configured_key = settings.INGEST_API_KEY.strip()
    if not configured_key:
        return  # No key configured → open access (dev mode)

    if x_api_key != configured_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-Api-Key header for ingestion.",
        )


def _validate_image_upload(contents: bytes, filename: str) -> None:
    """Raise 400 if image is empty, too large, or has an unsupported format."""
    if not contents:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded image is empty.",
        )

    max_bytes = int(settings.MAX_IMAGE_SIZE_MB * 1024 * 1024)
    if len(contents) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Image exceeds the maximum allowed size of "
                f"{settings.MAX_IMAGE_SIZE_MB} MB."
            ),
        )

    allowed_extensions = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp"}
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Unsupported image format '{ext}'. "
                f"Allowed: {', '.join(sorted(allowed_extensions))}."
            ),
        )


# ---------------------------------------------------------------------------
# Health checks
# ---------------------------------------------------------------------------


@app.get("/", status_code=status.HTTP_200_OK, tags=["Health"])
async def root_health():
    """Quick liveness check."""
    indexed = await run_in_threadpool(retriever.collection.count)
    return {
        "status": "healthy",
        "service": "UrbanPick Multimodal RAG API",
        "version": "2.0.0",
        "model_loaded": encoder is not None,
        "indexed_products": indexed,
    }


@app.get("/api/v1/health", status_code=status.HTTP_200_OK, tags=["Health"])
async def detailed_health():
    """Detailed readiness check including Ollama and ChromaDB status."""
    ollama = await _get_cached_ollama_health()
    indexed = await run_in_threadpool(retriever.collection.count)
    return {
        "status": "healthy",
        "encoder": {
            "loaded": encoder is not None,
            "model": settings.EMBEDDING_MODEL_NAME,
        },
        "chromadb": {
            "path": settings.CHROMA_DB_PATH,
            "indexed_products": indexed,
        },
        "ollama": {
            "base_url": settings.OLLAMA_BASE_URL,
            "model": settings.OLLAMA_MODEL,
            "reachable": ollama["reachable"],
            "model_available": ollama["model_available"],
            "error": ollama.get("error"),
        },
        "gemini": {
            "configured": bool(settings.GEMINI_API_KEY),
            "model": settings.GEMINI_MODEL,
        },
        "ingest_protected": bool(settings.INGEST_API_KEY.strip()),
    }


# ---------------------------------------------------------------------------
# Product ingestion
# ---------------------------------------------------------------------------


@app.post(
    "/api/v1/ingest",
    status_code=status.HTTP_201_CREATED,
    tags=["Products"],
    dependencies=[Depends(_verify_ingest_api_key)],
)
async def ingest_product(
    product: ProductIngestSchema,
    enc: MultimodalEncoder = Depends(_require_encoder),
):
    """
    Ingest (create or update) a product in the vector index.

    - Validates all fields via ProductIngestSchema.
    - Downloads and encodes the image URL if provided.
    - Combines text and image embeddings into a joint vector.
    - Uses upsert so re-ingesting the same product_id is an update, not a duplicate.
    - Protected by X-Api-Key header when INGEST_API_KEY is configured.
    """
    try:
        # Build descriptive text for text embedding.
        text_content = (
            f"{product.title} by {product.brand}. "
            f"Category: {product.category}. "
            f"Price: {product.current_price}. "
            f"Specifications: {product.specs}"
        )
        text_vector = await run_in_threadpool(enc.encode_text, text_content)

        image_vector: Optional[List[float]] = None

        if product.image_url:
            try:
                max_bytes = int(settings.MAX_IMAGE_SIZE_MB * 1024 * 1024)
                async with http_client.stream("GET", product.image_url) as resp:
                    resp.raise_for_status()
                    chunks: list[bytes] = []
                    downloaded = 0
                    async for chunk in resp.aiter_bytes(65536):
                        downloaded += len(chunk)
                        if downloaded > max_bytes:
                            raise ValueError(
                                f"Remote image exceeds {settings.MAX_IMAGE_SIZE_MB} MB limit."
                            )
                        chunks.append(chunk)
                    raw_image = b"".join(chunks)
                image_vector = await run_in_threadpool(enc.encode_image, raw_image)
                logger.info("Image encoded for product '%s'.", product.product_id)
            except Exception as img_err:
                logger.warning(
                    "Could not fetch/encode image for product '%s': %s — "
                    "using text-only embedding.",
                    product.product_id,
                    img_err,
                )

        # Fuse embeddings when both are available.
        if image_vector is not None and text_vector is not None:
            combined = (
                np.asarray(text_vector, dtype=np.float32)
                + np.asarray(image_vector, dtype=np.float32)
            )
            joint_vector = normalize_vector(combined.tolist())
            embedding_type = "multimodal"
        else:
            joint_vector = text_vector
            embedding_type = "text_only"

        if not joint_vector:
            raise ValueError("Embedding generation produced an empty vector.")

        await run_in_threadpool(
            retriever.add_product,
            product_data=product.model_dump(),
            vector=joint_vector,
        )

        logger.info(
            "Product '%s' (%s) ingested. Embedding: %s, dim: %d.",
            product.product_id,
            product.title,
            embedding_type,
            len(joint_vector),
        )

        return {
            "status": "success",
            "message": f"Product '{product.title}' ingested successfully.",
            "product_id": product.product_id,
            "embedding_type": embedding_type,
            "vector_dimension": len(joint_vector),
            "indexed_products_total": await run_in_threadpool(retriever.collection.count),
        }

    except HTTPException:
        raise

    except Exception as exc:
        logger.exception("Error during product ingestion for '%s'.", product.product_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ingestion failed: {str(exc)}",
        ) from exc


# ---------------------------------------------------------------------------
# Get one product
# ---------------------------------------------------------------------------


@app.get("/api/v1/products/{product_id}", tags=["Products"])
async def get_product(product_id: str):
    """Fetch a single product's stored metadata by ID."""

    product_id = product_id.strip()
    if not product_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="product_id must not be empty.",
        )

    result = await run_in_threadpool(retriever.collection.get, ids=[product_id])

    if not result.get("ids"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product '{product_id}' not found.",
        )

    meta = result["metadatas"][0]

    # Deserialize JSON fields for the response.
    for field in ("store_availability", "price_history"):
        raw = meta.get(field, "[]")
        try:
            meta[field] = json.loads(raw) if isinstance(raw, str) else raw
        except (json.JSONDecodeError, TypeError):
            meta[field] = []

    return meta


# ---------------------------------------------------------------------------
# Delete one product
# ---------------------------------------------------------------------------


@app.delete(
    "/api/v1/products/{product_id}",
    status_code=status.HTTP_200_OK,
    tags=["Products"],
    dependencies=[Depends(_verify_ingest_api_key)],
)
async def delete_product(product_id: str):
    """Delete a product from the vector index by ID."""

    product_id = product_id.strip()
    if not product_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="product_id must not be empty.",
        )

    deleted = await run_in_threadpool(retriever.delete_product, product_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product '{product_id}' not found.",
        )

    return {
        "status": "success",
        "message": f"Product '{product_id}' deleted.",
        "indexed_products_total": await run_in_threadpool(retriever.collection.count),
    }


# ---------------------------------------------------------------------------
# Admin: clear catalog
# ---------------------------------------------------------------------------


@app.delete(
    "/api/v1/admin/clear",
    status_code=status.HTTP_200_OK,
    tags=["Admin"],
    dependencies=[Depends(_verify_ingest_api_key)],
)
async def admin_clear_catalog(
    confirm: bool = Query(False, description="Must be true to execute the clear."),
):
    """
    **DANGEROUS** — Delete the entire product catalog and recreate it empty.

    Requires:
    - ``X-Api-Key`` header matching ``INGEST_API_KEY`` (when configured).
    - ``?confirm=true`` query parameter as an extra safeguard.
    """
    if not confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Pass ?confirm=true to confirm catalog deletion.",
        )
    await run_in_threadpool(retriever._clear_for_tests)
    logger.warning("Admin catalog clear executed via API.")
    return {
        "status": "success",
        "message": "Product catalog cleared.",
        "indexed_products_total": await run_in_threadpool(retriever.collection.count),
    }


# ---------------------------------------------------------------------------
# Multimodal search
# ---------------------------------------------------------------------------


@app.post(
    "/api/v1/search",
    response_model=SearchResponseSchema,
    tags=["Search"],
)
@limiter.limit(settings.SEARCH_RATE_LIMIT)
async def search_products(
    request: Request,
    text_prompt: Optional[str] = Form(None),
    image_file: Optional[UploadFile] = File(None),
    max_price: Optional[float] = Form(None, ge=0),
    category: Optional[str] = Form(None),
    top_k: int = Form(5, gt=0, le=100),
    enc: MultimodalEncoder = Depends(_require_encoder),
):
    """
    Search products using text, an uploaded image, or both.

    Form fields:
    - text_prompt   : natural-language query (optional if image_file provided)
    - image_file    : product image upload (optional if text_prompt provided)
    - max_price     : maximum price filter (>= 0)
    - category      : category substring filter (case-insensitive)
    - top_k         : maximum results to return (1–100, default 5)

    Similarity scores are in [0, 1] — higher is more relevant.
    """

    cleaned_prompt = text_prompt.strip() if text_prompt and text_prompt.strip() else None

    if cleaned_prompt is None and image_file is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide at least one of: text_prompt or image_file.",
        )

    try:
        text_vector: Optional[List[float]] = None
        image_vector: Optional[List[float]] = None
        search_type = "text"

        # --- Encode text ---
        if cleaned_prompt:
            text_vector = await run_in_threadpool(enc.encode_text, cleaned_prompt)

        # --- Encode image ---
        if image_file is not None:
            contents = await image_file.read()
            _validate_image_upload(contents, image_file.filename or "upload.jpg")
            image_vector = await run_in_threadpool(enc.encode_image, contents)
            search_type = "image" if cleaned_prompt is None else "multimodal"

        # --- Build query vector ---
        if text_vector is not None and image_vector is not None:
            fused = (
                np.asarray(text_vector, dtype=np.float32)
                + np.asarray(image_vector, dtype=np.float32)
            )
            query_vector = normalize_vector(fused.tolist())
            query_desc = (
                f"Multimodal Search — text: '{cleaned_prompt}', "
                f"image: '{image_file.filename}'"
            )
        elif text_vector is not None:
            query_vector = text_vector
            query_desc = f"Text Search: '{cleaned_prompt}'"
        elif image_vector is not None:
            query_vector = image_vector
            query_desc = f"Image Search: '{image_file.filename}'"
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not generate a query vector from the provided input.",
            )

        # --- Retrieve ---
        products = await run_in_threadpool(
            retriever.retrieve,
            query_vector=query_vector,
            top_k=top_k,
            max_price=max_price,
            category=category,
            query_text=cleaned_prompt,
        )

        logger.info(
            "Search '%s' returned %d product(s) [top_k=%d, max_price=%s, category=%s].",
            query_desc,
            len(products),
            top_k,
            max_price,
            category,
        )

        # --- AI Reasoning ---
        reasoning = await generate_grounded_response(
            user_query=query_desc,
            retrieved_products=products,
        )

        if not isinstance(reasoning, dict):
            reasoning = {}

        return SearchResponseSchema(
            query=query_desc,
            recommended_products=products,
            ai_analysis=reasoning.get("summary", "No analysis generated."),
            comparison_table=reasoning.get("comparison_table", []),
            total_results=len(products),
            search_type=search_type,
        )

    except HTTPException:
        raise

    except Exception as exc:
        logger.exception("Unexpected error during search.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(exc)}",
        ) from exc
