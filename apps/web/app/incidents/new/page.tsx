import { NewIncidentForm } from "@/components/new-incident-form";
import { ensureAuth } from "@/lib/session";

export default async function NewIncidentPage() {
  await ensureAuth();
  return <>
    <header className="topbar"><div><p className="eyebrow">NEW SAFETY SIGNAL</p><h1>Create incident</h1><p>Start with the facts you have. Evidence can be uploaded after the incident is created.</p></div></header>
    <section className="card panel formCard"><NewIncidentForm/></section>
  </>;
}
