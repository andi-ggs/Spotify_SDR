import { storage } from "../app/storage";

const API_BASE =
  (import.meta.env.VITE_API_BASE_URL as string) || "http://127.0.0.1:8000";

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = storage.getToken();

  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", 
      ...(token ? { Authorization: `Bearer ${token}` } : {}), 
      ...(options.headers || {}) },
    ...options,
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `HTTP ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export type Preferences = {
  preferred_genres: string[];
  mood?: string | null;

  preferred_energy?: number | null;
  preferred_danceability?: number | null;

  preferred_acousticness?: number | null;
  preferred_instrumentalness?: number | null;
  preferred_valence?: number | null;
  preferred_speechiness?: number | null;
  preferred_liveness?: number | null;
  preferred_tempo?: number | null;
};

export type ViewEventPayload = {
  user_id: string;
  track_id: string;
  duration_ms: number; // IMPORTANT: always send this now
  recomm_id?: string | null;
};

export type RatingEventPayload = {
  user_id: string;
  track_id: string;
  rating: 1 | -1;
  recomm_id?: string | null;
};

export const api = {
  createUser: (user_id: string) =>
    request<{ user_id: string; created_at: string }>("/users", {
      method: "POST",
      body: JSON.stringify({ user_id }),
    }),

  setPrefs: (user_id: string, prefs: Preferences) =>
    request<{ ok: boolean }>(`/users/${encodeURIComponent(user_id)}/preferences`, {
      method: "PUT",
      body: JSON.stringify(prefs),
    }),

  getUser: (user_id: string) =>
    request<any>(`/users/${encodeURIComponent(user_id)}`),

  getUserInteractions: (user_id: string) =>
    request<any>(`/users/${encodeURIComponent(user_id)}/interactions?limit=50`),

  listTracks: (q?: string, limit = 24, offset = 0) => {
    const params = new URLSearchParams();
    if (q) params.set("q", q);
    params.set("limit", String(limit));
    params.set("offset", String(offset));
    return request<{ items: any[] }>(`/tracks?${params.toString()}`);
  },

  recommendForYou: (user_id: string, count = 10) =>
    request<{ recomm_id: string; tracks: any[] }>("/recommendations/for-you", {
      method: "POST",
      body: JSON.stringify({ user_id, count }),
    }),

  recommendKnowledgeOnly: (user_id: string, count = 10) =>
    request<{ recomm_id: string; tracks: any[] }>("/recommendations/knowledge-only", {
      method: "POST",
      body: JSON.stringify({ user_id, count }),
    }),

  recommendSimilar: (track_id: string, user_id: string, count = 10) =>
    request<{ recomm_id: string; tracks: any[] }>(
      `/recommendations/similar/${encodeURIComponent(track_id)}?user_id=${encodeURIComponent(
        user_id
      )}&count=${count}`
    ),

  eventView: (payload: ViewEventPayload) =>
    request<{ ok: boolean }>("/events/view", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  eventRating: (payload: RatingEventPayload) =>
    request<{ ok: boolean }>("/events/rating", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

    register: (user_id: string, password: string) =>
    request<{ user_id: string; access_token: string; token_type: string }>("/auth/register", {
      method: "POST",
      body: JSON.stringify({ user_id, password }),
    }),

  login: (user_id: string, password: string) =>
    request<{ user_id: string; access_token: string; token_type: string }>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ user_id, password }),
    }),
};
