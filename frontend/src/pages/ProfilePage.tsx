import { AvatarUpload } from "@/features/auth/components/AvatarUpload";
import { ChangePasswordDialog } from "@/features/auth/components/ChangePasswordDialog";
import { ProfileEditForm } from "@/features/auth/components/ProfileEditForm";
import { useProfile } from "@/features/auth/hooks/useAuth";

export function ProfilePage() {
  const { data: user, isLoading } = useProfile();

  if (isLoading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center text-muted-foreground">
        Loading…
      </div>
    );
  }

  if (!user) return null;

  return (
    <div className="mx-auto max-w-2xl space-y-8 px-4 py-10">
      <h1 className="text-2xl font-semibold">Your profile</h1>

      <AvatarUpload user={user} />
      <ProfileEditForm user={user} />

      <div className="border-t border-border pt-6">
        <ChangePasswordDialog />
      </div>
    </div>
  );
}
