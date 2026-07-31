import { Navigate, Outlet } from "react-router-dom";

import { useMyFamily } from "@/features/families/hooks/useFamilies";

/**
 * Sits inside ProtectedRoute — a logged-in user without a family yet gets
 * sent to onboarding before they can reach households/members/etc.
 */
export function FamilyGuard() {
  const { data: family, isLoading } = useMyFamily();

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center text-muted-foreground">
        Loading…
      </div>
    );
  }

  if (!family) {
    return <Navigate to="/onboarding" replace />;
  }

  return <Outlet />;
}
