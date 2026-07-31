import { Link } from "react-router-dom";

import { ForgotPasswordForm } from "@/features/auth/components/ForgotPasswordForm";

export function ForgotPasswordPage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-6 px-4">
      <div className="text-center">
        <h1 className="text-xl font-semibold">Reset your password</h1>
        <p className="text-sm text-muted-foreground">
          We'll email you a link to get back into your account.
        </p>
      </div>
      <ForgotPasswordForm />
      <Link to="/login" className="text-sm text-muted-foreground underline hover:text-foreground">
        Back to sign in
      </Link>
    </div>
  );
}
