"use client";

import { useCallback, useEffect, useState } from "react";
import Image from "next/image";
import { API, request } from "./api";

type Product = {
  id: string; name: string; category: string; body: string; top: string;
  back_sides: string; electronics: string; color: string; image: string; active: boolean;
};
type ProductDraft = Omit<Product, "id">;
const empty: ProductDraft = {
  name: "", category: "Akustik Standard", body: "", top: "", back_sides: "",
  electronics: "Tidak ada", color: "", image: "", active: true,
};
const fields: { key: keyof Omit<ProductDraft, "image" | "active">; label: string }[] = [
  { key: "name", label: "Nama model" }, { key: "category", label: "Kategori" },
  { key: "body", label: "Bentuk bodi" }, { key: "top", label: "Material top" },
  { key: "back_sides", label: "Belakang / sisi" }, { key: "electronics", label: "Elektronik" },
  { key: "color", label: "Warna" },
];

function imageSource(path: string) {
  return path.startsWith("/api/product-images/") ? `${API}${path}` : path;
}

export default function CatalogManager() {
  const [products, setProducts] = useState<Product[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [draft, setDraft] = useState<ProductDraft>(empty);
  const [file, setFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const refresh = useCallback(async () => setProducts(await request<Product[]>("/api/admin/products")), []);
  useEffect(() => { request<Product[]>("/api/admin/products").then(setProducts).catch(cause => setError(cause.message)); }, []);

  function choose(product: Product | null) {
    setSelected(product?.id ?? null);
    setDraft(product ? {
      name: product.name, category: product.category, body: product.body, top: product.top,
      back_sides: product.back_sides, electronics: product.electronics,
      color: product.color, image: product.image, active: product.active,
    } : { ...empty });
    setFile(null); setError(""); setNotice("");
  }

  async function save(event: React.FormEvent) {
    event.preventDefault(); setBusy(true); setError(""); setNotice("");
    try {
      let image = draft.image;
      if (file) {
        const form = new FormData(); form.append("file", file);
        image = (await request<{ image: string }>("/api/admin/product-images", { method: "POST", body: form })).image;
      }
      if (!image) throw Error("Pilih foto produk terlebih dahulu.");
      const path = selected ? `/api/admin/products/${selected}` : "/api/admin/products";
      const saved = await request<Product>(path, {
        method: selected ? "PUT" : "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...draft, image }),
      });
      await refresh(); choose(saved); setNotice("Produk tersimpan. Katalog dan jawaban AI memakai data terbaru.");
    } catch (cause) { setError(cause instanceof Error ? cause.message : "Produk belum tersimpan."); }
    finally { setBusy(false); }
  }

  async function remove() {
    if (!selected || !window.confirm("Hapus produk ini dari katalog?")) return;
    setBusy(true); setError(""); setNotice("");
    try { await request(`/api/admin/products/${selected}`, { method: "DELETE" }); await refresh(); choose(null); setNotice("Produk dihapus dari katalog."); }
    catch (cause) { setError(cause instanceof Error ? cause.message : "Produk belum dihapus."); }
    finally { setBusy(false); }
  }

  return <section className="admin-panel catalog-manager">
    <div className="panel-header"><div><small>01 / KATALOG</small><h2>Produk gitar</h2></div><button className="upload-button" type="button" onClick={() => choose(null)}>+ Produk baru</button></div>
    <p className="panel-note">Produk aktif tampil di website dan menjadi sumber rekomendasi AI. Isi data serta foto secara manual.</p>
    <div className="catalog-admin-layout">
      <div className="catalog-admin-list" aria-label="Daftar produk">
        {products.map(product => <button key={product.id} type="button" className={selected === product.id ? "selected" : ""} onClick={() => choose(product)}>
          <span>{product.name}</span><small>{product.category} · {product.active ? "Aktif" : "Nonaktif"}</small>
        </button>)}
      </div>
      <form className="catalog-admin-form" onSubmit={event => void save(event)}>
        <div className="catalog-form-title"><strong>{selected ? "Edit produk" : "Produk baru"}</strong>{selected && <button type="button" disabled={busy} onClick={() => void remove()}>Hapus</button>}</div>
        <div className="catalog-form-fields">{fields.map(field => <label key={field.key}>{field.label}<input required maxLength={100} value={draft[field.key]} onChange={event => setDraft(previous => ({ ...previous, [field.key]: event.target.value }))} /></label>)}</div>
        <div className="catalog-image-row">{draft.image && <Image src={imageSource(draft.image)} alt={draft.name || "Foto produk"} width={68} height={86} unoptimized={draft.image.startsWith("/api/")} />}
          <label>Foto produk<input type="file" accept="image/jpeg,image/png,image/webp" onChange={event => setFile(event.target.files?.[0] ?? null)} />{file && <small>Foto baru: {file.name}</small>}</label></div>
        <label className="catalog-active"><input type="checkbox" checked={draft.active} onChange={event => setDraft(previous => ({ ...previous, active: event.target.checked }))} /> Tampilkan produk di website</label>
        {error && <p className="admin-error" role="alert">{error}</p>}{notice && <p className="admin-status" role="status">{notice}</p>}
        <button className="catalog-save" disabled={busy}>{busy ? "Menyimpan…" : "Simpan produk"}</button>
      </form>
    </div>
  </section>;
}
