export const APP_NAME = "FamilyNexus";
export const APP_MARK = "FN";
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1";
/** Stores the refresh token. Access tokens stay in memory. */
export const STORAGE_TOKEN_KEY = "familynexus_access_token";
export const LEGACY_STORAGE_TOKEN_KEY = "parivarsetu_access_token";
export const THEME_STORAGE_KEY = "familynexus-theme";
export const LEGACY_THEME_STORAGE_KEY = "parivarsetu-theme";
