import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useEffect, useRef } from "react";
import { motion } from "motion/react";
import { Sparkles, MessageSquarePlus } from "lucide-react";
import { createThread, loadThreads, upsertThread, KIND_META, type Kind } from "@/lib/chat-storage";

export const Route = createFileRoute("/chat/$kind/")({
  component: ChatIndex,
});

function ChatIndex() {
  const { kind } = Route.useParams();
  const navigate = useNavigate();
  const k = kind as Kind;
  const meta = KIND_META[k];
  const bootstrapped = useRef(false);

  // Idempotent: if there are existing threads, jump to the most recent; otherwise show a start screen.
  useEffect(() => {
    if (bootstrapped.current) return;
    bootstrapped.current = true;
    if (typeof window === "undefined") return;
    const existing = loadThreads(k).sort((a, b) => b.updatedAt - a.updatedAt);
    if (existing.length > 0) {
      navigate({ to: "/chat/$kind/$threadId", params: { kind: k, threadId: existing[0].id }, replace: true });
    }
  }, [k, navigate]);

  const startNew = () => {
    const t = createThread(k);
    upsertThread(k, t);
    navigate({ to: "/chat/$kind/$threadId", params: { kind: k, threadId: t.id } });
  };

  return (
    <div className="glass flex min-h-[calc(100vh-9rem)] flex-col items-center justify-center rounded-3xl p-10 text-center">
      <motion.div
        initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
        className="grid h-16 w-16 place-items-center rounded-2xl gradient-medical text-white shadow-xl shadow-primary/25"
      >
        <Sparkles className="h-7 w-7" />
      </motion.div>
      <h1 className="mt-5 text-3xl font-semibold tracking-tight">
        Chat with AI about your <span className="text-gradient">{meta.label.toLowerCase()}</span>
      </h1>
      <p className="mt-2 max-w-md text-sm text-muted-foreground">{meta.welcome}</p>
      <button
        onClick={startNew}
        className="mt-6 inline-flex items-center gap-2 rounded-xl gradient-medical px-5 py-3 text-sm font-medium text-white shadow-lg shadow-primary/25 transition hover:opacity-95"
      >
        <MessageSquarePlus className="h-4 w-4" /> Start a new chat
      </button>
    </div>
  );
}
