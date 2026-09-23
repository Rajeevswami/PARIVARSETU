import { APP_NAME } from "@/constants";
import { SignupForm } from "@/features/auth/components/SignupForm";

export function SignupPage() {
  return (
    <main id="main" className="flex min-h-screen flex-col items-center justify-center gap-6 px-4">
      <div className="text-center">
        <h1 className="text-2xl font-semibold">{APP_NAME}</h1>
        <p className="text-sm text-muted-foreground">Create your family account</p>
      </div>
      <SignupForm />
    </main>
  );
}
