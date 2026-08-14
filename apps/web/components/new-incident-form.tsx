"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

const API = "/api/redtag";

export function NewIncidentForm() {
  const router = useRouter();
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    setBusy(true);
    setError("");
    try {
      const response = await fetch(`${API}/incidents`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: form.get("title"),
          description: form.get("description"),
          severity: form.get("severity"),
          product_hint: form.get("product_hint") || null
        })
      });
      if (!response.ok) throw new Error(await response.text());
      const incident = await response.json();
      router.push(`/incidents/${incident.id}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unable to create incident");
    } finally {
      setBusy(false);
    }
  }

  return <form className="incidentForm" onSubmit={submit}>
    <label>Incident title<input name="title" required minLength={3} placeholder="X91 connector overheating"/></label>
    <label>Product hint<input name="product_hint" placeholder="K100 / K120"/></label>
    <label>Severity<select name="severity" defaultValue="HIGH"><option>LOW</option><option>MEDIUM</option><option>HIGH</option><option>CRITICAL</option></select></label>
    <label>Description<textarea name="description" rows={6} placeholder="Describe what was observed, where it came from, and any known supplier or batch references."/></label>
    {error && <p className="formError">{error}</p>}
    <button className="primaryButton" disabled={busy}>{busy ? "Creating..." : "Create incident"}</button>
  </form>;
}
