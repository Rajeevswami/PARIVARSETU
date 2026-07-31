import { useRef } from "react";

import { Button } from "@/components/ui/button";
import type { User } from "@/types/user";

import { useUploadAvatar } from "../hooks/useAuth";

export function AvatarUpload({ user }: { user: User }) {
  const inputRef = useRef<HTMLInputElement>(null);
  const uploadAvatar = useUploadAvatar();

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) uploadAvatar.mutate(file);
  };

  return (
    <div className="flex items-center gap-4">
      <div className="h-16 w-16 overflow-hidden rounded-full bg-muted">
        {user.profile_photo ? (
          <img
            src={user.profile_photo}
            alt={user.full_name}
            className="h-full w-full object-cover"
          />
        ) : (
          <div className="flex h-full w-full items-center justify-center text-sm text-muted-foreground">
            {user.first_name[0]}
          </div>
        )}
      </div>

      <input
        ref={inputRef}
        type="file"
        accept="image/*"
        className="hidden"
        onChange={handleFileChange}
      />
      <Button
        type="button"
        variant="outline"
        size="sm"
        onClick={() => inputRef.current?.click()}
        disabled={uploadAvatar.isPending}
      >
        {uploadAvatar.isPending ? "Uploading…" : "Change photo"}
      </Button>
    </div>
  );
}
