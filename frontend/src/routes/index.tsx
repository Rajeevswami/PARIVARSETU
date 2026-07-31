import { Navigate, Route, Routes } from "react-router-dom";

import { MainLayout } from "@/layouts/MainLayout";
import { AcceptInvitationPage } from "@/pages/AcceptInvitationPage";
import { BorrowLendPage } from "@/pages/BorrowLendPage";
import { CategoryManagerPage } from "@/pages/CategoryManagerPage";
import { ExpenseDetailPage } from "@/pages/ExpenseDetailPage";
import { ExpenseListPage } from "@/pages/ExpenseListPage";
import { FamilySettingsPage } from "@/pages/FamilySettingsPage";
import { ForgotPasswordPage } from "@/pages/ForgotPasswordPage";
import { HouseholdDetailPage } from "@/pages/HouseholdDetailPage";
import { HouseholdListPage } from "@/pages/HouseholdListPage";
import { ChartOfAccountsPage } from "@/pages/ChartOfAccountsPage";
import { JournalDetailPage } from "@/pages/JournalDetailPage";
import { JournalListPage } from "@/pages/JournalListPage";
import { TrialBalancePage } from "@/pages/TrialBalancePage";
import { LoanDetailPage } from "@/pages/LoanDetailPage";
import { LoanListPage } from "@/pages/LoanListPage";
import { LoanRemindersPage } from "@/pages/LoanRemindersPage";
import { LoginPage } from "@/pages/LoginPage";
import { MemberDirectoryPage } from "@/pages/MemberDirectoryPage";
import { MemberProfilePage } from "@/pages/MemberProfilePage";
import { OnboardingPage } from "@/pages/OnboardingPage";
import { ProfilePage } from "@/pages/ProfilePage";
import { DashboardPage } from "@/pages/DashboardPage";
import { AnalyticsPage } from "@/pages/AnalyticsPage";
import { ReportsPage } from "@/pages/ReportsPage";
import { ResetPasswordPage } from "@/pages/ResetPasswordPage";
import { NotificationsPage } from "@/pages/NotificationsPage";
import { AuditLogsPage } from "@/pages/AuditLogsPage";
import { SettingsPage } from "@/pages/SettingsPage";
import { ForbiddenPage, NotFoundPage } from "@/pages/SystemErrorPages";
import { DocumentsPage } from "@/pages/DocumentsPage";

import { FamilyGuard } from "./FamilyGuard";
import { ProtectedRoute } from "./ProtectedRoute";

/**
 * Route tree is intentionally minimal — feature routes (expenses, loans,
 * ledger, dashboard, etc.) are added as each module lands.
 */
export function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/forgot-password" element={<ForgotPasswordPage />} />
      <Route path="/reset-password" element={<ResetPasswordPage />} />
      <Route path="/accept-invitation" element={<AcceptInvitationPage />} />
      <Route path="/forbidden" element={<ForbiddenPage />} />

      <Route element={<ProtectedRoute />}>
        <Route element={<MainLayout />}>
          <Route path="/onboarding" element={<OnboardingPage />} />
          <Route path="/profile" element={<ProfilePage />} />

          <Route element={<FamilyGuard />}>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/analytics" element={<AnalyticsPage />} />
            <Route path="/reports" element={<ReportsPage />} />
            <Route path="/documents" element={<DocumentsPage />} />
            <Route path="/notifications" element={<NotificationsPage />} />
            <Route path="/audit" element={<AuditLogsPage />} />
            <Route path="/settings" element={<SettingsPage />} />
            <Route path="/family" element={<FamilySettingsPage />} />
            <Route path="/households" element={<HouseholdListPage />} />
            <Route path="/households/:id" element={<HouseholdDetailPage />} />
            <Route path="/members" element={<MemberDirectoryPage />} />
            <Route path="/members/:id" element={<MemberProfilePage />} />
            <Route path="/expenses" element={<ExpenseListPage />} />
            <Route path="/expenses/categories" element={<CategoryManagerPage />} />
            <Route path="/expenses/:id" element={<ExpenseDetailPage />} />
            <Route path="/loans" element={<LoanListPage />} />
            <Route path="/loans/reminders" element={<LoanRemindersPage />} />
            <Route path="/loans/:id" element={<LoanDetailPage />} />
            <Route path="/borrow-lend" element={<BorrowLendPage />} />
            <Route path="/ledger" element={<JournalListPage />} />
            <Route path="/ledger/accounts" element={<ChartOfAccountsPage />} />
            <Route path="/ledger/trial-balance" element={<TrialBalancePage />} />
            <Route path="/ledger/journals/:id" element={<JournalDetailPage />} />
          </Route>
        </Route>
      </Route>
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}






