import { LoginForm } from "@/features/auth/components/LoginForm";

export function LoginPage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-6 px-4">
      <div className="text-center">
        <h1 className="text-2xl font-semibold">ParivarSetu</h1>
        <p className="text-sm text-muted-foreground">Sign in to your family's account</p>
      </div>
      <LoginForm />
    </div>
  );
}
