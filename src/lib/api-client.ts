/**
 * Typed API client for frontend use.
 * Handles JWT token injection and error responses.
 */

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string
  ) {
    super(message);
    this.name = "ApiError";
  }
}

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("token");
}

export async function apiFetch<T>(
  url: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(url, {
    ...options,
    headers,
  });

  const data = await res.json();

  if (!res.ok) {
    throw new ApiError(res.status, data.error || "请求失败");
  }

  return data as T;
}

export async function apiUpload<T>(
  url: string,
  formData: FormData
): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {};

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  // Don't set Content-Type for FormData — browser sets multipart boundary
  const res = await fetch(url, {
    method: "POST",
    headers,
    body: formData,
  });

  const data = await res.json();

  if (!res.ok) {
    throw new ApiError(res.status, data.error || "上传失败");
  }

  return data as T;
}
