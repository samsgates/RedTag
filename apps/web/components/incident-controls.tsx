"use client";

import { useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { Bot, FileUp, Loader2, Play, ShieldCheck } from "lucide-react";

const API = "/api/redtag";

const commands = [
  ["Triage evidence", "triage"],
  ["Trace impact", "trace"],
  ["Simulate scope", "simulate"],
  ["Approve & contain", "approve-and-contain"],
  ["Notify customers", "notify"],
  ["Verify closure", "close"]
] as const;

export function IncidentControls({ incidentId }: { incidentId: string }) {
  const router = useRouter();
  const fileRef = useRef<HTMLInputElement>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [message, setMessage] = useState<string>("");

  async function run(command: string) {
    setBusy(command);
    setMessage("");
    try {
      const response = await fetch(`${API}/incidents/${incidentId}/${command}`, {
        method: "POST"
      });
      const body = await response.text();
      if (!response.ok) throw new Error(body);
      setMessage(`${command.replaceAll("-", " ")} completed`);
      router.refresh();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Command failed");
    } finally {
      setBusy(null);
    }
  }

  async function upload() {
    const file = fileRef.current?.files?.[0];
    if (!file) return;
    setBusy("upload");
    setMessage("");
    try {
      const form = new FormData();
      form.append("file", file);
      const response = await fetch(`${API}/incidents/${incidentId}/evidence`, {
        method: "POST",
        body: form
      });
      if (!response.ok) throw new Error(await response.text());
      setMessage(`Uploaded ${file.name}`);
      router.refresh();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Upload failed");
    } finally {
      setBusy(null);
    }
  }

  return (
    <section className="card panel commandPanel">
      <div className="panelHead">
        <div><span className="eyebrow">OPERATOR CONTROL</span><h2>Recall workflow</h2></div>
        <ShieldCheck size={20}/>
      </div>
      <div className="commandButtons">
        <button className="primaryAction" onClick={() => run("autopilot")} disabled={busy !== null}>
          {busy === "autopilot" ? <Loader2 size={15} className="spin"/> : <Bot size={15}/>} Run autonomous workflow
        </button>
        {commands.map(([label, command]) => (
          <button key={command} onClick={() => run(command)} disabled={busy !== null}>
            {busy === command ? <Loader2 size={15} className="spin"/> : <Play size={14}/>} {label}
          </button>
        ))}
      </div>
      <div className="uploadRow">
        <input ref={fileRef} type="file" aria-label="Evidence file"/>
        <button onClick={upload} disabled={busy !== null}><FileUp size={14}/> Upload evidence</button>
      </div>
      {message && <p className="commandMessage">{message}</p>}
    </section>
  );
}
