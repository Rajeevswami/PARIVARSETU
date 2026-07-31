import { STORAGE_TOKEN_KEY } from "@/constants";

/**
 * Access token lives in memory only (cleared on refresh, not persisted) —
 * the refresh token is the one persisted, in localStorage, so a page
 * reload can silently re-establish a session via the refresh endpoint.
 */
let accessToken: string | null = null;

export const tokenStorage = {
  getAccessToken: () => accessToken,
  setAccessToken: (token: string | null) => {
    accessToken = token;
  },
  getRefreshToken: () => localStorage.getItem(STORAGE_TOKEN_KEY),
  setRefreshToken: (token: string | null) => {
    if (token) localStorage.setItem(STORAGE_TOKEN_KEY, token);
    else localStorage.removeItem(STORAGE_TOKEN_KEY);
  },
  clear: () => {
    accessToken = null;
    localStorage.removeItem(STORAGE_TOKEN_KEY);
  },
};
