export const API = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export async function request<T = unknown>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API}${path}`, { credentials: "include", ...options });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw Error(data.detail || `Permintaan gagal (${response.status})`);
  }
  return data as T;
}
