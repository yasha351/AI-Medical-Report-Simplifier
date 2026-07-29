import { Link, useNavigate, useRouterState } from "@tanstack/react-router";
import { useEffect, useMemo, useRef, useState } from "react";
import { motion, AnimatePresence } from "motion/react";
import {
  Plus, Search, MoreHorizontal, Pencil, Trash2, MessageSquare,
  ScanSearch, FlaskConical, Pill, X, Check,
} from "lucide-react";
import {
  KIND_META, createThread, deleteThread, groupByDate, loadThreads,
  renameThread, upsertThread, type ChatThread, type Kind,
} from "@/lib/chat-storage";

const KIND_ICON = { scan: ScanSearch, lab: FlaskConical, prescription: Pill } as const;

export function ChatSidebar({ kind, activeThreadId }: { kind: Kind; activeThreadId?: string }) {
  const navigate = useNavigate();
  const [threads, setThreads] = useState<ChatThread[]>([]);
  const [query, setQuery] = useState("");
  const [menuId, setMenuId] = useState<string | null>(null);
  const [renamingId, setRenamingId] = useState<string | null>(null);
  const [renameValue, setRenameValue] = useState("");

  const routerPath = useRouterState({ select: (s) => s.location.pathname });

  useEffect(() => {
    setThreads(loadThreads(kind).sort((a, b) => b.updatedAt - a.updatedAt));
  }, [kind, routerPath]);

  useEffect(() => {
    const onUpdate = (e: Event) => {
      const detail = (e as CustomEvent).detail;
      if (detail === kind || detail === undefined) {
        setThreads(loadThreads(kind).sort((a, b) => b.updatedAt - a.updatedAt));
      }
    };
    const onStorage = () => setThreads(loadThreads(kind).sort((a, b) => b.updatedAt - a.updatedAt));
    window.addEventListener("medsimplify:chats-updated", onUpdate);
    window.addEventListener("storage", onStorage);
    return () => {
      window.removeEventListener("medsimplify:chats-updated", onUpdate);
      window.removeEventListener("storage", onStorage);
    };
  }, [kind]);

  const meta = KIND_META[kind];
  const Icon = KIND_ICON[kind];

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return threads;
    return threads.filter((t) => t.title.toLowerCase().includes(q));
  }, [threads, query]);

  const grouped = groupByDate(filtered);

  const startNewChat = () => {
    const t = createThread(kind);
    upsertThread(kind, t);
    navigate({ to: "/chat/$kind/$threadId", params: { kind, threadId: t.id } });
  };

  const commitRename = (id: string) => {
    const value = renameValue.trim();
    if (value) renameThread(kind, id, value);
    setRenamingId(null);
    setMenuId(null);
  };

  const removeThread = (id: string) => {
    deleteThread(kind, id);
    setMenuId(null);
    if (activeThreadId === id) {
      const rest = loadThreads(kind);
      if (rest.length) navigate({ to: "/chat/$kind/$threadId", params: { kind, threadId: rest[0].id } });
      else navigate({ to: "/chat/$kind", params: { kind } });
    }
  };

  return (
    <aside className="glass sticky top-24 flex h-[calc(100vh-7rem)] w-72 shrink-0 flex-col overflow-hidden rounded-3xl p-4">
      <div className="mb-3 flex items-center gap-2">
        <div className="grid h-9 w-9 place-items-center rounded-xl gradient-medical text-white shadow-lg shadow-primary/25">
          <Icon className="h-4 w-4" />
        </div>
        <div>
          <div className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">{meta.short} Chats</div>
          <div className="text-sm font-semibold">{meta.label}</div>
        </div>
      </div>

      <button
        onClick={startNewChat}
        className="mb-3 inline-flex items-center justify-center gap-2 rounded-xl gradient-medical px-3 py-2.5 text-sm font-medium text-white shadow-lg shadow-primary/25 transition hover:opacity-95"
      >
        <Plus className="h-4 w-4" /> New Chat
      </button>

      <div className="relative mb-3">
        <Search className="pointer-events-none absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" />
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search chats"
          className="w-full rounded-xl border border-border bg-white/70 py-2 pl-8 pr-3 text-sm outline-none transition placeholder:text-muted-foreground focus:border-primary/40 focus:bg-white"
        />
      </div>

      <div className="-mx-1 flex-1 space-y-4 overflow-y-auto px-1">
        {grouped.length === 0 && (
          <div className="rounded-xl border border-dashed border-border p-4 text-center text-xs text-muted-foreground">
            No chats yet. Start a new one.
          </div>
        )}
        {grouped.map((g) => (
          <div key={g.label}>
            <div className="mb-1.5 px-2 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
              {g.label}
            </div>
            <div className="space-y-0.5">
              {g.items.map((t) => {
                const active = t.id === activeThreadId;
                const isRenaming = renamingId === t.id;
                return (
                  <div key={t.id} className="group relative">
                    {isRenaming ? (
                      <div className="flex items-center gap-1 rounded-lg bg-white px-2 py-1.5">
                        <input
                          autoFocus
                          value={renameValue}
                          onChange={(e) => setRenameValue(e.target.value)}
                          onKeyDown={(e) => {
                            if (e.key === "Enter") commitRename(t.id);
                            if (e.key === "Escape") setRenamingId(null);
                          }}
                          className="min-w-0 flex-1 bg-transparent text-sm outline-none"
                        />
                        <button onClick={() => commitRename(t.id)} className="rounded p-1 text-primary hover:bg-primary/10">
                          <Check className="h-3.5 w-3.5" />
                        </button>
                        <button onClick={() => setRenamingId(null)} className="rounded p-1 text-muted-foreground hover:bg-muted">
                          <X className="h-3.5 w-3.5" />
                        </button>
                      </div>
                    ) : (
                      <Link
                        to="/chat/$kind/$threadId"
                        params={{ kind, threadId: t.id }}
                        className={`flex items-center gap-2 rounded-lg px-2 py-2 text-sm transition ${
                          active ? "bg-primary/10 text-primary" : "text-foreground/80 hover:bg-white/70"
                        }`}
                      >
                        <MessageSquare className={`h-3.5 w-3.5 shrink-0 ${active ? "text-primary" : "text-muted-foreground"}`} />
                        <span className="truncate">{t.title}</span>
                      </Link>
                    )}

                    {!isRenaming && (
                      <button
                        onClick={(e) => { e.preventDefault(); e.stopPropagation(); setMenuId(menuId === t.id ? null : t.id); }}
                        className={`absolute right-1 top-1/2 -translate-y-1/2 rounded-md p-1 text-muted-foreground transition ${
                          menuId === t.id ? "bg-white opacity-100" : "opacity-0 group-hover:opacity-100 hover:bg-white"
                        }`}
                      >
                        <MoreHorizontal className="h-3.5 w-3.5" />
                      </button>
                    )}

                    <AnimatePresence>
                      {menuId === t.id && !isRenaming && (
                        <motion.div
                          initial={{ opacity: 0, y: -4 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -4 }}
                          className="absolute right-1 top-full z-10 mt-1 w-36 overflow-hidden rounded-lg border border-border bg-white shadow-xl"
                        >
                          <button
                            onClick={() => { setRenameValue(t.title); setRenamingId(t.id); setMenuId(null); }}
                            className="flex w-full items-center gap-2 px-3 py-2 text-left text-xs hover:bg-muted"
                          >
                            <Pencil className="h-3.5 w-3.5" /> Rename
                          </button>
                          <button
                            onClick={() => removeThread(t.id)}
                            className="flex w-full items-center gap-2 px-3 py-2 text-left text-xs text-red-600 hover:bg-red-50"
                          >
                            <Trash2 className="h-3.5 w-3.5" /> Delete
                          </button>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>
                );
              })}
            </div>
          </div>
        ))}
      </div>
    </aside>
  );
}

// Close menus on outside click helper
export function useClickOutside(ref: React.RefObject<HTMLElement | null>, handler: () => void) {
  useEffect(() => {
    const onClick = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) handler();
    };
    document.addEventListener("mousedown", onClick);
    return () => document.removeEventListener("mousedown", onClick);
  }, [ref, handler]);
}
