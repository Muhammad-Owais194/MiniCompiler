const BASE = import.meta.env.VITE_API_URL || "/api";

async function post(path, body) {
  const r = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!r.ok) throw new Error(`HTTP ${r.status}: ${await r.text()}`);
  return r.json();
}

export const compile = (source_code) => post("/compile", { source_code });
export const run = (source_code, stdin = "") => post("/run", { source_code, stdin });
