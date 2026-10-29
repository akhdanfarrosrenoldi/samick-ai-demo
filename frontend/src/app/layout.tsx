import type { Metadata } from "next";
import "./globals.css";
export const metadata: Metadata = { title: "Samick | Gitar dan Asisten Produk", description: "Jelajahi koleksi gitar Samick dan temukan model yang sesuai dengan kebutuhan Anda." };
export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) { return <html lang="id"><body>{children}</body></html>; }
