import { AppProviders } from "@/app/providers";
import { AppRoutes } from "@/routes";

function App() {
  return (
    <AppProviders>
      <AppRoutes />
    </AppProviders>
  );
}

export default App;
