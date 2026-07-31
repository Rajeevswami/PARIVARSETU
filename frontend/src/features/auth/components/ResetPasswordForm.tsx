import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { useSearchParams } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

import { useResetPassword } from "../hooks/useAuth";
import { resetPasswordSchema, type ResetPasswordFormValues } from "../schemas/authSchemas";

export function ResetPasswordForm() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token") ?? "";
  const resetPassword = useResetPassword();

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ResetPasswordFormValues>({ resolver: zodResolver(resetPasswordSchema) });

  if (!token) {
    return (
      <p className="max-w-sm text-sm text-destructive">
        This reset link is missing its token. Please use the link from your email.
      </p>
    );
  }

  const onSubmit = (values: ResetPasswordFormValues) =>
    resetPassword.mutate({
      token,
      newPassword: values.newPassword,
      confirmPassword: values.confirmPassword,
    });

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="w-full max-w-sm space-y-4">
      <div className="space-y-1.5">
        <Label htmlFor="newPassword">New password</Label>
        <Input id="newPassword" type="password" {...register("newPassword")} />
        {errors.newPassword && (
          <p className="text-sm text-destructive">{errors.newPassword.message}</p>
        )}
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="confirmPassword">Confirm new password</Label>
        <Input id="confirmPassword" type="password" {...register("confirmPassword")} />
        {errors.confirmPassword && (
          <p className="text-sm text-destructive">{errors.confirmPassword.message}</p>
        )}
      </div>

      {resetPassword.isError && (
        <p className="text-sm text-destructive">
          This reset link is invalid or has expired. Please request a new one.
        </p>
      )}

      <Button type="submit" className="w-full" disabled={resetPassword.isPending}>
        {resetPassword.isPending ? "Resetting…" : "Reset password"}
      </Button>
    </form>
  );
}
