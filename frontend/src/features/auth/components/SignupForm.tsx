import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { Link } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

import { useRegister } from "../hooks/useAuth";
import { signupSchema, type SignupFormValues } from "../schemas/authSchemas";

export function SignupForm() {
  const signup = useRegister();
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<SignupFormValues>({ resolver: zodResolver(signupSchema) });

  if (signup.isSuccess && signup.data?.verification_required) {
    return (
      <p className="max-w-sm text-sm text-muted-foreground" role="status">
        Check your email to verify {signup.data.email}. Then you can sign in.
      </p>
    );
  }

  return (
    <form
      onSubmit={handleSubmit((values) =>
        signup.mutate({
          name: values.name,
          email: values.email,
          password: values.password,
          confirm_password: values.confirmPassword,
        })
      )}
      className="w-full max-w-sm space-y-4"
    >
      <div className="space-y-1.5">
        <Label htmlFor="name">Name</Label>
        <Input id="name" autoComplete="name" {...register("name")} />
        {errors.name && <p className="text-sm text-destructive">{errors.name.message}</p>}
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="email">Email</Label>
        <Input id="email" type="email" autoComplete="email" {...register("email")} />
        {errors.email && <p className="text-sm text-destructive">{errors.email.message}</p>}
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="password">Password</Label>
        <Input
          id="password"
          type="password"
          autoComplete="new-password"
          {...register("password")}
        />
        {errors.password && <p className="text-sm text-destructive">{errors.password.message}</p>}
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="confirmPassword">Confirm password</Label>
        <Input
          id="confirmPassword"
          type="password"
          autoComplete="new-password"
          {...register("confirmPassword")}
        />
        {errors.confirmPassword && (
          <p className="text-sm text-destructive">{errors.confirmPassword.message}</p>
        )}
      </div>

      {signup.isError && (
        <p className="text-sm text-destructive" role="alert">
          {(signup.error as { response?: { data?: { message?: string } } })?.response?.data
            ?.message ?? "Could not create the account. Please try again."}
        </p>
      )}

      <Button type="submit" className="w-full" disabled={signup.isPending}>
        {signup.isPending ? "Creating account…" : "Create account"}
      </Button>

      <p className="text-center text-sm text-muted-foreground">
        Already have an account?{" "}
        <Link to="/login" className="underline hover:text-foreground">
          Sign in
        </Link>
      </p>
    </form>
  );
}
