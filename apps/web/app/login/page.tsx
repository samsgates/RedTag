"use client";

import { FormEvent, useState } from "react";
import { GoogleAuthProvider, signInWithEmailAndPassword, signInWithPopup } from "firebase/auth";
import { firebaseAuth } from "@/lib/firebase";

export default function LoginPage() {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [tenant, setTenant] = useState(process.env.NEXT_PUBLIC_TENANT_ID || "tenant_demo");

  async function establishSession(token: string) {
    const response = await fetch("/api/auth/session", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ token, tenant_id: tenant }) });
    if (!response.ok) throw new Error(await response.text());
    window.location.assign("/");
  }

  async function loginWithGoogle() {
    setBusy(true); setError("");
    try {
      const credential = await signInWithPopup(firebaseAuth(), new GoogleAuthProvider());
      await establishSession(await credential.user.getIdToken());
    } catch (e) { setError(e instanceof Error ? e.message : "Sign in failed"); setBusy(false); }
  }

  async function loginWithEmail(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setBusy(true); setError("");
    const form = new FormData(event.currentTarget);
    try {
      const credential = await signInWithEmailAndPassword(firebaseAuth(), String(form.get("email")), String(form.get("password")));
      await establishSession(await credential.user.getIdToken());
    } catch (e) { setError(e instanceof Error ? e.message : "Sign in failed"); setBusy(false); }
  }

  return <div className="loginWrap"><section className="card loginCard"><div className="brand loginBrand"><span className="brandMark">R</span><div><strong>RedTag</strong><small>Recall Command</small></div></div><p className="eyebrow">SECURE ENTERPRISE ACCESS</p><h1>Sign in</h1><p className="mutedText">Your organization membership and role are validated by the RedTag API before any data is returned.</p><label className="loginLabel">Organization tenant<input value={tenant} onChange={e=>setTenant(e.target.value)} required/></label><button className="primaryButton loginGoogle" disabled={busy} onClick={loginWithGoogle}>Continue with Google</button><div className="loginDivider"><span>or</span></div><form className="loginForm" onSubmit={loginWithEmail}><label>Email<input type="email" name="email" required autoComplete="email"/></label><label>Password<input type="password" name="password" required autoComplete="current-password"/></label>{error && <p className="formError">{error}</p>}<button className="tinyButton loginSubmit" disabled={busy}>{busy ? "Signing in..." : "Sign in with email"}</button></form></section></div>;
}
