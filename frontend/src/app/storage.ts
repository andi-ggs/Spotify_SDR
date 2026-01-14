const USER_KEY = "sr_user_id_v1";
const LAST_TRACK_KEY = "sr_last_track_id_v1";
const TOKEN_KEY = "sr_token_v1";

export const storage = {
  getUserId(): string | null {
    return localStorage.getItem(USER_KEY);
  },
  setUserId(id: string) {
    localStorage.setItem(USER_KEY, id);
  },
  clearUser() {
    localStorage.removeItem(USER_KEY);
  },

  getLastTrackId(): string | null {
    return localStorage.getItem(LAST_TRACK_KEY);
  },
  setLastTrackId(trackId: string) {
    localStorage.setItem(LAST_TRACK_KEY, trackId);
  },
  clearLastTrackId() {
    localStorage.removeItem(LAST_TRACK_KEY);
  },
   getToken(): string | null {
    return localStorage.getItem(TOKEN_KEY);
  },
  setToken(t: string) {
    localStorage.setItem(TOKEN_KEY, t);
  },
  clearAuth() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem("sr_user_id_v1");
  },
};
