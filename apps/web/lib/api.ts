import { cookies } from "next/headers";

export type Incident = {
  id: string;
  title: string;
  description: string;
  severity: string;
  status: string;
  affected_customers: number;
  affected_units: number;
  verification_coverage: number;
  created_at: string;
};

export type Inventory = {
  id: string;
  product_id: string;
  manufacturing_batch_id: string;
  warehouse: string;
  quantity: number;
  status: string;
  version: number;
};

const API = process.env.REDTAG_API_URL || process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080/api/v1";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const store = await cookies();
  const tenant = store.get("redtag_tenant")?.value || process.env.REDTAG_DEFAULT_TENANT_ID || "tenant_demo";
  const token = store.get("redtag_id_token")?.value;
  const response = await fetch(`${API}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      "X-Tenant-ID": tenant,
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(init?.headers || {})
    },
    cache: "no-store"
  });
  if (!response.ok) {
    throw new Error(`${response.status} ${await response.text()}`);
  }
  return response.json() as Promise<T>;
}

export const api = {
  incidents: () => request<Incident[]>("/incidents"),
  incident: (id: string) => request<Incident>(`/incidents/${id}`),
  inventory: () => request<Inventory[]>("/inventory"),
  actions: (id: string) => request<any[]>(`/incidents/${id}/actions`),
  strategies: (id: string) => request<any[]>(`/incidents/${id}/strategies`),
  timeline: (id: string) => request<any[]>(`/incidents/${id}/timeline`),
  proof: (id: string) => request<any>(`/incidents/${id}/proof`),
  security: () => request<any[]>("/security/events"),
  returns: (incidentId: string) => request<any[]>(`/returns?incident_id=${encodeURIComponent(incidentId)}`),
  notifications: () => request<any[]>("/notifications"),
  shipments: () => request<any[]>("/shipments"),
  agents: () => request<any[]>("/agents"),
  approvals: () => request<any[]>("/approvals"),
  connectors: () => request<any[]>("/connectors"),
  policies: () => request<any>("/policies")
};
