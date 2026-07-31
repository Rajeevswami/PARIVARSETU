export interface Family {
  id: string;
  family_name: string;
  family_code: string;
  description: string;
  logo: string | null;
  country: string;
  state: string;
  city: string;
  currency: string;
  language: string;
  timezone: string;
  subscription_plan: "free" | "basic" | "premium" | "enterprise";
  subscription_status: "trial" | "active" | "past_due" | "cancelled" | "expired";
  status: "active" | "inactive" | "suspended";
  member_count: number;
  household_count: number;
  created_at: string;
  updated_at: string;
}
