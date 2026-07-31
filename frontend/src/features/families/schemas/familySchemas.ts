import { z } from "zod";

export const createFamilySchema = z.object({
  family_name: z.string().min(1, "Family name is required.").max(150),
  description: z.string().max(1000).optional().or(z.literal("")),
  country: z.string().max(100).optional().or(z.literal("")),
  state: z.string().max(100).optional().or(z.literal("")),
  city: z.string().max(100).optional().or(z.literal("")),
  currency: z.string().max(3).optional().or(z.literal("")),
});
export type CreateFamilyFormValues = z.infer<typeof createFamilySchema>;

export const editFamilySchema = z.object({
  family_name: z.string().min(1, "Family name is required.").max(150),
  description: z.string().max(1000).optional().or(z.literal("")),
  country: z.string().max(100).optional().or(z.literal("")),
  state: z.string().max(100).optional().or(z.literal("")),
  city: z.string().max(100).optional().or(z.literal("")),
});
export type EditFamilyFormValues = z.infer<typeof editFamilySchema>;
