import { Navigate } from "react-router-dom";

import { CreateFamilyForm } from "@/features/families/components/CreateFamilyForm";
import { useMyFamily } from "@/features/families/hooks/useFamilies";

export function OnboardingPage() {
  const { data: family, isLoading } = useMyFamily();

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center text-muted-foreground">
        Loading…
      </div>
    );
  }
  if (family) {
    return <Navigate to="/members" replace />;
  }

  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-6 px-4">
      <div className="text-center">
        <h1 className="text-2xl font-semibold">Set up your family</h1>
        <p className="text-sm text-muted-foreground">
          Create a family workspace to start managing households and members together.
        </p>
      </div>
      <CreateFamilyForm />
    </div>
  );
}
