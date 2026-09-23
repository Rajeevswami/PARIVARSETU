import { useEffect, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { authApi } from "@/features/auth/api/authApi";
import { tokenStorage } from "@/lib/tokenStorage";

export function VerifyEmailPage() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const token = params.get("token") ?? "";
  const [error, setError] = useState(token ? "" : "This verification link is missing a token.");

  useEffect(() => {
    if (!token) return;
    let cancelled = false;
    authApi
      .verifyEmail(token)
      .then((data) => {
        if (cancelled) return;
        tokenStorage.setAccessToken(data.tokens.access);
        tokenStorage.setRefreshToken(data.tokens.refresh);
        navigate("/onboarding", { replace: true });
      })
      .catch(() => {
        if (!cancelled) setError("This verification link is invalid or has expired.");
      });
    return () => {
      cancelled = true;
    };
  }, [navigate, token]);

  return (
    <main id="main" className="flex min-h-screen flex-col items-center justify-center gap-4 px-4">
      <h1 className="text-2xl font-semibold">Verify email</h1>
      {error ? (
        <>
          <p className="text-sm text-destructive" role="alert">
            {error}
          </p>
          <Button asChild>
            <Link to="/login">Back to sign in</Link>
          </Button>
        </>
      ) : (
        <p className="text-sm text-muted-foreground">Confirming your email…</p>
      )}
    </main>
  );
}
