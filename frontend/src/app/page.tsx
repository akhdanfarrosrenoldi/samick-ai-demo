"use client";

import { useEffect, useRef, useState } from "react";
import Image from "next/image";

const API = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

type Product = { id: string; name: string; category: string; body: string; top: string; back_sides: string; electronics: string; image: string };
type ChatResult = { answer: string; products: Product[] };
type VisionResult = { observed_features: string; reason: string; uncertain: boolean; candidates: Product[] };
type Message = { id: number; role: "user" | "assistant"; text: string; products?: Product[] };

const slides = [
  { src: "/brand/main_img2.jpg", alt: "Gitar akustik Greg Bennett Samick" },
  { src: "/brand/main_img1.jpg", alt: "Piano grand Samick" },
  { src: "/brand/main_img3.jpg", alt: "Piano grand Seiler" },
];
const categoryOrder = ["Akustik Standard", "Akustik Intermediate", "Akustik Pro", "Elektrik"];

async function errorText(response: Response) {
  const data = await response.json().catch(() => ({}));
  return data.detail || `Permintaan gagal (${response.status})`;
}

function productImage(path: string) {
  return path.startsWith("/api/product-images/") ? `${API}${path}` : path;
}

function ProductCard({ product, compact = false }: { product: Product; compact?: boolean }) {
  return <article className={`guitar-item${compact ? " guitar-item-small" : ""}`}>
    <div className="guitar-image"><Image src={productImage(product.image)} alt={product.name} fill unoptimized={product.image.startsWith("/api/")} sizes={compact ? "96px" : "(max-width: 760px) 46vw, (max-width: 1080px) 30vw, 260px"} /></div>
    <div className="guitar-info"><span>{product.category}</span><h3>{product.name}</h3><p>{product.body} · {product.top}</p>
      {!compact && <dl><div><dt>Belakang / sisi</dt><dd>{product.back_sides}</dd></div><div><dt>Elektronik</dt><dd>{product.electronics}</dd></div></dl>}
    </div>
  </article>;
}

function HeroCarousel() {
  const [current, setCurrent] = useState(0);
  const [paused, setPaused] = useState(false);
  const [reducedMotion, setReducedMotion] = useState(false);

  useEffect(() => {
    const preference = window.matchMedia("(prefers-reduced-motion: reduce)");
    const update = () => setReducedMotion(preference.matches);
    update();
    preference.addEventListener("change", update);
    return () => preference.removeEventListener("change", update);
  }, []);
  useEffect(() => {
    if (paused || reducedMotion) return;
    const timer = window.setInterval(() => setCurrent(index => (index + 1) % slides.length), 6000);
    return () => window.clearInterval(timer);
  }, [paused, reducedMotion]);

  return <section className="hero-carousel" aria-label="Sorotan Samick" aria-roledescription="carousel" onMouseEnter={() => setPaused(true)} onMouseLeave={() => setPaused(false)} onFocusCapture={() => setPaused(true)} onBlurCapture={event => { if (!event.currentTarget.contains(event.relatedTarget)) setPaused(false); }}>
    <div className="hero-viewport">
      {slides.map((slide, index) => <div className={`hero-slide${current === index ? " active" : ""}`} key={slide.src} aria-hidden={current !== index}>
        <Image src={slide.src} alt={current === index ? slide.alt : ""} fill sizes="100vw" priority={index === 0} />
      </div>)}
      <button className="hero-arrow hero-prev" type="button" aria-label="Gambar sebelumnya" onClick={() => setCurrent(index => (index + slides.length - 1) % slides.length)}>‹</button>
      <button className="hero-arrow hero-next" type="button" aria-label="Gambar berikutnya" onClick={() => setCurrent(index => (index + 1) % slides.length)}>›</button>
      <div className="hero-dots" aria-label="Pilih gambar">{slides.map((slide, index) => <button type="button" key={slide.src} aria-label={`Gambar ${index + 1}`} aria-current={current === index ? "true" : undefined} className={current === index ? "active" : ""} onClick={() => setCurrent(index)} />)}</div>
    </div>
  </section>;
}

function ChatIcon() {
  return <svg viewBox="0 0 24 24" width="23" height="23" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M20 11.5a8 8 0 0 1-8 8 8.5 8.5 0 0 1-3.2-.6L4 20l1.1-4.6A8 8 0 1 1 20 11.5Z" /><path d="M8.5 11.5h7" /></svg>;
}

function AssistantBubble({ open, onOpenChange }: { open: boolean; onOpenChange: (value: boolean) => void }) {
  const [messages, setMessages] = useState<Message[]>([{ id: 0, role: "assistant", text: "Halo! Gitar seperti apa yang Anda cari? Ceritakan kebutuhan Anda, atau kirim foto gitar." }]);
  const [query, setQuery] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [camera, setCamera] = useState(false);
  const fileInput = useRef<HTMLInputElement>(null);
  const video = useRef<HTMLVideoElement>(null);
  const stream = useRef<MediaStream | null>(null);
  const chatMessages = useRef<HTMLDivElement>(null);
  const nextId = useRef(1);

  useEffect(() => { if (open && chatMessages.current) chatMessages.current.scrollTo({ top: chatMessages.current.scrollHeight, behavior: "smooth" }); }, [messages, busy, error, open]);
  useEffect(() => () => stream.current?.getTracks().forEach(track => track.stop()), []);
  useEffect(() => { if (camera && video.current && stream.current) video.current.srcObject = stream.current; }, [camera]);

  function addMessage(role: Message["role"], text: string, products?: Product[]) {
    setMessages(previous => [...previous, { id: nextId.current++, role, text, products }]);
  }
  async function ask() {
    const message = query.trim();
    if (!message || busy) return;
    const history = messages.slice(-6).map(item => ({ role: item.role, content: item.text }));
    setQuery(""); setError(""); setBusy(true); addMessage("user", message);
    try {
      const response = await fetch(`${API}/api/product-chat`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ message, history }) });
      if (!response.ok) throw Error(await errorText(response));
      const data: ChatResult = await response.json();
      addMessage("assistant", data.answer, data.products);
    } catch (cause) { setError(cause instanceof Error ? cause.message : "Pertanyaan belum dapat diproses."); }
    finally { setBusy(false); }
  }
  async function analyze(file: File) {
    if (busy) return;
    setError(""); setBusy(true); addMessage("user", `Foto gitar: ${file.name}`);
    try {
      const form = new FormData(); form.append("file", file);
      const response = await fetch(`${API}/api/vision/identify`, { method: "POST", body: form });
      if (!response.ok) throw Error(await errorText(response));
      const data: VisionResult = await response.json();
      addMessage("assistant", `${data.observed_features}\n\n${data.reason}${data.uncertain ? "\n\nModel belum dapat dipastikan dari foto ini." : ""}`, data.candidates);
    } catch (cause) { setError(cause instanceof Error ? cause.message : "Foto belum dapat dianalisis."); }
    finally { setBusy(false); if (fileInput.current) fileInput.current.value = ""; }
  }
  async function openCamera() {
    setError("");
    try { stream.current = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" }, audio: false }); setCamera(true); }
    catch { setError("Kamera tidak tersedia atau izin ditolak. Anda masih bisa mengunggah foto."); }
  }
  function closeCamera() { stream.current?.getTracks().forEach(track => track.stop()); stream.current = null; setCamera(false); }
  function capture() {
    const source = video.current; if (!source || !source.videoWidth) return;
    const canvas = document.createElement("canvas"); canvas.width = source.videoWidth; canvas.height = source.videoHeight;
    canvas.getContext("2d")?.drawImage(source, 0, 0);
    canvas.toBlob(blob => { if (blob) { closeCamera(); void analyze(new File([blob], "foto-kamera.jpg", { type: "image/jpeg" })); } }, "image/jpeg", 0.9);
  }
  function close() { closeCamera(); onOpenChange(false); }

  return <>
    <button className="chat-launcher" type="button" aria-label={open ? "Tutup asisten gitar" : "Buka asisten gitar"} aria-expanded={open} aria-controls="assistant-panel" onClick={() => open ? close() : onOpenChange(true)}><ChatIcon /><span>Asisten Gitar</span></button>
    {open && <section className="chat-panel" id="assistant-panel" aria-label="Percakapan dengan asisten gitar">
      <header className="chat-head"><div><strong>Asisten Gitar</strong><small>Tanya produk atau kirim satu foto</small></div><button type="button" onClick={close} aria-label="Tutup percakapan">×</button></header>
      <div className="chat-messages" ref={chatMessages} role="log" aria-live="polite" aria-relevant="additions text">
        {messages.map(item => <div className={`chat-message ${item.role}`} key={item.id}><p>{item.text}</p>{item.products && item.products.length > 0 && <div className="chat-products">{item.products.map(product => <ProductCard key={product.id} product={product} compact />)}</div>}</div>)}
        {busy && <p className="chat-wait">Sedang memproses…</p>}
        {error && <p className="chat-error" role="alert">{error}</p>}
        {camera && <div className="camera-view"><video ref={video} autoPlay playsInline muted /><div><button type="button" onClick={capture}>Ambil foto</button><button type="button" onClick={closeCamera}>Batal</button></div></div>}
      </div>
      <form className="chat-compose" onSubmit={event => { event.preventDefault(); void ask(); }}>
        <div className="chat-tools"><button type="button" onClick={() => fileInput.current?.click()} disabled={busy}>＋ Foto</button><button type="button" onClick={() => void openCamera()} disabled={busy || camera}>◎ Kamera</button><input ref={fileInput} type="file" accept="image/jpeg,image/png,image/webp" hidden aria-label="Unggah foto gitar" onChange={event => { const file = event.target.files?.[0]; if (file) void analyze(file); }} /></div>
        <div className="chat-input-row"><input value={query} onChange={event => setQuery(event.target.value)} placeholder="Tulis pertanyaan tentang gitar…" aria-label="Pertanyaan tentang gitar" /><button type="submit" disabled={busy || !query.trim()}>Kirim</button></div>
      </form>
    </section>}
  </>;
}

export default function Home() {
  const [products, setProducts] = useState<Product[]>([]);
  const [category, setCategory] = useState("Semua");
  const [catalogError, setCatalogError] = useState("");
  const [chatOpen, setChatOpen] = useState(false);
  const availableCategories = [...new Set(products.map(product => product.category))];
  const categories = ["Semua", ...categoryOrder.filter(item => availableCategories.includes(item)), ...availableCategories.filter(item => !categoryOrder.includes(item))];
  const shown = category === "Semua" ? products : products.filter(product => product.category === category);

  useEffect(() => { fetch(`${API}/api/products`).then(response => { if (!response.ok) throw Error(); return response.json(); }).then(setProducts).catch(() => setCatalogError("Katalog belum dapat dimuat. Periksa koneksi aplikasi.")); }, []);

  return <div className="public-site" id="beranda">
    <header className="site-header"><a className="site-logo" href="#beranda" aria-label="Samick, ke beranda"><Image src="/brand/logo.jpg" alt="Samick" width={209} height={60} priority /></a>
      <nav className="site-nav" aria-label="Navigasi utama"><a href="#beranda">Beranda</a><a href="#produk">Produk</a><button type="button" onClick={() => setChatOpen(true)}>Asisten</button></nav>
    </header>
    <main><HeroCarousel />
      <section className="catalog-section" id="produk"><div className="catalog-intro"><div><span className="catalog-kicker">PRODUK</span><h1>Gitar Samick</h1></div><p>Pilih model melalui bentuk bodi, material, dan fitur yang sesuai dengan cara Anda bermain.</p></div>
        <div className="catalog-filters" role="group" aria-label="Kategori gitar">{categories.map(item => <button key={item} type="button" className={category === item ? "active" : ""} aria-pressed={category === item} onClick={() => setCategory(item)}>{item === "Semua" ? "Semua gitar" : item}</button>)}</div>
        {catalogError && <p className="catalog-error" role="alert">{catalogError}</p>}
        <div className="guitar-grid">{shown.map(product => <ProductCard key={product.id} product={product} />)}</div>
      </section>
    </main>
    <footer className="site-footer"><Image src="/brand/logo.jpg" alt="Samick" width={145} height={42} /><span>Gitar, informasi produk, dan asisten pilihan.</span></footer>
    <AssistantBubble open={chatOpen} onOpenChange={setChatOpen} />
  </div>;
}
