import { z } from "zod";

// Mirrors the backend's PasswordComplexityValidator exactly — same rules,
// same messages where practical, so errors feel consistent end to end.
const passwordSchema = z
  .string()
  .min(8, "Password must be at least 8 characters.")
  .max(128, "Password must be at most 128 characters.")
  .regex(/[A-Z]/, "Include at least one uppercase letter.")
  .regex(/[a-z]/, "Include at least one lowercase letter.")
  .regex(/\d/, "Include at least one number.")
  .regex(/[!@#$%^&*()\-_=+[\]{};:'",.<>/?\\|`~]/, "Include at least one special character.");

export const loginSchema = z.object({
  identifier: z.string().min(1, "Enter your email or mobile number."),
  password: z.string().min(1, "Password is required."),
});
export type LoginFormValues = z.infer<typeof loginSchema>;

export const forgotPasswordSchema = z.object({
  identifier: z.string().min(1, "Enter your email or mobile number."),
});
export type ForgotPasswordFormValues = z.infer<typeof forgotPasswordSchema>;

export const resetPasswordSchema = z
  .object({
    newPassword: passwordSchema,
    confirmPassword: z.string().min(1, "Please confirm your new password."),
  })
  .refine((data) => data.newPassword === data.confirmPassword, {
    message: "Passwords do not match.",
    path: ["confirmPassword"],
  });
export type ResetPasswordFormValues = z.infer<typeof resetPasswordSchema>;

export const changePasswordSchema = z
  .object({
    oldPassword: z.string().min(1, "Current password is required."),
    newPassword: passwordSchema,
    confirmPassword: z.string().min(1, "Please confirm your new password."),
  })
  .refine((data) => data.newPassword === data.confirmPassword, {
    message: "Passwords do not match.",
    path: ["confirmPassword"],
  })
  .refine((data) => data.oldPassword !== data.newPassword, {
    message: "New password must be different from the current password.",
    path: ["newPassword"],
  });
export type ChangePasswordFormValues = z.infer<typeof changePasswordSchema>;

export const profileUpdateSchema = z.object({
  first_name: z.string().min(1, "First name is required.").max(150),
  last_name: z.string().max(150).optional().or(z.literal("")),
  gender: z.enum(["male", "female", "other", "prefer_not_to_say", ""]).optional(),
  date_of_birth: z.string().optional().or(z.literal("")),
});
export type ProfileUpdateFormValues = z.infer<typeof profileUpdateSchema>;
