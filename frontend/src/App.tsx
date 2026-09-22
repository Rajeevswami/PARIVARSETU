import { AppProviders } from "@/app/providers";
import { CookieBanner } from "@/components/CookieBanner";
import { AppRoutes } from "@/routes";

function App() {
  return (
    <AppProviders>
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:bg-background focus:px-3 focus:py-2"
      >
        Skip to content
      </a>
      <AppRoutes />
      <CookieBanner />
    </AppProviders>
  );
}

export default App;
