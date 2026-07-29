import { createFileRoute, Link, Outlet, useParams } from "@tanstack/react-router";
import { ArrowLeft } from "lucide-react";
import { Nav, ScrollProgress } from "@/components/site/shell";
import { ChatSidebar } from "@/components/site/chat-sidebar";
import { KIND_META, type Kind } from "@/lib/chat-storage";

const KINDS: Kind[] = ["scan", "lab", "prescription"];

export const Route = createFileRoute("/chat/$kind")({
  head: ({ params }) => {
    const label = KIND_META[(params.kind as Kind)]?.label ?? "Chat";
    return {
      meta: [
        { title: `${label} — MedSimplify AI` },
        { name: "description", content: `Chat with AI about your ${label.toLowerCase()}.` },
      ],
    };
  },
  component: ChatLayout,
});

function ChatLayout() {
  const { kind } = useParams({ strict: false }) as { kind?: string };
  const validKind = (KINDS.includes(kind as Kind) ? kind : "scan") as Kind;
  const routeParams = useParams({ strict: false }) as { threadId?: string };

  return (
    <div className="relative min-h-screen bg-background">
      <ScrollProgress />
      <Nav />
      <div className="mesh-bg min-h-screen pt-24">
        <div className="mx-auto max-w-7xl px-4 pb-2 md:px-6">
          <Link
            to="/"
            className="inline-flex items-center gap-1.5 rounded-xl px-3 py-2 text-sm font-medium text-muted-foreground transition hover:bg-white/60 hover:text-foreground"
          >
            <ArrowLeft className="h-4 w-4" /> Back to home
          </Link>
        </div>
        <div className="mx-auto flex max-w-7xl gap-6 px-4 pb-6 md:px-6">
          <ChatSidebar kind={validKind} activeThreadId={routeParams.threadId} />
          <main className="min-w-0 flex-1">
            <Outlet />
          </main>
        </div>
      </div>
    </div>
  );
}
