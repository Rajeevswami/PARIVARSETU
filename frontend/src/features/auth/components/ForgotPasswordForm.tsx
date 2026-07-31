import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

import { useForgotPassword } from "../hooks/useAuth";
import { forgotPasswordSchema, type ForgotPasswordFormValues } from "../schemas/authSchemas";

export function ForgotPasswordForm() {
  const forgotPassword = useForgotPassword();
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ForgotPasswordFormValues>({ resolver: zodResolver(forgotPasswordSchema) });

  if (forgotPassword.isSuccess) {
    return (
      <p className="max-w-sm text-sm text-muted-foreground">
        If an account exists for that email or mobile number, we've sent a password reset link.
      </p>
    );
  }

  return (
    <form
      onSubmit={handleSubmit((values) => forgotPassword.mutate(values.identifier))}
      className="w-full max-w-sm space-y-4"
    >
      <div className="space-y-1.5">
        <Label htmlFor="identifier">Email or mobile number</Label>
        <Input id="identifier" {...register("identifier")} />
        {errors.identifier && (
          <p className="text-sm text-destructive">{errors.identifier.message}</p>
        )}
      </div>

      <Button type="submit" className="w-full" disabled={forgotPassword.isPending}>
        {forgotPassword.isPending ? "Sending…" : "Send reset link"}
      </Button>
    </form>
  );
}
