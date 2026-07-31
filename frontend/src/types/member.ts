export type Relationship =
  | "father"
  | "mother"
  | "son"
  | "daughter"
  | "brother"
  | "sister"
  | "grandfather"
  | "grandmother"
  | "uncle"
  | "aunt"
  | "cousin"
  | "other"
  | "";

export interface Member {
  id: string;
  user: string;
  email: string;
  role: string;
  family: string;
  household: string | null;
  household_name: string | null;
  employee_code: string;
  display_name: string;
  relationship: Relationship;
  gender: string;
  blood_group: string;
  marital_status: string;
  occupation: string;
  date_of_birth: string | null;
  joining_date: string;
  photo: string | null;
  aadhaar_number_ready: boolean;
  pan_number_ready: boolean;
  emergency_contact: string;
  notes: string;
  status: "active" | "inactive";
  created_at: string;
}

export interface MemberInvitation {
  id: string;
  family: string;
  household: string | null;
  email: string | null;
  mobile: string | null;
  role: string;
  relationship: Relationship;
  status: "pending" | "accepted" | "rejected" | "expired";
  created_at: string;
  expires_at: string;
}
