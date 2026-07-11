// Real-time file-backed persistence for the frontend UI state.
//
// The app historically relied ONLY on browser localStorage, which is tied to a
// specific browser + origin (localhost:PORT) and gets wiped whenever the user
// opens the app in a different browser/profile, uses incognito, or clears site
// data. This module mirrors the relevant localStorage keys to a JSON file on
// the server's disk, so the user's lyrics / settings survive those cases.
//
// Flow:
//   - hydrateFromServer(): on startup, pull the server file and write it into
//     localStorage BEFORE React mounts (so useState initializers read it).
//   - startAutoSync(): periodically mirror localStorage -> server file, plus on
//     tab hide / page unload.

const PERSIST_PREFIXES = ['ace-', 'acestep_'];
const PERSIST_EXACT = ['theme', 'volume'];

function isPersistedKey(key: string | null): key is string {
  if (!key) return false;
  if (PERSIST_EXACT.includes(key)) return true;
  return PERSIST_PREFIXES.some((p) => key.startsWith(p));
}

function collect(): Record<string, string> {
  const out: Record<string, string> = {};
  try {
    for (let i = 0; i < localStorage.length; i++) {
      const k = localStorage.key(i);
      if (isPersistedKey(k)) {
        out[k as string] = localStorage.getItem(k as string) || '';
      }
    }
  } catch {
    /* localStorage may be unavailable in some contexts */
  }
  return out;
}

function apply(state: Record<string, string>): void {
  if (!state || typeof state !== 'object') return;
  try {
    for (const [k, v] of Object.entries(state)) {
      localStorage.setItem(k, v);
    }
  } catch {
    /* ignore */
  }
}

let lastSignature = '';
let syncStarted = false;

async function push(): Promise<void> {
  const state = collect();
  const sig = JSON.stringify(state);
  if (sig === lastSignature) return; // nothing changed since last push
  lastSignature = sig;
  try {
    await fetch('/api/ui-state', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(state),
      credentials: 'include',
    });
  } catch {
    /* server temporarily unavailable — next interval will retry */
  }
}

/** Pull server-side state into localStorage. Call BEFORE React renders. */
export async function hydrateFromServer(): Promise<void> {
  try {
    const res = await fetch('/api/ui-state', { credentials: 'include' });
    if (!res.ok) return;
    const json = await res.json();
    const data = json && json.data;
    if (data && typeof data === 'object') {
      apply(data as Record<string, string>);
      lastSignature = JSON.stringify(collect());
    }
  } catch {
    /* offline / server not ready yet — fall back to existing localStorage */
  }
}

/** Begin mirroring localStorage -> server file. Safe to call once. */
export function startAutoSync(): void {
  if (syncStarted) return;
  syncStarted = true;

  // Immediate best-effort push (captures state right after mount).
  push();

  // Periodic mirror so the latest edits are flushed within ~1s.
  setInterval(() => {
    push();
  }, 1000);

  // Flush when the tab is hidden or the page is being unloaded.
  const flush = () => {
    push();
  };
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'hidden') flush();
  });
  window.addEventListener('pagehide', flush);
  window.addEventListener('beforeunload', flush);
}
