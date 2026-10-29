"""Page-preserving PDF extraction and bounded retrieval."""
import os
import re
from decimal import Decimal

import pymupdf as fitz
from fastapi import HTTPException
from pgvector import Vector

from .ai import embed, generate, json_result
from .db import DIMENSION, connection, setting


def extract_pages(data: bytes) -> list[str]:
    try:
        pdf = fitz.open(stream=data, filetype="pdf")
        if len(pdf) > 20:
            raise HTTPException(413, "PDF maksimal 20 halaman")
        pages = [page.get_text(sort=True).strip() for page in pdf]
        pdf.close()
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(400, "PDF tidak dapat dibaca") from exc
    if not any(pages):
        raise HTTPException(422, "PDF ini tidak memiliki teks yang dapat dibaca. OCR untuk PDF scan belum tersedia.")
    return pages


def chunks_for_pages(pages: list[str]):
    chunks = []
    for page_number, text in enumerate(pages, 1):
        paragraphs = [s.strip() for s in re.split(r"\n\s*\n", text) if s.strip()]
        current = ""
        for part in paragraphs:
            if len(current) + len(part) > 1000 and current:
                chunks.append((page_number, current.strip()))
                current = ""
            if len(part) > 1000:
                for start in range(0, len(part), 900):
                    chunks.append((page_number, part[start:start+900]))
            else:
                current += ("\n" if current else "") + part
        if current:
            chunks.append((page_number, current.strip()))
    return chunks


def index_document(conn, document_id, pages: list[str]):
    chunks = chunks_for_pages(pages)
    if not chunks:
        raise HTTPException(422, "PDF tidak memiliki teks yang dapat diindeks")
    vectors = embed([text for _, text in chunks])
    if any(len(vector) != DIMENSION for vector in vectors):
        raise HTTPException(500, "Dimensi embedding tidak cocok dengan database")
    for page_number, text in enumerate(pages, 1):
        conn.execute("INSERT INTO document_pages(document_id,page_number,text) VALUES (%s,%s,%s)", (document_id, page_number, text))
    for idx, ((page, text), vector) in enumerate(zip(chunks, vectors)):
        conn.execute("""INSERT INTO document_chunks(document_id,page_number,chunk_index,text,embedding_model,embedding)
            VALUES (%s,%s,%s,%s,%s,%s)""", (document_id, page, idx, text, os.getenv("EMBEDDING_MODEL", "gemini-embedding-2"), Vector(vector)))


def retrieve(document_id, question: str) -> list[dict]:
    vector = embed([question], query=True)[0]
    if len(vector) != DIMENSION:
        raise HTTPException(500, "Dimensi embedding tidak cocok dengan database")
    with connection() as conn:
        rows = conn.execute("""SELECT page_number,text,embedding <=> %s AS distance
            FROM document_chunks WHERE document_id=%s AND embedding_model=%s
            ORDER BY embedding <=> %s LIMIT 5""", (Vector(vector), document_id, os.getenv("EMBEDDING_MODEL", "gemini-embedding-2"), Vector(vector))).fetchall()
        # Exact term matches complement vector retrieval for finance labels and amounts.
        words = [w for w in re.findall(r"[\w]+", question.lower()) if len(w) > 4][:5]
        if words:
            exact = conn.execute("SELECT page_number,text FROM document_chunks WHERE document_id=%s AND (" + " OR ".join(["lower(text) LIKE %s"] * len(words)) + ") LIMIT 5", [document_id] + [f"%{w}%" for w in words]).fetchall()
            seen = {(r["page_number"], r["text"]) for r in rows}
            rows += [r for r in exact if (r["page_number"], r["text"]) not in seen]
    return rows[:8]


def verified_calculation(proposal: dict, contexts: list[dict]) -> dict | None:
    """Accept only a two-number operation backed by exact label/number pairs in retrieved text."""
    try:
        operation = proposal["operation"]
        if operation not in ("add", "subtract"):
            return None
        operands = proposal["operands"]
        if not isinstance(operands, list) or len(operands) != 2:
            return None
        numbers = []
        checked = []
        for item in operands:
            label = str(item["label"]).strip()
            page = int(item["page_number"])
            value = str(item["value"]).strip()
            amount = re.sub(r"^Rp\s*", "", value, flags=re.I)
            if not label or len(label) > 80 or not re.fullmatch(r"[\d.,]+", amount):
                return None
            normalized = amount.replace(".", "").replace(",", "")
            matching = [c["text"] for c in contexts if c["page_number"] == page]
            pattern = re.compile(r"^\s*" + re.escape(label) + r"\s*:\s*(?:Rp\s*)?" + re.escape(amount) + r"(?![\d.,])", re.I | re.M)
            if not any(pattern.search(text) for text in matching):
                return None
            numbers.append(Decimal(normalized))
            checked.append({"label": label, "value": int(normalized), "page_number": page})
        result = numbers[0] + numbers[1] if operation == "add" else numbers[0] - numbers[1]
        return {"operation": operation, "operands": checked, "result": int(result)}
    except (KeyError, TypeError, ValueError, ArithmeticError):
        return None


def answer_document(document_id, filename: str, question: str) -> dict:
    contexts = retrieve(document_id, question)
    if not contexts:
        return {"answer": "Informasi tidak ditemukan dalam dokumen ini.", "sources": [], "calculation": None}
    selected = [{"page_number": r["page_number"], "text": r["text"]} for r in contexts]
    prompt = f"Pertanyaan: {question}\n\nKonteks dokumen {filename}:\n" + "\n\n".join(f"[Halaman {c['page_number']}]\n{c['text']}" for c in selected)
    instructions = """Jawab dalam bahasa Indonesia hanya dari konteks PDF. Kembalikan JSON valid tanpa markdown:
{"answer":"...","pages":[1],"calculation":null}.
Jika tidak ditemukan, answer harus 'Informasi tidak ditemukan dalam dokumen ini.' dan pages [].
Untuk permintaan penjumlahan/selisih DUA pos berlabel, isi calculation:
{"operation":"add" atau "subtract","operands":[{"label":"label persis","value":"angka persis seperti PDF","page_number":1},{...}]}.
Jangan hitung sendiri; program akan memverifikasi dan menghitung. Jangan gunakan pengetahuan di luar konteks."""
    choice = setting("finance_qa")
    result = json_result(generate(choice["provider"], choice["model"], instructions, prompt))
    valid_pages = {c["page_number"] for c in selected}
    pages = sorted({int(p) for p in result.get("pages", []) if str(p).isdigit() and int(p) in valid_pages})
    calculation = None
    if result.get("calculation"):
        calculation = verified_calculation(result["calculation"], selected)
        if calculation is None:
            return {"answer": "Perhitungan belum dapat dipastikan dari angka dan label pada PDF ini.", "sources": [], "calculation": None, "provider": choice["provider"]}
        pages = sorted({i["page_number"] for i in calculation["operands"]})
        operation_word = "ditambah" if calculation["operation"] == "add" else "dikurangi"
        a, b = calculation["operands"]
        answer = f"{a['label']} (Rp {a['value']:,}) {operation_word} {b['label']} (Rp {b['value']:,}) = Rp {calculation['result']:,}.".replace(",", ".")
    else:
        answer = str(result.get("answer", "")).strip()
        if not pages or not answer:
            answer, pages = "Informasi tidak ditemukan dalam dokumen ini.", []
        else:
            # Direct financial amounts must occur in one of the cited PDF chunks.
            cited = "\n".join(c["text"] for c in selected if c["page_number"] in pages)
            for amount in re.findall(r"Rp\s*([\d.,]+)", answer, re.I):
                if amount.rstrip(".,") not in cited:
                    return {"answer": "Nominal dalam jawaban belum dapat diverifikasi pada halaman sumber.", "sources": [], "calculation": None, "provider": choice["provider"]}
    sources = [{"document_id": str(document_id), "filename": filename, "page_number": page, "snippet": next(c["text"][:220] for c in selected if c["page_number"] == page)} for page in pages]
    return {"answer": answer, "sources": sources, "calculation": calculation, "provider": choice["provider"], "model": choice["model"]}
