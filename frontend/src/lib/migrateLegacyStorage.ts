import {
  LEGACY_STORAGE_TOKEN_KEY,
  LEGACY_THEME_STORAGE_KEY,
  STORAGE_TOKEN_KEY,
  THEME_STORAGE_KEY,
} from "@/constants";

function moveOnce(legacyKey: string, nextKey: string) {
  const current = localStorage.getItem(nextKey);
  const legacy = localStorage.getItem(legacyKey);
  if (current === null && legacy !== null) {
    localStorage.setItem(nextKey, legacy);
  }
  if (legacy !== null) {
    localStorage.removeItem(legacyKey);
  }
}

/** One-shot browser migration. Never overwrites a value already stored under the new key. */
export function migrateLegacyStorage() {
  moveOnce(LEGACY_STORAGE_TOKEN_KEY, STORAGE_TOKEN_KEY);
  moveOnce(LEGACY_THEME_STORAGE_KEY, THEME_STORAGE_KEY);
}
