import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { useNavigate, useSearchParams } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAcceptInvitation } from "@/features/members/hooks/useMembers";
import {
  acceptInvitationSchema,
  type AcceptInvitationFormValues,
} from "@/features/members/schemas/memberSchemas";

export function AcceptInvitationPage() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token") ?? "";
  const navigate = useNavigate();
  const acceptInvitation = useAcceptInvitation();

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<AcceptInvitationFormValues>({ resolver: zodResolver(acceptInvitationSchema) });

  if (!token) {
    return (
      <div className="flex min-h-screen items-center justify-center px-4">
        <p className="text-sm text-destructive">
          This invitation link is missing its token. Please use the link from your email.
        </p>
      </div>
    );
  }

  const onSubmit = (values: AcceptInvitationFormValues) =>
    acceptInvitation.mutate(
      { token, first_name: values.first_name, password: values.password },
      { onSuccess: () => navigate("/login") }
    );

  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-6 px-4">
      <div className="text-center">
        <h1 className="text-xl font-semibold">Join your family on ParivarSetu</h1>
        <p className="text-sm text-muted-foreground">
          Set your name and password to accept the invite.
        </p>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="w-full max-w-sm space-y-4">
        <div className="space-y-1.5">
          <Label htmlFor="first_name">Your name</Label>
          <Input id="first_name" {...register("first_name")} />
          {errors.first_name && (
            <p className="text-sm text-destructive">{errors.first_name.message}</p>
          )}
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="password">Password</Label>
          <Input id="password" type="password" {...register("password")} />
          {errors.password && <p className="text-sm text-destructive">{errors.password.message}</p>}
        </div>

        {acceptInvitation.isError && (
          <p className="text-sm text-destructive">This invitation is invalid or has expired.</p>
        )}

        <Button type="submit" className="w-full" disabled={acceptInvitation.isPending}>
          {acceptInvitation.isPending ? "Joining…" : "Accept invitation"}
        </Button>
      </form>
    </div>
  );
}
