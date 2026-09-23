import { Link } from "react-router-dom";

import { APP_NAME } from "@/constants";
import { LoginForm } from "@/features/auth/components/LoginForm";

export function LoginPage() {
  return (
    <main id="main" className="flex min-h-screen flex-col items-center justify-center gap-6 px-4">
      <div className="text-center">
        <h1 className="text-2xl font-semibold">{APP_NAME}</h1>
        <p className="text-sm text-muted-foreground">Sign in to your family's account</p>
      </div>
      <LoginForm />
      <p className="text-sm">
        <Link to="/signup">Create an account</Link> · <Link to="/welcome">About FamilyNexus</Link> ·{" "}
        <Link to="/pricing">Pricing</Link>
      </p>
    </main>
  );
}
