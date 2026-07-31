import { z } from "zod";

export const householdSchema = z.object({
  household_name: z.string().min(1, "Household name is required.").max(150),
  description: z.string().max(1000).optional().or(z.literal("")),
  address: z.string().max(1000).optional().or(z.literal("")),
  contact_number: z.string().max(17).optional().or(z.literal("")),
});
export type HouseholdFormValues = z.infer<typeof householdSchema>;

export const changeHeadSchema = z.object({
  member_id: z.string().min(1, "Select a member."),
});
export type ChangeHeadFormValues = z.infer<typeof changeHeadSchema>;
