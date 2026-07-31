import { Navigate, Outlet } from "react-router-dom";

import { useProfile } from "@/features/auth/hooks/useAuth";
import { tokenStorage } from "@/lib/tokenStorage";

export function ProtectedRoute() {
  const hasSession = Boolean(tokenStorage.getAccessToken() || tokenStorage.getRefreshToken());
  const { isLoading, isError } = useProfile();

  if (!hasSession || isError) {
    return <Navigate to="/login" replace />;
  }

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center text-muted-foreground">
        Loading…
      </div>
    );
  }

  return <Outlet />;
}
