import { useNavigate } from "react-router-dom";

import type { Loan } from "@/types/loan";

export function LoanTable({ loans }: { loans: Loan[] }) {
  const navigate = useNavigate();

  return (
    <div className="overflow-x-auto rounded-lg border border-border">
      <table className="w-full text-sm">
        <thead className="border-b border-border bg-muted/50 text-left text-muted-foreground">
          <tr>
            <th className="px-3 py-2 font-medium">Number</th>
            <th className="px-3 py-2 font-medium">Title</th>
            <th className="px-3 py-2 font-medium">Borrower</th>
            <th className="px-3 py-2 text-right font-medium">Total</th>
            <th className="px-3 py-2 text-right font-medium">Remaining</th>
            <th className="px-3 py-2 font-medium">Status</th>
          </tr>
        </thead>
        <tbody>
          {loans.map((l) => (
            <tr
              key={l.id}
              onClick={() => navigate(`/loans/${l.id}`)}
              className="cursor-pointer border-b border-border last:border-0 hover:bg-accent"
            >
              <td className="px-3 py-2 text-muted-foreground">{l.loan_number}</td>
              <td className="px-3 py-2">{l.title}</td>
              <td className="px-3 py-2">{l.borrower_name}</td>
              <td className="px-3 py-2 text-right">{l.total_amount}</td>
              <td className="px-3 py-2 text-right">{l.remaining_amount}</td>
              <td className="px-3 py-2 capitalize">{l.status}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
