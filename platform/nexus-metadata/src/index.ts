/**
 * Domain API over D1 for Nexus artifact/run metadata.
 * Blobs stay on R2; this Worker only serves the index.
 * Auth: Authorization: Bearer <API_KEY> (wrangler secret).
 */
export interface Env {
  DB: D1Database;
  API_KEY: string;
}

const CATEGORIES = new Set([
  "pcaps",
  "sboms",
  "skills",
  "sessions",
  "images",
  "other",
]);

function json(data: unknown, status = 200): Response {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "content-type": "application/json; charset=utf-8" },
  });
}

function unauthorized(): Response {
  return json({ error: "unauthorized" }, 401);
}

function badRequest(msg: string): Response {
  return json({ error: msg }, 400);
}

function uuid(): string {
  return crypto.randomUUID();
}

async function requireAuth(request: Request, env: Env): Promise<Response | null> {
  const header = request.headers.get("authorization") || "";
  const match = /^Bearer\s+(.+)$/i.exec(header);
  if (!match || match[1] !== env.API_KEY) {
    return unauthorized();
  }
  return null;
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);
    const { pathname } = url;

    if (request.method === "GET" && pathname === "/healthz") {
      return json({ status: "ok", service: "nexus-metadata" });
    }

    const authErr = await requireAuth(request, env);
    if (authErr) return authErr;

    try {
      if (request.method === "GET" && pathname === "/v1/artifacts") {
        const category = url.searchParams.get("category");
        const limit = Math.min(Number(url.searchParams.get("limit") || "50"), 200);
        if (category && !CATEGORIES.has(category)) {
          return badRequest(`invalid category: ${category}`);
        }
        const stmt = category
          ? env.DB.prepare(
              "SELECT * FROM artifacts WHERE category = ? ORDER BY created_at DESC LIMIT ?",
            ).bind(category, limit)
          : env.DB.prepare(
              "SELECT * FROM artifacts ORDER BY created_at DESC LIMIT ?",
            ).bind(limit);
        const { results } = await stmt.all();
        return json(results ?? []);
      }

      if (request.method === "POST" && pathname === "/v1/artifacts") {
        const body = (await request.json()) as Record<string, unknown>;
        const objectKey = String(body.object_key || "").trim();
        const category = String(body.category || "").trim();
        if (!objectKey || !category) {
          return badRequest("object_key and category are required");
        }
        if (!CATEGORIES.has(category)) {
          return badRequest(`invalid category: ${category}`);
        }
        const id = String(body.id || uuid());
        await env.DB.prepare(
          `INSERT INTO artifacts (
             id, object_key, category, digest, media_type, size_bytes,
             source, image_ref, ssf_attestation_url, metadata_json
           ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
           ON CONFLICT(object_key) DO UPDATE SET
             category=excluded.category,
             digest=excluded.digest,
             media_type=excluded.media_type,
             size_bytes=excluded.size_bytes,
             source=excluded.source,
             image_ref=excluded.image_ref,
             ssf_attestation_url=excluded.ssf_attestation_url,
             metadata_json=excluded.metadata_json`,
        )
          .bind(
            id,
            objectKey,
            category,
            body.digest ?? null,
            body.media_type ?? null,
            body.size_bytes ?? null,
            body.source ?? "gateway",
            body.image_ref ?? null,
            body.ssf_attestation_url ?? null,
            body.metadata_json
              ? JSON.stringify(body.metadata_json)
              : null,
          )
          .run();
        const row = await env.DB.prepare(
          "SELECT * FROM artifacts WHERE object_key = ?",
        )
          .bind(objectKey)
          .first();
        return json(row, 201);
      }

      if (request.method === "GET" && pathname.startsWith("/v1/artifacts/")) {
        const id = pathname.slice("/v1/artifacts/".length);
        const row = await env.DB.prepare("SELECT * FROM artifacts WHERE id = ?")
          .bind(id)
          .first();
        if (!row) return json({ error: "not found" }, 404);
        return json(row);
      }

      if (request.method === "POST" && pathname === "/v1/runs") {
        const body = (await request.json()) as Record<string, unknown>;
        const kind = String(body.kind || "").trim();
        if (!kind) return badRequest("kind is required");
        const id = String(body.id || uuid());
        await env.DB.prepare(
          `INSERT INTO runs (id, kind, status, actor, summary, metadata_json)
           VALUES (?, ?, ?, ?, ?, ?)`,
        )
          .bind(
            id,
            kind,
            body.status ?? "pending",
            body.actor ?? null,
            body.summary ?? null,
            body.metadata_json ? JSON.stringify(body.metadata_json) : null,
          )
          .run();
        const row = await env.DB.prepare("SELECT * FROM runs WHERE id = ?")
          .bind(id)
          .first();
        return json(row, 201);
      }

      if (request.method === "GET" && pathname.startsWith("/v1/runs/")) {
        const id = pathname.slice("/v1/runs/".length);
        if (id.includes("/")) return json({ error: "not found" }, 404);
        const run = await env.DB.prepare("SELECT * FROM runs WHERE id = ?")
          .bind(id)
          .first();
        if (!run) return json({ error: "not found" }, 404);
        const { results: artifacts } = await env.DB.prepare(
          `SELECT a.* FROM artifacts a
           INNER JOIN run_artifacts ra ON ra.artifact_id = a.id
           WHERE ra.run_id = ?`,
        )
          .bind(id)
          .all();
        return json({ ...run, artifacts: artifacts ?? [] });
      }

      if (
        request.method === "POST" &&
        pathname.match(/^\/v1\/runs\/[^/]+\/artifacts$/)
      ) {
        const runId = pathname.split("/")[3];
        const body = (await request.json()) as Record<string, unknown>;
        const artifactId = String(body.artifact_id || "").trim();
        if (!artifactId) return badRequest("artifact_id is required");
        await env.DB.prepare(
          "INSERT OR IGNORE INTO run_artifacts (run_id, artifact_id) VALUES (?, ?)",
        )
          .bind(runId, artifactId)
          .run();
        return json({ run_id: runId, artifact_id: artifactId }, 201);
      }

      return json({ error: "not found" }, 404);
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      return json({ error: message }, 500);
    }
  },
};
