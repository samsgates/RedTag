"use client";

import { signOut } from "firebase/auth";
import { firebaseAuth } from "@/lib/firebase";

export function SignOut() {
  if ((process.env.NEXT_PUBLIC_AUTH_MODE || "dev") === "dev") return null;
  return <button className="signOut" onClick={async()=>{try{await signOut(firebaseAuth())}catch{} await fetch("/api/auth/session",{method:"DELETE"}); window.location.assign("/login");}}>Sign out</button>;
}
