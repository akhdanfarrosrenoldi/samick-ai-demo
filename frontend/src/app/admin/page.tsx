"use client";
/* eslint-disable @next/next/no-img-element -- PDF preview needs the admin cookie. */

import { useCallback, useEffect, useState } from "react";
import Image from "next/image";
import Link from "next/link";
import CatalogManager from "./catalog-manager";
import { API, request } from "./api";
import "./admin.css";

type Document = { id: string; filename: string; page_count: number; created_at: string };
type Setting = { feature: string; provider: string; model: string };
type SettingsResponse = { settings: Setting[]; available: Record<string, boolean> };
type Answer = {
  answer: string;
  provider: string;
  sources: { document_id: string; filename: string; page_number: number; snippet: string }[];
};

export default function Admin() {
  const [logged, setLogged] = useState(false);
  const [loading, setLoading] = useState(true);
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("");
  const [documents, setDocuments] = useState<Document[]>([]);
  const [selected, setSelected] = useState("");
  const [settings, setSettings] = useState<Setting[]>([]);
  const [available, setAvailable] = useState<Record<string, boolean>>({});
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState<Answer | null>(null);
  const [preview, setPreview] = useState<number | null>(null);
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");

  const refresh = useCallback(async () => {
    const [items, configuration] = await Promise.all([
      request<Document[]>("/api/admin/documents"),
      request<SettingsResponse>("/api/admin/ai-settings"),
    ]);
    setDocuments(items);
    setSettings(configuration.settings);
    setAvailable(configuration.available);
    setSelected(current => current || items[0]?.id || "");
  }, []);

  useEffect(() => {
    request("/api/admin/me")
      .then(() => { setLogged(true); return refresh(); })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [refresh]);

  async function login(event: React.FormEvent) {
    event.preventDefault();
    setBusy("login"); setError("");
    try {
      await request("/api/admin/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });
      setLogged(true);
      setPassword("");
      await refresh();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Login gagal");
    } finally { setBusy(""); }
  }

  async function logout() {
    try { await request("/api/admin/logout", { method: "POST" }); }
    finally { setLogged(false); setDocuments([]); setAnswer(null); }
  }

  async function upload(file: File) {
    setBusy("upload"); setError("");
    try {
      const form = new FormData();
      form.append("file", file);
      const document = await request<Document>("/api/admin/documents", { method: "POST", body: form });
      await refresh();
      setSelected(document.id);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Unggah gagal");
    } finally { setBusy(""); }
  }

  async function remove(id: string) {
    if (!window.confirm("Hapus PDF ini beserta indeksnya?")) return;
    setBusy("delete"); setError("");
    try {
      await request(`/api/admin/documents/${id}`, { method: "DELETE" });
      setSelected(""); setAnswer(null); setPreview(null);
      await refresh();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Hapus gagal");
    } finally { setBusy(""); }
  }

  async function ask(event: React.FormEvent) {
    event.preventDefault();
    if (!selected || !question.trim()) return;
    setBusy("ask"); setError(""); setAnswer(null); setPreview(null);
    try {
      setAnswer(await request<Answer>(`/api/admin/documents/${selected}/questions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: question }),
      }));
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Pertanyaan gagal");
    } finally { setBusy(""); }
  }

  async function change(feature: string, provider: string) {
    setBusy(feature); setError("");
    try {
      await request(`/api/admin/ai-settings/${feature}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ provider }),
      });
      await refresh();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Perubahan gagal");
    } finally { setBusy(""); }
  }

  const current = documents.find(document => document.id === selected);

  return <div className="admin-shell">
    <header className="admin-top">
      <Link href="/" className="admin-logo"><Image src="/brand/logo.jpg" alt="Samick" width={145} height={42} /></Link>
      <div><strong>SAMICK / INTERNAL</strong><small>Ruang kerja internal · data fiktif</small></div>
      <Link href="/">← Kembali ke customer</Link>
      {logged && <button onClick={() => void logout()}>Keluar</button>}
    </header>

    {loading ? <main className="login-wrap">Memeriksa sesi…</main> : !logged ?
      <main className="login-wrap">
        <div className="login-card">
          <span className="admin-eyebrow">/ AKSES INTERNAL</span>
          <h1>Masuk ke CMS.</h1>
          <p>Kelola katalog, dokumen internal, dan pilihan provider AI dari satu tempat.</p>
          <form onSubmit={event => void login(event)}>
            <label>Username<input value={username} onChange={event => setUsername(event.target.value)} autoComplete="username" /></label>
            <label>Kata sandi<input type="password" value={password} onChange={event => setPassword(event.target.value)} autoComplete="current-password" /></label>
            <button disabled={!!busy}>Masuk</button>
          </form>
          {error && <p className="admin-error" role="alert">{error}</p>}
          <small>Dokumen dan angka dalam aplikasi ini adalah data fiktif.</small>
        </div>
      </main> :
      <main className="admin-main">
        <div className="admin-heading">
          <div><span className="admin-eyebrow">/ RUANG KERJA INTERNAL</span><h1>Katalog, dokumen & AI.</h1><p>Kelola katalog gitar dan dokumen internal. Jawaban PDF dibatasi pada dokumen terpilih.</p></div>
          <div className="admin-badge">● Sesi admin aktif</div>
        </div>
        {error && <p className="admin-error" role="alert">{error}</p>}

        <CatalogManager />

        <div className="admin-grid">
          <section className="admin-panel">
            <div className="panel-header">
              <div><small>02 / PUSTAKA PDF</small><h2>Dokumen internal</h2></div>
              <label className="upload-button">+ Unggah PDF<input type="file" accept="application/pdf" onChange={event => {
                const file = event.target.files?.[0];
                if (file) void upload(file);
                event.target.value = "";
              }} /></label>
            </div>
            <p className="panel-note">Maksimal 10 MB dan 20 halaman. PDF scan memerlukan OCR dan belum didukung.</p>
            {busy === "upload" && <p className="admin-status">Mengunggah dan mengindeks PDF…</p>}
            {documents.length === 0 ? <div className="empty">Belum ada dokumen. Unggah PDF untuk mulai bertanya.</div> :
              <div className="doc-list">{documents.map(document =>
                <div className={`doc-row ${selected === document.id ? "selected" : ""}`} key={document.id}>
                  <button onClick={() => { setSelected(document.id); setAnswer(null); setPreview(null); }}>
                    <span className="pdf-icon">PDF</span>
                    <span><strong>{document.filename}</strong><small>{document.page_count} halaman · {new Date(document.created_at).toLocaleDateString("id-ID")}</small></span>
                  </button>
                  <button className="doc-delete" disabled={!!busy} onClick={() => void remove(document.id)}>Hapus</button>
                </div>)}</div>}
          </section>

          <section className="admin-panel">
            <div className="panel-header"><div><small>03 / TANYA DOKUMEN</small><h2>Asisten laporan</h2></div></div>
            <p className="panel-note">Dokumen aktif: <strong>{current?.filename || "Belum dipilih"}</strong>. Semua angka dalam PDF adalah simulasi.</p>
            <div className="example-questions">{[
              "Ringkas isi laporan ini", "Berapa penjualan gitar akustik?", "Berapa jumlah penjualan gitar akustik dan elektrik?",
            ].map(example => <button key={example} onClick={() => setQuestion(example)}>{example}</button>)}</div>
            <form className="qa-form" onSubmit={event => void ask(event)}>
              <textarea value={question} onChange={event => setQuestion(event.target.value)} placeholder="Tanyakan isi PDF terpilih…" rows={3} />
              <button disabled={!selected || !question.trim() || !!busy}>{busy === "ask" ? "Memproses…" : "Tanya PDF"}</button>
            </form>
            {answer && <div className="qa-answer">
              <small>JAWABAN · {answer.provider?.toUpperCase()}</small>
              <p>{answer.answer}</p>
              {answer.sources.length > 0 && <div className="citations">{answer.sources.map(source =>
                <button key={source.page_number} onClick={() => setPreview(source.page_number)}>Lihat {source.filename} · halaman {source.page_number}</button>)}</div>}
              {preview && <div className="page-preview">
                <img src={`${API}/api/admin/documents/${selected}/pages/${preview}/preview`} alt={`Pratinjau halaman ${preview}`} />
                <a href={`${API}/api/admin/documents/${selected}/file`} target="_blank" rel="noreferrer">Buka PDF asli</a>
              </div>}
            </div>}
          </section>
        </div>

        <section className="admin-panel settings-panel">
          <div className="panel-header"><div><small>04 / KONFIGURASI</small><h2>Provider AI</h2></div><p>Pilihan berlaku pada permintaan berikutnya.</p></div>
          <div className="settings-grid">{settings.map(item =>
            <div className="setting" key={item.feature}>
              <span>{item.feature === "product_chat" ? "Chat produk" : item.feature === "finance_qa" ? "Tanya PDF" : "Analisis foto"}</span>
              <strong>{item.model}</strong>
              <select value={item.provider} disabled={!!busy} onChange={event => void change(item.feature, event.target.value)}>
                <option value="openai" disabled={!available.openai}>OpenAI{!available.openai ? " · belum ada key" : ""}</option>
                <option value="gemini" disabled={!available.gemini}>Gemini{!available.gemini ? " · belum ada key" : ""}</option>
              </select>
            </div>)}</div>
          <p className="panel-note">Embedding PDF memakai Gemini. Mengubah provider jawaban tidak mengindeks ulang PDF.</p>
        </section>
      </main>}
  </div>;
}
