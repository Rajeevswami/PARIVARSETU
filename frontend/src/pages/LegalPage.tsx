import { useQuery } from "@tanstack/react-query";
import { useParams } from "react-router-dom";

import { api } from "@/api/axios";

export function LegalPage() {
  const { document = "terms" } = useParams();
  const query = useQuery({
    queryKey: ["legal", document],
    queryFn: async () => {
      const response = await api.get(`/privacy/legal/${document}/`);
      return response.data.data as { body: string; version: string };
    },
  });

  return (
    <main id="main" className="mx-auto min-h-screen max-w-2xl px-6 py-16">
      <h1 className="text-2xl font-semibold capitalize">{document}</h1>
      {query.isLoading ? <p>Loading…</p> : null}
      {query.isError ? <p role="alert">The legal text could not be loaded.</p> : null}
      {query.data ? (
        <pre className="mt-6 whitespace-pre-wrap font-sans text-sm leading-6">
          {query.data.body}
        </pre>
      ) : null}
    </main>
  );
}
