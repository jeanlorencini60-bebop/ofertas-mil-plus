import json
import os
import re
import sqlite3
from datetime import datetime, timedelta, timezone

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(ROOT, ".env"))

DB_PATH = os.path.join(ROOT, "data", "offers.sqlite3")
CATALOG_PATH = os.path.join(ROOT, "config", "catalog.json")

DRY_RUN = os.getenv("DRY_RUN", "true").lower() == "true"
MIN_DISCOUNT = float(os.getenv("MIN_DISCOUNT_PCT", "15"))
MAX_PRICE = float(os.getenv("MAX_PRICE_BRL", "5000"))
COOLDOWN_HOURS = int(os.getenv("REPOST_COOLDOWN_HOURS", "168"))
MAX_POSTS = int(os.getenv("MAX_POSTS_PER_RUN", "3"))
TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "20"))
WHAPI_BASE = os.getenv("WHAPI_BASE_URL", "https://gate.whapi.cloud").rstrip("/")
WHAPI_TOKEN = os.getenv("WHAPI_TOKEN", "").strip()
CHANNEL_JID = os.getenv("WHATSAPP_CHANNEL_JID", "").strip()

HEADERS = {"User-Agent": "Mozilla/5.0 OFERTAS-MIL-PLUS/1.0"}


def utc_now():
    return datetime.now(timezone.utc)


def iso_now():
    return utc_now().isoformat()


def db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute("""
      CREATE TABLE IF NOT EXISTS products (
        id TEXT PRIMARY KEY,
        affiliate_url TEXT NOT NULL,
        canonical_url TEXT,
        item_id TEXT,
        title TEXT,
        price REAL,
        original_price REAL,
        discount_pct REAL,
        available INTEGER,
        checked_at TEXT,
        last_posted_at TEXT,
        post_count INTEGER DEFAULT 0
      )
    """)
    con.execute("""
      CREATE TABLE IF NOT EXISTS price_history (
        product_id TEXT,
        checked_at TEXT,
        price REAL,
        original_price REAL,
        PRIMARY KEY(product_id, checked_at)
      )
    """)
    con.commit()
    return con


def resolve(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT, allow_redirects=True)
        return r.url, r.text
    except Exception as exc:
        print("resolve error:", url, exc)
        return url, ""


def extract_mlb(url):
    match = re.search(r"MLB[-_]?([0-9]{6,})", url.upper())
    return f"MLB{match.group(1)}" if match else None


def item_api(item_id):
    if not item_id:
        return None
    try:
        r = requests.get(
            f"https://api.mercadolibre.com/items/{item_id}",
            headers=HEADERS,
            timeout=TIMEOUT,
        )
        if r.ok:
            return r.json()
    except Exception as exc:
        print("item api error:", item_id, exc)
    return None


def parse_price(text):
    values = re.findall(r"R\$\s*([0-9.]+,[0-9]{2})", text)
    output = []
    for value in values:
        try:
            output.append(float(value.replace(".", "").replace(",", ".")))
        except ValueError:
            pass
    return output


def scrape_page(html):
    if not html:
        return None, None
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.get_text(" ", strip=True) if soup.title else None
    prices = parse_price(soup.get_text(" ", strip=True))
    return title, (min(prices) if prices else None)


def fetch_product(affiliate_url):
    canonical, html = resolve(affiliate_url)
    item_id = extract_mlb(canonical)
    item = item_api(item_id)

    if item:
        price = item.get("price")
        original = item.get("original_price")
        available = 1 if item.get("available_quantity", 0) > 0 else 0
        discount = round((original - price) / original * 100, 2) if original and price and original > price else 0.0
        return {
            "canonical_url": canonical,
            "item_id": item_id,
            "title": item.get("title"),
            "price": price,
            "original_price": original,
            "discount_pct": discount,
            "available": available,
        }

    title, price = scrape_page(html)
    return {
        "canonical_url": canonical,
        "item_id": item_id,
        "title": title,
        "price": price,
        "original_price": None,
        "discount_pct": 0.0,
        "available": 1 if price else 0,
    }


def upsert(con, product, info):
    ts = iso_now()
    con.execute("""
      INSERT INTO products
      (id, affiliate_url, canonical_url, item_id, title, price, original_price,
       discount_pct, available, checked_at)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
      ON CONFLICT(id) DO UPDATE SET
        affiliate_url=excluded.affiliate_url,
        canonical_url=excluded.canonical_url,
        item_id=excluded.item_id,
        title=excluded.title,
        price=excluded.price,
        original_price=excluded.original_price,
        discount_pct=excluded.discount_pct,
        available=excluded.available,
        checked_at=excluded.checked_at
    """, (
        product["id"], product["affiliate_url"], info["canonical_url"], info["item_id"],
        info["title"], info["price"], info["original_price"],
        info["discount_pct"], info["available"], ts
    ))
    if info["price"] is not None:
        con.execute(
            "INSERT OR IGNORE INTO price_history VALUES (?, ?, ?, ?)",
            (product["id"], ts, info["price"], info["original_price"]),
        )
    con.commit()


def eligible(row):
    if not row["available"] or row["price"] is None:
        return False
    if row["price"] > MAX_PRICE:
        return False
    if row["discount_pct"] < MIN_DISCOUNT:
        return False
    if row["last_posted_at"]:
        try:
            last = datetime.fromisoformat(row["last_posted_at"])
            if utc_now() - last < timedelta(hours=COOLDOWN_HOURS):
                return False
        except ValueError:
            pass
    return True


def brl(value):
    if value is None:
        return "—"
    return "R$ " + f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def make_message(row):
    title = row["title"] or "Oferta"
    return (
        "🔥 OFERTAS MIL +\n\n"
        f"🛍️ {title}\n"
        f"💰 {brl(row['price'])}\n"
        f"🏷️ {row['discount_pct']:.0f}% OFF\n\n"
        f"👉 VER OFERTA:\n{row['affiliate_url']}\n\n"
        "Publicidade / link de afiliado."
    )


def publish_whatsapp(message):
    if DRY_RUN:
        print("\n--- DRY RUN ---\n" + message + "\n---------------")
        return {"dry_run": True}

    if not WHAPI_TOKEN or not CHANNEL_JID:
        raise RuntimeError("WHAPI_TOKEN e WHATSAPP_CHANNEL_JID ainda não estão configurados.")

    response = requests.post(
        f"{WHAPI_BASE}/messages/text",
        headers={
            "Authorization": f"Bearer {WHAPI_TOKEN}",
            "Content-Type": "application/json",
        },
        json={"to": CHANNEL_JID, "body": message},
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    return response.json()


def run():
    with open(CATALOG_PATH, encoding="utf-8") as handle:
        catalog = json.load(handle)

    con = db()
    candidates = []

    for product in catalog.get("products", []):
        if not product.get("enabled", True):
            continue
        try:
            info = fetch_product(product["affiliate_url"])
            upsert(con, product, info)
            row = con.execute("SELECT * FROM products WHERE id=?", (product["id"],)).fetchone()
            print(product["id"], row["title"], row["price"], row["discount_pct"])
            if eligible(row):
                candidates.append(row)
        except Exception as exc:
            print("product error:", product["id"], exc)

    candidates.sort(key=lambda row: row["discount_pct"], reverse=True)

    processed = 0
    for row in candidates[:MAX_POSTS]:
        result = publish_whatsapp(make_message(row))
        print("publish result:", result)
        if not DRY_RUN:
            con.execute(
                "UPDATE products SET last_posted_at=?, post_count=post_count+1 WHERE id=?",
                (iso_now(), row["id"]),
            )
            con.commit()
        processed += 1

    print(f"eligible={len(candidates)} processed={processed} dry_run={DRY_RUN}")


if __name__ == "__main__":
    run()
