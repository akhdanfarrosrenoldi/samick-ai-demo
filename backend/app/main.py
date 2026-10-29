import os
import re
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal

import pymupdf as fitz
from fastapi import Depends, FastAPI, File, HTTPException, Request, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from .ai import generate, json_result, model_for
from .catalog import PRODUCTS, public_product
from .db import connection, init_db, products, setting
from .rag import answer_document, extract_pages, index_document
from .security import COOKIE, require_admin, signer, verify_password

UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "./backend/data/uploads")).resolve()
PRODUCT_IMAGE_DIR = UPLOAD_DIR / "product-images"
ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")
FEATURES = {"product_chat", "finance_qa", "vision"}

@asynccontextmanager
async def lifespan(_app: FastAPI):
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    PRODUCT_IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    init_db()
    yield

app = FastAPI(title="Samick Assistant API", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=[ORIGIN], allow_credentials=True, allow_methods=["GET", "POST", "PUT", "DELETE"], allow_headers=["Content-Type"])

@app.middleware("http")
async def origin_guard(request: Request, call_next):
    if request.url.path.startswith("/api/admin/") and request.method not in ("GET", "HEAD", "OPTIONS"):
        if request.headers.get("origin") not in (None, ORIGIN):
            return Response("Origin tidak diizinkan", status_code=403)
    return await call_next(request)

class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=1500)

class ChatRequest(BaseModel):
    message: str = Field(min_length=2, max_length=1500)
    history: list[ChatMessage] = Field(default_factory=list, max_length=6)

class LoginRequest(BaseModel):
    username: str
    password: str

class SettingRequest(BaseModel):
    provider: str

class ProductRequest(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    category: str = Field(min_length=2, max_length=60)
    body: str = Field(min_length=2, max_length=100)
    top: str = Field(min_length=2, max_length=100)
    back_sides: str = Field(min_length=2, max_length=100)
    electronics: str = Field(min_length=2, max_length=100)
    color: str = Field(min_length=2, max_length=100)
    image: str = Field(min_length=2, max_length=200)
    active: bool = True

def checked_product(body: ProductRequest) -> dict:
    data = {key: value.strip() if isinstance(value, str) else value for key, value in body.model_dump().items()}
    if any(not data[key] for key in ("name", "category", "body", "top", "back_sides", "electronics", "color")):
        raise HTTPException(400, "Kolom produk tidak boleh kosong")
    image = data["image"]
    if image.startswith("/api/product-images/"):
        name = image.removeprefix("/api/product-images/")
        if not re.fullmatch(r"[0-9a-f]{32}\.(jpg|png|webp)", name) or not (PRODUCT_IMAGE_DIR / name).is_file():
            raise HTTPException(400, "Foto produk tidak ditemukan")
    elif image not in {product["image"] for product in PRODUCTS}:
        raise HTTPException(400, "Foto produk harus berasal dari unggahan CMS")
    return data

def remove_unused_image(image: str):
    if not image.startswith("/api/product-images/"):
        return
    with connection() as conn:
        used = conn.execute("SELECT 1 FROM products WHERE image=%s LIMIT 1", (image,)).fetchone()
    if not used:
        (PRODUCT_IMAGE_DIR / image.rsplit("/", 1)[-1]).unlink(missing_ok=True)

@app.get("/api/health")
def health():
    with connection() as conn:
        conn.execute("SELECT 1")
    return {"status": "ok", "database": "ok"}

@app.get("/api/products")
def list_products():
    return [public_product(p) for p in products()]

@app.get("/api/product-images/{filename}")
def product_image(filename: str):
    if not re.fullmatch(r"[0-9a-f]{32}\.(jpg|png|webp)", filename):
        raise HTTPException(404, "Foto tidak ditemukan")
    path = PRODUCT_IMAGE_DIR / filename
    if not path.is_file():
        raise HTTPException(404, "Foto tidak ditemukan")
    return FileResponse(path)

def relevant_products(message: str, all_products: list[dict]) -> list[dict]:
    words = set(re.findall(r"[a-z0-9]+", message.lower()))
    if len(words) <= 2 or words & {"gitar", "beli", "rekomendasi"} and len(words) <= 4:
        return all_products[:8]
    scored = []
    for p in all_products:
        score = sum(2 if word in p["name"].lower() else 1 for word in words if len(word) > 2 and word in (p["name"] + " " + p["category"] + " " + p["body"] + " " + p["top"] + " " + p["electronics"] + " " + p["color"]).lower())
        if "pemula" in words and "Standard" in p["category"]: score += 3
        if "panggung" in words and p["electronics"] != "Tidak ada": score += 3
        if "kecil" in words and "mini" in p["body"].lower(): score += 3
        if "elektrik" in words and p["category"] == "Elektrik": score += 5
        if "akustik" in words and p["category"] != "Elektrik": score += 2
        scored.append((score, p))
    scored.sort(key=lambda row: row[0], reverse=True)
    return [p for _, p in scored[:6]]

@app.post("/api/product-chat")
def product_chat(body: ChatRequest):
    context = "\n".join([item.content for item in body.history[-4:]] + [body.message])
    candidates = relevant_products(context, products())
    choice = setting("product_chat")
    catalog = "\n".join(f"ID: {p['id']} | {p['name']} | {p['category']} | bodi {p['body']} | top {p['top']} | belakang/sisi {p['back_sides']} | elektronik {p['electronics']} | warna {p['color']}" for p in candidates)
    instructions = """Anda asisten katalog gitar Samick berbahasa Indonesia. Hanya rekomendasikan produk dari daftar. Gunakan riwayat untuk memahami pertanyaan lanjutan. Jelaskan alasan dari spesifikasi tersimpan. Jangan klaim harga, stok, checkout, atau spesifikasi di luar daftar. Bila kebutuhan terlalu umum, ajukan satu pertanyaan klarifikasi sambil boleh memberi contoh kandidat. Kembalikan JSON valid tanpa markdown: {"answer":"jawaban ringkas","product_ids":["id"]}. Pilih maksimal 3 ID dari kandidat, atau [] bila tidak relevan. Jangan masukkan URL atau harga."""
    history = "\n".join(f"{item.role}: {item.content}" for item in body.history)
    result = json_result(generate(choice["provider"], choice["model"], instructions, f"Riwayat percakapan:\n{history}\n\nPertanyaan terbaru: {body.message}\n\nKatalog kandidat:\n{catalog}"))
    allowed = {p["id"]: p for p in candidates}
    ids = [i for i in result.get("product_ids", []) if isinstance(i, str) and i in allowed][:3]
    answer = str(result.get("answer", ""))[:3000]
    answer = re.sub(r"(?:Rp\s*|harga\s+)(?:\d[\d.,]*)(?:\s*(?:juta|ribu))?", "harga belum tersedia", answer, flags=re.I)
    return {"answer": answer, "products": [public_product(allowed[i]) for i in ids], "provider": choice["provider"], "model": choice["model"]}

@app.post("/api/vision/identify")
async def identify(file: UploadFile = File(...)):
    data = await file.read(5 * 1024 * 1024 + 1)
    if len(data) > 5 * 1024 * 1024:
        raise HTTPException(413, "Gambar maksimal 5 MB")
    signatures = {"image/jpeg": data.startswith(b"\xff\xd8\xff"), "image/png": data.startswith(b"\x89PNG\r\n\x1a\n"), "image/webp": data.startswith(b"RIFF") and data[8:12] == b"WEBP"}
    mime = next((key for key, valid in signatures.items() if valid), None)
    if not mime:
        raise HTTPException(415, "Gunakan gambar JPEG, PNG, atau WebP")
    all_products = products()
    catalog = "\n".join(f"{p['id']}: {p['name']}, {p['category']}, {p['body']}, {p['color']}, {p['electronics']}" for p in all_products)
    choice = setting("vision")
    instructions = """Amati hanya ciri yang terlihat pada foto. Cocokkan dengan katalog terbatas dan jangan menyatakan model pasti bila logo/detail tidak jelas. Jika bukan gitar, kembalikan kandidat kosong. Kembalikan JSON valid tanpa markdown: {"observed_features":"...","uncertain":true,"candidate_ids":["id"],"reason":"..."}. Maksimal 3 kandidat dan ID hanya dari katalog."""
    result = json_result(generate(choice["provider"], choice["model"], instructions, f"Katalog:\n{catalog}", image=(data, mime)))
    allowed = {p["id"]: p for p in all_products}
    ids = [i for i in result.get("candidate_ids", []) if isinstance(i, str) and i in allowed][:3]
    return {"observed_features": str(result.get("observed_features", ""))[:1000], "reason": str(result.get("reason", ""))[:1000], "uncertain": bool(result.get("uncertain", True)), "candidates": [public_product(allowed[i]) for i in ids], "provider": choice["provider"], "model": choice["model"]}

@app.post("/api/admin/login")
def login(body: LoginRequest, response: Response):
    username = os.getenv("ADMIN_USERNAME", "admin")
    if body.username != username or not verify_password(body.password):
        raise HTTPException(401, "Username atau kata sandi salah")
    response.set_cookie(COOKIE, signer().dumps(username), httponly=True, secure=False, samesite="lax", max_age=60 * 60 * 8, path="/api/admin")
    return {"username": username}

@app.get("/api/admin/me")
def me(username: str = Depends(require_admin)):
    return {"username": username}

@app.get("/api/admin/products")
def admin_products(_: str = Depends(require_admin)):
    with connection() as conn:
        rows = conn.execute("SELECT id,name,category,body,top,back_sides,electronics,color,image,active FROM products ORDER BY name").fetchall()
    return rows

@app.post("/api/admin/product-images")
async def upload_product_image(file: UploadFile = File(...), _: str = Depends(require_admin)):
    data = await file.read(5 * 1024 * 1024 + 1)
    if len(data) > 5 * 1024 * 1024:
        raise HTTPException(413, "Foto maksimal 5 MB")
    signatures = {"jpg": data.startswith(b"\xff\xd8\xff"), "png": data.startswith(b"\x89PNG\r\n\x1a\n"), "webp": data.startswith(b"RIFF") and data[8:12] == b"WEBP"}
    extension = next((name for name, valid in signatures.items() if valid), None)
    if not extension:
        raise HTTPException(415, "Gunakan JPEG, PNG, atau WebP")
    filename = f"{uuid.uuid4().hex}.{extension}"
    (PRODUCT_IMAGE_DIR / filename).write_bytes(data)
    return {"image": f"/api/product-images/{filename}"}

@app.post("/api/admin/products", status_code=201)
def create_product(body: ProductRequest, _: str = Depends(require_admin)):
    data = checked_product(body)
    data["id"] = uuid.uuid4().hex[:12]
    with connection() as conn:
        conn.execute("""INSERT INTO products(id,name,category,body,top,back_sides,electronics,color,price,image,active)
            VALUES (%(id)s,%(name)s,%(category)s,%(body)s,%(top)s,%(back_sides)s,%(electronics)s,%(color)s,0,%(image)s,%(active)s)""", data)
    return data

@app.put("/api/admin/products/{product_id}")
def update_product(product_id: str, body: ProductRequest, _: str = Depends(require_admin)):
    data = checked_product(body)
    with connection() as conn:
        previous = conn.execute("SELECT image FROM products WHERE id=%s", (product_id,)).fetchone()
        if not previous:
            raise HTTPException(404, "Produk tidak ditemukan")
        conn.execute("""UPDATE products SET name=%(name)s,category=%(category)s,body=%(body)s,top=%(top)s,
            back_sides=%(back_sides)s,electronics=%(electronics)s,color=%(color)s,image=%(image)s,active=%(active)s
            WHERE id=%(id)s""", {**data, "id": product_id})
    if previous["image"] != data["image"]:
        remove_unused_image(previous["image"])
    return {"id": product_id, **data}

@app.delete("/api/admin/products/{product_id}")
def delete_product(product_id: str, _: str = Depends(require_admin)):
    with connection() as conn:
        previous = conn.execute("DELETE FROM products WHERE id=%s RETURNING image", (product_id,)).fetchone()
    if not previous:
        raise HTTPException(404, "Produk tidak ditemukan")
    remove_unused_image(previous["image"])
    return {"ok": True}

@app.post("/api/admin/logout")
def logout(response: Response, _: str = Depends(require_admin)):
    response.delete_cookie(COOKIE, path="/api/admin")
    return {"ok": True}

@app.get("/api/admin/ai-settings")
def get_settings(_: str = Depends(require_admin)):
    with connection() as conn:
        rows = conn.execute("SELECT * FROM ai_settings ORDER BY feature").fetchall()
    return {"settings": rows, "available": {"openai": bool(os.getenv("OPENAI_API_KEY")), "gemini": bool(os.getenv("GEMINI_API_KEY"))}}

@app.put("/api/admin/ai-settings/{feature}")
def update_setting(feature: str, body: SettingRequest, _: str = Depends(require_admin)):
    if feature not in FEATURES or body.provider not in {"openai", "gemini"}:
        raise HTTPException(400, "Fitur atau provider tidak dikenal")
    if not os.getenv("OPENAI_API_KEY" if body.provider == "openai" else "GEMINI_API_KEY"):
        raise HTTPException(400, "API key provider ini belum diatur")
    model = model_for(body.provider)
    with connection() as conn:
        conn.execute("UPDATE ai_settings SET provider=%s, model=%s WHERE feature=%s", (body.provider, model, feature))
    return {"feature": feature, "provider": body.provider, "model": model}

@app.get("/api/admin/documents")
def documents(_: str = Depends(require_admin)):
    with connection() as conn:
        rows = conn.execute("SELECT id,filename,page_count,created_at FROM documents ORDER BY created_at DESC").fetchall()
    return [{**row, "id": str(row["id"])} for row in rows]

@app.post("/api/admin/documents")
async def upload_document(file: UploadFile = File(...), _: str = Depends(require_admin)):
    if not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(415, "Hanya PDF yang diterima")
    if file.content_type not in {"application/pdf", "application/x-pdf", "application/octet-stream"}:
        raise HTTPException(415, "Tipe file harus PDF")
    data = await file.read(10 * 1024 * 1024 + 1)
    if len(data) > 10 * 1024 * 1024:
        raise HTTPException(413, "PDF maksimal 10 MB")
    if not data.startswith(b"%PDF-"):
        raise HTTPException(415, "File bukan PDF valid")
    pages = extract_pages(data)
    document_id = uuid.uuid4()
    storage_name = f"{document_id}.pdf"
    path = UPLOAD_DIR / storage_name
    try:
        with connection() as conn:
            conn.execute("INSERT INTO documents(id,filename,storage_name,page_count) VALUES (%s,%s,%s,%s)", (document_id, Path(file.filename).name[:180], storage_name, len(pages)))
            index_document(conn, document_id, pages)
            path.write_bytes(data)
    except Exception:
        path.unlink(missing_ok=True)
        raise
    return {"id": str(document_id), "filename": Path(file.filename).name, "page_count": len(pages)}

def document_or_404(document_id: uuid.UUID):
    with connection() as conn:
        row = conn.execute("SELECT * FROM documents WHERE id=%s", (document_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Dokumen tidak ditemukan")
    return row

@app.get("/api/admin/documents/{document_id}/file")
def document_file(document_id: uuid.UUID, _: str = Depends(require_admin)):
    row = document_or_404(document_id)
    return FileResponse(UPLOAD_DIR / row["storage_name"], media_type="application/pdf", filename=row["filename"], content_disposition_type="inline")

@app.get("/api/admin/documents/{document_id}/pages/{page_number}/preview")
def page_preview(document_id: uuid.UUID, page_number: int, _: str = Depends(require_admin)):
    row = document_or_404(document_id)
    if page_number < 1 or page_number > row["page_count"]:
        raise HTTPException(404, "Halaman tidak ditemukan")
    with fitz.open(UPLOAD_DIR / row["storage_name"]) as pdf:
        data = pdf[page_number - 1].get_pixmap(matrix=fitz.Matrix(1.4, 1.4)).tobytes("png")
    return Response(data, media_type="image/png")

@app.delete("/api/admin/documents/{document_id}")
def delete_document(document_id: uuid.UUID, _: str = Depends(require_admin)):
    row = document_or_404(document_id)
    with connection() as conn:
        conn.execute("DELETE FROM documents WHERE id=%s", (document_id,))
    (UPLOAD_DIR / row["storage_name"]).unlink(missing_ok=True)
    return {"ok": True}

@app.post("/api/admin/documents/{document_id}/questions")
def ask_document(document_id: uuid.UUID, body: ChatRequest, _: str = Depends(require_admin)):
    row = document_or_404(document_id)
    return answer_document(document_id, row["filename"], body.message)
