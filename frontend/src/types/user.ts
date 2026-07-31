export type UserRole = "family_admin" | "member" | "future_ready" | "read_only" | "auditor";
export type UserStatus = "active" | "inactive" | "blocked" | "pending_verification";
export type Gender = "male" | "female" | "other" | "prefer_not_to_say" | "";

export interface User {
  id: string;
  email: string;
  mobile: string | null;
  first_name: string;
  last_name: string;
  full_name: string;
  gender: Gender;
  date_of_birth: string | null;
  profile_photo: string | null;
  role: UserRole;
  status: UserStatus;
  is_verified: boolean;
  last_login: string | null;
  created_at: string;
}

export interface AuthTokens {
  access: string;
  refresh: string;
}
