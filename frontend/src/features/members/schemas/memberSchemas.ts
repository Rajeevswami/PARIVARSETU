import { z } from "zod";

export const RELATIONSHIP_OPTIONS = [
  "father",
  "mother",
  "son",
  "daughter",
  "brother",
  "sister",
  "grandfather",
  "grandmother",
  "uncle",
  "aunt",
  "cousin",
  "other",
] as const;

export const inviteMemberSchema = z
  .object({
    email: z.string().email("Enter a valid email.").optional().or(z.literal("")),
    mobile: z.string().optional().or(z.literal("")),
    household: z.string().optional().or(z.literal("")),
    relationship: z.enum(RELATIONSHIP_OPTIONS).optional().or(z.literal("")),
  })
  .refine((data) => data.email || data.mobile, {
    message: "Provide an email or a mobile number.",
    path: ["email"],
  });
export type InviteMemberFormValues = z.infer<typeof inviteMemberSchema>;

export const transferMemberSchema = z.object({
  household_id: z.string().min(1, "Select a household."),
});
export type TransferMemberFormValues = z.infer<typeof transferMemberSchema>;

export const memberProfileSchema = z.object({
  display_name: z.string().min(1, "Display name is required.").max(150),
  relationship: z.enum(RELATIONSHIP_OPTIONS).optional().or(z.literal("")),
  gender: z.string().optional().or(z.literal("")),
  blood_group: z.string().optional().or(z.literal("")),
  marital_status: z.string().optional().or(z.literal("")),
  occupation: z.string().max(150).optional().or(z.literal("")),
  date_of_birth: z.string().optional().or(z.literal("")),
  emergency_contact: z.string().max(17).optional().or(z.literal("")),
  notes: z.string().max(2000).optional().or(z.literal("")),
});
export type MemberProfileFormValues = z.infer<typeof memberProfileSchema>;

export const acceptInvitationSchema = z.object({
  first_name: z.string().min(1, "Your name is required."),
  password: z
    .string()
    .min(8, "Password must be at least 8 characters.")
    .regex(/[A-Z]/, "Include at least one uppercase letter.")
    .regex(/[a-z]/, "Include at least one lowercase letter.")
    .regex(/\d/, "Include at least one number.")
    .regex(/[!@#$%^&*()\-_=+[\]{};:'",.<>/?\\|`~]/, "Include at least one special character."),
});
export type AcceptInvitationFormValues = z.infer<typeof acceptInvitationSchema>;
