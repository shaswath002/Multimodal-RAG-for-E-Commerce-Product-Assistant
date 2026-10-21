"""
catalog_seed.py — Seed the UrbanPick ChromaDB with a realistic headphone catalog.

This script:
  1. Removes any placeholder / "string" products.
  2. Ingests 8 real headphone products covering different categories and price ranges.
  3. Verifies each product is retrievable after ingestion.

Run from the backend directory:
    python catalog_seed.py

Make sure the FastAPI server is running first:
    uvicorn main:app --reload
"""

import argparse
import json
import os
import sys
import httpx

PRODUCTS = [
    {
        "product_id": "sony-wh1000xm5",
        "title": "Sony WH-1000XM5 Wireless Noise Cancelling Headphones",
        "brand": "Sony",
        "category": "Over-Ear Headphones",
        "specs": (
            "Industry-leading noise cancellation, 30-hour battery, "
            "Multipoint connection, LDAC Hi-Res Audio, over-ear design, "
            "foldable, USB-C charging, speak-to-chat"
        ),
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2a/Sony_WH-1000XM5_product_image_20220523.jpg/440px-Sony_WH-1000XM5_product_image_20220523.jpg",
        "current_price": 24990,
        "original_price": 34990,
        "discount": 28.6,
        "rating": 4.7,
        "availability": "In Stock",
        "store": "Amazon",
        "store_availability": [
            {"store": "Amazon", "price": 24990, "url": "https://www.amazon.in/dp/B09XS7JWHH"},
            {"store": "Flipkart", "price": 25490, "url": "https://www.flipkart.com/sony-wh-1000xm5"},
        ],
        "price_history": [
            {"date": "2024-01-01", "price": 34990},
            {"date": "2024-06-01", "price": 29990},
            {"date": "2024-10-01", "price": 24990},
        ],
    },
    {
        "product_id": "bose-qc45",
        "title": "Bose QuietComfort 45 Wireless Headphones",
        "brand": "Bose",
        "category": "Over-Ear Headphones",
        "specs": (
            "World-class noise cancellation, 24-hour battery, "
            "Aware Mode, TriPort acoustic architecture, over-ear, "
            "USB-C charging, multi-device pairing"
        ),
        "image_url": "https://assets.bose.com/content/dam/Bose_DAM/Web/consumer_electronics/global/products/headphones/qc45/product_seo_images/qc45_PDP_ecomm_black_hero.png/jcr:content/renditions/cq5dam.web.1280.1280.png",
        "current_price": 22900,
        "original_price": 29900,
        "discount": 23.4,
        "rating": 4.6,
        "availability": "In Stock",
        "store": "Amazon",
        "store_availability": [
            {"store": "Amazon", "price": 22900, "url": "https://www.amazon.in/dp/B098FKXT8L"},
            {"store": "Croma", "price": 23500, "url": "https://www.croma.com/bose-qc45"},
        ],
        "price_history": [
            {"date": "2024-01-01", "price": 29900},
            {"date": "2024-09-01", "price": 22900},
        ],
    },
    {
        "product_id": "jbl-tune770nc",
        "title": "JBL Tune 770NC Adaptive Noise Cancelling Wireless Headphones",
        "brand": "JBL",
        "category": "Over-Ear Headphones",
        "specs": (
            "Adaptive Noise Cancelling, 70-hour battery, "
            "JBL Pure Bass Sound, Ambient Aware, Talk-Thru, "
            "over-ear foldable, Bluetooth 5.3, hands-free calls"
        ),
        "image_url": "https://in.jbl.com/on/demandware.static/-/Sites-masterCatalog_Harman/default/dw7cba8cd3/JBL_TUNE770NC_Product%20Image_Hero_Black.png",
        "current_price": 7999,
        "original_price": 11999,
        "discount": 33.3,
        "rating": 4.4,
        "availability": "In Stock",
        "store": "Flipkart",
        "store_availability": [
            {"store": "Flipkart", "price": 7999, "url": "https://www.flipkart.com/jbl-tune-770nc"},
            {"store": "Amazon", "price": 8499, "url": "https://www.amazon.in/dp/jbl770nc"},
        ],
        "price_history": [
            {"date": "2024-01-01", "price": 11999},
            {"date": "2024-08-01", "price": 7999},
        ],
    },
    {
        "product_id": "apple-airpods-pro-2",
        "title": "Apple AirPods Pro (2nd Generation) with MagSafe Charging Case",
        "brand": "Apple",
        "category": "In-Ear Earbuds",
        "specs": (
            "Active Noise Cancellation, Transparency mode, Adaptive Audio, "
            "Conversation Awareness, 30-hour total battery life, "
            "IP54 water resistant, Personalized Spatial Audio, H2 chip, "
            "in-ear TWS earbuds"
        ),
        "image_url": "https://store.storeimages.cdn-apple.com/4668/as-images.apple.com/is/MQD83?wid=572&hei=572&fmt=jpeg&qlt=95&.v=1660803972361",
        "current_price": 19900,
        "original_price": 24900,
        "discount": 20.1,
        "rating": 4.8,
        "availability": "In Stock",
        "store": "Apple Store",
        "store_availability": [
            {"store": "Apple Store", "price": 24900, "url": "https://www.apple.com/in/shop/buy-airpods/airpods-pro"},
            {"store": "Amazon", "price": 19900, "url": "https://www.amazon.in/dp/B0BDHWDR12"},
            {"store": "Flipkart", "price": 20490, "url": "https://www.flipkart.com/apple-airpods-pro-2"},
        ],
        "price_history": [
            {"date": "2024-01-01", "price": 24900},
            {"date": "2024-07-01", "price": 21990},
            {"date": "2024-10-01", "price": 19900},
        ],
    },
    {
        "product_id": "samsung-galaxy-buds2-pro",
        "title": "Samsung Galaxy Buds2 Pro True Wireless Earbuds",
        "brand": "Samsung",
        "category": "In-Ear Earbuds",
        "specs": (
            "Intelligent ANC, 360 Audio, Hi-Fi 24bit sound, "
            "IPX7 water resistance, 8-hour battery (29hr with case), "
            "Bluetooth 5.3, in-ear TWS earbuds, compatible with Galaxy ecosystem"
        ),
        "image_url": "https://image-us.samsung.com/SamsungUS/home/mobile/galaxy-buds/all-galaxy-buds/07082022/Galaxy-Buds2-Pro-Bora-Purple_Main.jpg",
        "current_price": 12999,
        "original_price": 17999,
        "discount": 27.8,
        "rating": 4.3,
        "availability": "In Stock",
        "store": "Samsung",
        "store_availability": [
            {"store": "Samsung Shop", "price": 12999, "url": "https://www.samsung.com/in/audio-sound/galaxy-buds/galaxy-buds2-pro"},
            {"store": "Amazon", "price": 13499, "url": "https://www.amazon.in/samsung-galaxy-buds2-pro"},
        ],
        "price_history": [
            {"date": "2024-01-01", "price": 17999},
            {"date": "2024-10-01", "price": 12999},
        ],
    },
    {
        "product_id": "sennheiser-hd660s2",
        "title": "Sennheiser HD 660S2 Open-Back Wired Headphones",
        "brand": "Sennheiser",
        "category": "Over-Ear Headphones",
        "specs": (
            "Open-back audiophile design, 38-ohm impedance, 10Hz-41kHz frequency response, "
            "detachable cables (6.35mm + 4.4mm balanced), velour ear pads, "
            "wired over-ear, studio reference quality"
        ),
        "image_url": "https://en-us.sennheiser.com/globalassets/catalog/products/headphones/hd-660-s2/hd-660-s2_main.png",
        "current_price": 34990,
        "original_price": 39990,
        "discount": 12.5,
        "rating": 4.6,
        "availability": "In Stock",
        "store": "Amazon",
        "store_availability": [
            {"store": "Amazon", "price": 34990, "url": "https://www.amazon.in/Sennheiser-HD660S2"},
            {"store": "Sennheiser Official", "price": 39990, "url": "https://www.sennheiser.com/in/hd-660-s2"},
        ],
        "price_history": [
            {"date": "2024-01-01", "price": 39990},
            {"date": "2024-10-01", "price": 34990},
        ],
    },
    {
        "product_id": "boat-rockerz-450",
        "title": "boAt Rockerz 450 Wireless Bluetooth Headphones",
        "brand": "boAt",
        "category": "Over-Ear Headphones",
        "specs": (
            "40mm dynamic drivers, 15-hour battery, Bluetooth 5.0, "
            "foldable over-ear design, padded ear cushions, "
            "built-in mic, voice assistant support, 3.5mm aux input"
        ),
        "image_url": "https://www.boat-lifestyle.com/cdn/shop/products/Rockerz450Glossy_MainImage.jpg",
        "current_price": 999,
        "original_price": 3990,
        "discount": 74.9,
        "rating": 4.1,
        "availability": "In Stock",
        "store": "Amazon",
        "store_availability": [
            {"store": "Amazon", "price": 999, "url": "https://www.amazon.in/boAt-Rockerz-450"},
            {"store": "Flipkart", "price": 1099, "url": "https://www.flipkart.com/boat-rockerz-450"},
        ],
        "price_history": [
            {"date": "2024-01-01", "price": 3990},
            {"date": "2024-10-01", "price": 999},
        ],
    },
    {
        "product_id": "jabra-evolve2-65",
        "title": "Jabra Evolve2 65 Professional Wireless Headset",
        "brand": "Jabra",
        "category": "Over-Ear Headphones",
        "specs": (
            "Professional ANC, 37-hour battery, USB-A dongle included, "
            "MS Teams certified, Busy Light, over-ear foldable, "
            "Bluetooth 5.0, 10-microphone call technology"
        ),
        "image_url": "https://www.jabra.com/~/media/Images/Products/Jabra/Evolve2-65/jabra-evolve2-65-ms-stereo-black-hero-web.jpg",
        "current_price": 21999,
        "original_price": 27999,
        "discount": 21.4,
        "rating": 4.5,
        "availability": "In Stock",
        "store": "Amazon",
        "store_availability": [
            {"store": "Amazon", "price": 21999, "url": "https://www.amazon.in/Jabra-Evolve2-65"},
        ],
        "price_history": [
            {"date": "2024-01-01", "price": 27999},
            {"date": "2024-10-01", "price": 21999},
        ],
    },
]

# IDs that are known placeholder records to clean up first
PLACEHOLDER_IDS = ["string", "test", "placeholder", "example", "none", "null"]


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Seed the UrbanPick ChromaDB with a headphone catalog.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--base-url",
        default=os.environ.get("URBANPICK_BASE_URL", "http://localhost:8000"),
        help="Base URL of the running FastAPI server.",
    )
    parser.add_argument(
        "--api-key",
        default=os.environ.get("INGEST_API_KEY", ""),
        help="X-Api-Key header value for protected endpoints.",
    )
    return parser.parse_args()


def main():
    args = _parse_args()
    base_url: str = args.base_url.rstrip("/")
    api_key: str = args.api_key

    headers = {"X-Api-Key": api_key} if api_key else {}
    client = httpx.Client(timeout=60.0, base_url=base_url, headers=headers)

    # 1. Delete placeholder records
    print("=== Cleaning up placeholder products ===")
    for pid in PLACEHOLDER_IDS:
        try:
            resp = client.delete(f"/api/v1/products/{pid}")
            if resp.status_code == 200:
                print(f"  [deleted] '{pid}'")
            elif resp.status_code == 404:
                print(f"  [skip] '{pid}' not found")
            else:
                print(f"  [warn] DELETE {pid}: {resp.status_code} {resp.text}")
        except Exception as e:
            print(f"  [error] Could not delete '{pid}': {e}")

    # 2. Ingest products
    print(f"\n=== Ingesting {len(PRODUCTS)} products ===")
    success = 0
    failures = []

    for product in PRODUCTS:
        try:
            resp = client.post("/api/v1/ingest", json=product)
            if resp.status_code == 201:
                data = resp.json()
                print(
                    f"  [OK] {product['product_id']!r:35s} "
                    f"dim={data['vector_dimension']} "
                    f"type={data['embedding_type']} "
                    f"total={data['indexed_products_total']}"
                )
                success += 1
            else:
                print(f"  [FAIL] {product['product_id']}: {resp.status_code} — {resp.text}")
                failures.append(product["product_id"])
        except Exception as e:
            print(f"  [ERROR] {product['product_id']}: {e}")
            failures.append(product["product_id"])

    # 3. Quick retrieval checks
    print("\n=== Retrieval smoke tests ===")
    smoke_queries = [
        ("Sony headphones", None, None),
        ("wireless headphones under 10000", 10000, None),
        ("noise cancelling headphones", None, None),
        ("earbuds TWS", None, "In-Ear Earbuds"),
        ("budget headphones under 2000", 2000, None),
        ("professional headset for calls", None, None),
    ]

    for query, max_price, category in smoke_queries:
        payload = {"text_prompt": query, "top_k": "3"}
        if max_price:
            payload["max_price"] = str(max_price)
        if category:
            payload["category"] = category

        try:
            resp = client.post("/api/v1/search", data=payload)
            if resp.status_code == 200:
                data = resp.json()
                results = data["recommended_products"]
                titles = [r["title"][:40] for r in results]
                print(f"  Query: {query!r:45s} → {len(results)} result(s)")
                for t, r in zip(titles, results):
                    print(f"    • {t} (score={r['similarity_score']})")
            else:
                print(f"  [FAIL] {query!r}: {resp.status_code} — {resp.text}")
        except Exception as e:
            print(f"  [ERROR] {query!r}: {e}")

    # 4. Summary
    print(f"\n=== Seed complete: {success}/{len(PRODUCTS)} products ingested ===")
    if failures:
        print(f"  Failed: {failures}")
        sys.exit(1)


if __name__ == "__main__":
    main()
