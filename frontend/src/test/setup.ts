import "@testing-library/jest-dom/vitest";

// jsdom doesn't implement matchMedia — ThemeProvider's system-theme
// detection needs it, so tests get a deterministic (light) mock.
Object.defineProperty(window, "matchMedia", {
  writable: true,
  value: (query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => false,
  }),
});
