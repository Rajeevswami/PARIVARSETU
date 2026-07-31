import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { api } from "@/api/axios";

export function DashboardPage() {
  const { data, isLoading } = useQuery({ queryKey: ["dashboard"], queryFn: () => api.get("/dashboard/").then(r => r.data.data) });
  if (isLoading) return <div className="p-8">Loading dashboard…</div>;
  const kpis = data?.kpis ?? {};
  return <div className="mx-auto max-w-6xl space-y-6 p-6"><div className="flex items-center justify-between"><div><h1 className="text-2xl font-semibold">Financial dashboard</h1><p className="text-sm text-muted-foreground">Live family financial summary</p></div><div className="flex gap-2"><Link className="rounded-md border px-3 py-2 text-sm" to="/analytics">Analytics</Link><Link className="rounded-md border px-3 py-2 text-sm" to="/reports">Reports</Link></div></div><div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">{Object.entries(kpis).slice(0,8).map(([name, value]) => <div key={name} className="rounded-lg border bg-card p-4"><p className="text-sm capitalize text-muted-foreground">{name.replaceAll("_", " ")}</p><p className="mt-2 text-xl font-semibold">{String(value)}</p></div>)}</div><div className="grid gap-6 md:grid-cols-2"><Recent title="Recent expenses" rows={data?.recent?.expenses} /><Recent title="Recent loans" rows={data?.recent?.loans} /></div></div>;
}
function Recent({title, rows}: {title: string, rows?: Record<string, unknown>[]}) { return <section className="rounded-lg border p-4"><h2 className="font-medium">{title}</h2><div className="mt-3 space-y-2 text-sm">{rows?.length ? rows.map((r,i)=><div key={i} className="flex justify-between border-b pb-2"><span>{String(r.title ?? r.expense_number ?? r.loan_number)}</span><span>{String(r.amount ?? r.remaining_amount)}</span></div>) : <p className="text-muted-foreground">No records yet.</p>}</div></section> }
