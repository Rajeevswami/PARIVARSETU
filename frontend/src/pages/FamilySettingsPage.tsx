import { EditFamilyForm } from "@/features/families/components/EditFamilyForm";
import { useMyFamily } from "@/features/families/hooks/useFamilies";

export function FamilySettingsPage() {
  const { data: family, isLoading } = useMyFamily();

  if (isLoading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center text-muted-foreground">
        Loading…
      </div>
    );
  }
  if (!family) return null;

  return (
    <div className="mx-auto max-w-2xl space-y-8 px-4 py-10">
      <div>
        <h1 className="text-2xl font-semibold">{family.family_name}</h1>
        <p className="text-sm text-muted-foreground">
          {family.family_code} · {family.member_count} members · {family.household_count} households
        </p>
      </div>

      <EditFamilyForm family={family} />
    </div>
  );
}
