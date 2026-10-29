import os
from contextlib import contextmanager

import psycopg
from psycopg.rows import dict_row
from pgvector.psycopg import register_vector

from .catalog import PRODUCTS

DIMENSION = int(os.getenv("EMBEDDING_DIMENSION", "1536"))

def database_url():
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL belum diatur")
    return url

@contextmanager
def connection():
    with psycopg.connect(database_url(), row_factory=dict_row) as conn:
        register_vector(conn)
        yield conn

def init_db():
    with psycopg.connect(database_url(), row_factory=dict_row) as conn:
        conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
        register_vector(conn)
        conn.execute("""CREATE TABLE IF NOT EXISTS products (
            id TEXT PRIMARY KEY, name TEXT NOT NULL, category TEXT NOT NULL,
            body TEXT NOT NULL, top TEXT NOT NULL, back_sides TEXT NOT NULL,
            electronics TEXT NOT NULL, color TEXT NOT NULL, price INTEGER NOT NULL,
            image TEXT NOT NULL)""")
        conn.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS active BOOLEAN NOT NULL DEFAULT TRUE")
        conn.execute("ALTER TABLE products DROP COLUMN IF EXISTS source_url")
        conn.execute("CREATE TABLE IF NOT EXISTS app_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
        conn.execute("""CREATE TABLE IF NOT EXISTS documents (
            id UUID PRIMARY KEY, filename TEXT NOT NULL, storage_name TEXT NOT NULL,
            page_count INTEGER NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT now())""")
        conn.execute("""CREATE TABLE IF NOT EXISTS document_pages (
            document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
            page_number INTEGER NOT NULL, text TEXT NOT NULL,
            PRIMARY KEY(document_id, page_number))""")
        conn.execute(f"""CREATE TABLE IF NOT EXISTS document_chunks (
            id BIGSERIAL PRIMARY KEY, document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
            page_number INTEGER NOT NULL, chunk_index INTEGER NOT NULL,
            text TEXT NOT NULL, embedding_model TEXT NOT NULL,
            embedding vector({DIMENSION}) NOT NULL)""")
        conn.execute("""CREATE TABLE IF NOT EXISTS ai_settings (
            feature TEXT PRIMARY KEY, provider TEXT NOT NULL, model TEXT NOT NULL)""")
        seeded = conn.execute("SELECT 1 FROM app_meta WHERE key='catalog_seeded'").fetchone()
        if not seeded:
            for product in PRODUCTS:
                conn.execute("""INSERT INTO products (id,name,category,body,top,back_sides,electronics,color,price,image)
                    VALUES (%(id)s,%(name)s,%(category)s,%(body)s,%(top)s,%(back_sides)s,%(electronics)s,%(color)s,%(price)s,%(image)s)
                    ON CONFLICT(id) DO NOTHING""", product)
            conn.execute("INSERT INTO app_meta(key,value) VALUES ('catalog_seeded','1')")
        for feature in ("product_chat", "finance_qa", "vision"):
            conn.execute("INSERT INTO ai_settings(feature,provider,model) VALUES (%s,'gemini',%s) ON CONFLICT DO NOTHING", (feature, os.getenv("GEMINI_MODEL", "gemini-3.5-flash")))

def products():
    with connection() as conn:
        return conn.execute("SELECT * FROM products WHERE active=TRUE ORDER BY category,name").fetchall()

def setting(feature: str):
    with connection() as conn:
        return conn.execute("SELECT * FROM ai_settings WHERE feature=%s", (feature,)).fetchone()
