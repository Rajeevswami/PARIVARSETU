export interface Household {
  id: string;
  family: string;
  household_name: string;
  household_code: string;
  description: string;
  head_of_household: string | null;
  head_of_household_name: string | null;
  address: string;
  contact_number: string;
  status: "active" | "inactive";
  member_count: number;
  created_at: string;
  updated_at: string;
}
