import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";
import { motion, AnimatePresence } from "motion/react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {
  UploadCloud, Send, Paperclip, Sparkles, Brain, FileText,
  Copy, RefreshCcw, ThumbsUp, ThumbsDown, Check, ShieldAlert,
} from "lucide-react";
import {
  KIND_META, getThread, upsertThread, newId,
  type ChatMessage, type ChatThread, type Kind,
} from "@/lib/chat-storage";
import { generateAnalysis, generateReply, generateTitle } from "@/lib/mock-ai";

export const Route = createFileRoute("/chat/$kind/$threadId")({
  component: ChatThreadPage,
});

const SUGGESTIONS = [
  "What are the abnormal findings?",
  "Explain all medical terms",
  "Summarize this report",
  "Should I consult a doctor?",
];

function ChatThreadPage() {
  const { kind, threadId } = Route.useParams();
  const navigate = useNavigate();
  const k = kind as Kind;
  const meta = KIND_META[k];

  const [thread, setThread] = useState<ChatThread | null>(null);
  const [input, setInput] = useState("");
  const [dragging, setDragging] = useState(false);
  const [pendingId, setPendingId] = useState<string | null>(null); // assistant msg being streamed
  const [copied, setCopied] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<Record<string, "up" | "down">>({});
  const scrollRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const streamTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const [hydrated, setHydrated] = useState(false);

  useEffect(() => setHydrated(true), []);

  useEffect(() => {
    if (!hydrated) return;
    const t = getThread(k, threadId);
    if (!t) {
      navigate({ to: "/chat/$kind", params: { kind: k }, replace: true });
      return;
    }
    setThread(t);
    setPendingId(null);
    if (streamTimerRef.current) clearInterval(streamTimerRef.current);
  }, [k, threadId, hydrated, navigate]);

  // auto-scroll
  useLayoutEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [thread?.messages.length, pendingId, thread?.messages[thread.messages.length - 1]?.content.length]);

  const persist = useCallback((next: ChatThread) => {
    setThread(next);
    upsertThread(k, next);
  }, [k]);

  const streamAssistant = useCallback((base: ChatThread, fullText: string) => {
    const asstId = newId();
    const assistantMsg: ChatMessage = { id: asstId, role: "assistant", content: "", createdAt: Date.now() };
    const withMsg: ChatThread = {
      ...base,
      messages: [...base.messages, assistantMsg],
      updatedAt: Date.now(),
    };
    persist(withMsg);
    setPendingId(asstId);

    if (streamTimerRef.current) clearInterval(streamTimerRef.current);
    const words = fullText.split(/(\s+)/);
    let i = 0;
    let acc = "";
    streamTimerRef.current = setInterval(() => {
      // stream a few words at a time
      const chunk = words.slice(i, i + 3).join("");
      acc += chunk;
      i += 3;
      setThread((prev) => {
        if (!prev) return prev;
        const msgs = prev.messages.map((m) => (m.id === asstId ? { ...m, content: acc } : m));
        return { ...prev, messages: msgs };
      });
      if (i >= words.length) {
        if (streamTimerRef.current) clearInterval(streamTimerRef.current);
        // final persist with full text
        setThread((prev) => {
          if (!prev) return prev;
          const msgs = prev.messages.map((m) => (m.id === asstId ? { ...m, content: fullText } : m));
          const final = { ...prev, messages: msgs, updatedAt: Date.now() };
          upsertThread(k, final);
          return final;
        });
        setPendingId(null);
      }
    }, 40);
  }, [persist, k]);

  const handleFile = (file: File) => {
    if (!thread) return;
    // TODO: replace with `POST /upload` — send file to backend.
    const fileMsg: ChatMessage = {
      id: newId(),
      role: "user",
      content: `Uploaded: ${file.name}`,
      variant: "file",
      fileName: file.name,
      fileSize: file.size,
      createdAt: Date.now(),
    };
    const title = thread.messages.length === 0 ? generateTitle(k, file.name) : thread.title;
    const next: ChatThread = {
      ...thread,
      title,
      fileName: file.name,
      messages: [...thread.messages, fileMsg],
      updatedAt: Date.now(),
    };
    persist(next);

    // Auto AI analysis after "upload"
    setTimeout(() => {
      const analysis = generateAnalysis(k, file.name);
      streamAssistant(next, analysis);
    }, 500);
  };

  const sendText = (text: string) => {
    if (!thread || !text.trim() || pendingId) return;
    // TODO: replace with `POST /chat` — send { threadId, message, history } to backend.
    const userMsg: ChatMessage = {
      id: newId(),
      role: "user",
      content: text.trim(),
      createdAt: Date.now(),
    };
    const title = thread.messages.length === 0 && !thread.fileName
      ? generateTitle(k, undefined, text.trim())
      : thread.title;
    const next: ChatThread = {
      ...thread,
      title,
      messages: [...thread.messages, userMsg],
      updatedAt: Date.now(),
    };
    persist(next);
    setInput("");

    setTimeout(() => {
      const reply = generateReply(k, text.trim(), next.messages, next.fileName);
      streamAssistant(next, reply);
    }, 350);
  };

  const regenerate = (asstMessageId: string) => {
    if (!thread || pendingId) return;
    const idx = thread.messages.findIndex((m) => m.id === asstMessageId);
    if (idx === -1) return;
    const prevUser = [...thread.messages].slice(0, idx).reverse().find((m) => m.role === "user");
    const trimmed = { ...thread, messages: thread.messages.slice(0, idx) };
    persist(trimmed);
    setTimeout(() => {
      let text: string;
      if (prevUser?.variant === "file" && prevUser.fileName) {
        text = generateAnalysis(k, prevUser.fileName);
      } else {
        text = generateReply(k, prevUser?.content ?? "", trimmed.messages, trimmed.fileName);
      }
      streamAssistant(trimmed, text);
    }, 200);
  };

  const copy = async (id: string, content: string) => {
    try { await navigator.clipboard.writeText(content); setCopied(id); setTimeout(() => setCopied(null), 1500); } catch {}
  };

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault(); setDragging(false);
    const f = e.dataTransfer.files?.[0];
    if (f) handleFile(f);
  };

  const isEmpty = (thread?.messages.length ?? 0) === 0;
  const showSuggestions = useMemo(() => {
    if (!thread || pendingId) return false;
    const hasAsst = thread.messages.some((m) => m.role === "assistant");
    return hasAsst;
  }, [thread, pendingId]);

  if (!hydrated || !thread) {
    return (
      <div className="glass grid min-h-[calc(100vh-9rem)] place-items-center rounded-3xl">
        <div className="text-sm text-muted-foreground">Loading chat...</div>
      </div>
    );
  }

  return (
    <div className="glass flex min-h-[calc(100vh-9rem)] flex-col rounded-3xl">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-border/70 px-6 py-4">
        <div className="min-w-0">
          <div className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">{meta.label}</div>
          <div className="truncate text-base font-semibold">{thread.title}</div>
        </div>
        {thread.fileName && (
          <div className="hidden items-center gap-2 rounded-xl bg-primary/10 px-3 py-1.5 text-xs text-primary md:flex">
            <FileText className="h-3.5 w-3.5" /> {thread.fileName}
          </div>
        )}
      </div>

      {/* Messages */}
      <div
        ref={scrollRef}
        onDragOver={(e) => { if (isEmpty) { e.preventDefault(); setDragging(true); } }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        className="relative flex-1 space-y-6 overflow-y-auto px-4 py-6 md:px-8"
      >
        {isEmpty ? (
          <EmptyDropzone dragging={dragging} onFile={handleFile} welcome={meta.welcome} />
        ) : (
          thread.messages.map((m) => (
            <MessageBubble
              key={m.id}
              message={m}
              streaming={pendingId === m.id}
              onCopy={() => copy(m.id, m.content)}
              copied={copied === m.id}
              onRegenerate={() => regenerate(m.id)}
              feedback={feedback[m.id]}
              onFeedback={(v) => setFeedback((f) => ({ ...f, [m.id]: v }))}
            />
          ))
        )}
        {pendingId && thread.messages.find((m) => m.id === pendingId)?.content === "" && <TypingIndicator />}

        {isEmpty && (
          <div className="mt-6 flex items-start gap-2 rounded-xl border border-amber-200 bg-amber-50 p-3 text-xs text-amber-800">
            <ShieldAlert className="mt-0.5 h-3.5 w-3.5 shrink-0" />
            <p>AI explanations are for education only and do not replace professional medical advice.</p>
          </div>
        )}
      </div>

      {/* Suggested chips */}
      <AnimatePresence>
        {showSuggestions && (
          <motion.div
            initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
            className="flex flex-wrap gap-2 px-4 pb-2 md:px-8"
          >
            {SUGGESTIONS.map((s) => (
              <button
                key={s}
                onClick={() => sendText(s)}
                className="rounded-full border border-border bg-white/70 px-3 py-1.5 text-xs text-foreground/80 transition hover:bg-white hover:text-primary"
              >
                {s}
              </button>
            ))}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Composer */}
      <Composer
        value={input}
        onChange={setInput}
        onSubmit={() => sendText(input)}
        onFile={handleFile}
        placeholder={meta.placeholder}
        disabled={!!pendingId}
        textareaRef={textareaRef}
      />
    </div>
  );
}

function MessageBubble({
  message, streaming, onCopy, copied, onRegenerate, feedback, onFeedback,
}: {
  message: ChatMessage;
  streaming: boolean;
  onCopy: () => void;
  copied: boolean;
  onRegenerate: () => void;
  feedback?: "up" | "down";
  onFeedback: (v: "up" | "down") => void;
}) {
  const isUser = message.role === "user";
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
      className={`flex gap-3 ${isUser ? "justify-end" : "justify-start"}`}
    >
      {!isUser && (
        <div className="grid h-8 w-8 shrink-0 place-items-center rounded-xl gradient-medical text-white shadow-lg shadow-primary/25">
          <Brain className="h-4 w-4" />
        </div>
      )}
      <div className={`max-w-[min(720px,85%)] ${isUser ? "order-2" : ""}`}>
        {isUser ? (
          message.variant === "file" ? (
            <div className="rounded-2xl bg-primary px-4 py-3 text-primary-foreground">
              <div className="mb-1 text-[10px] font-semibold uppercase tracking-wider opacity-80">Uploaded</div>
              <div className="flex items-center gap-2">
                <FileText className="h-4 w-4" />
                <div className="min-w-0">
                  <div className="truncate text-sm font-medium">{message.fileName}</div>
                  {message.fileSize != null && (
                    <div className="text-[11px] opacity-80">{(message.fileSize / 1024).toFixed(1)} KB</div>
                  )}
                </div>
              </div>
            </div>
          ) : (
            <div className="rounded-2xl bg-primary px-4 py-2.5 text-sm text-primary-foreground">
              {message.content}
            </div>
          )
        ) : (
          <>
            <div className="rounded-2xl bg-white/70 px-5 py-4 text-sm leading-relaxed text-foreground shadow-sm">
              <div className="prose prose-sm max-w-none prose-headings:mt-4 prose-headings:mb-2 prose-headings:font-semibold prose-p:my-2 prose-ul:my-2 prose-ol:my-2 prose-li:my-0.5 prose-table:my-3 prose-th:bg-muted/60 prose-th:px-3 prose-th:py-2 prose-td:px-3 prose-td:py-2 prose-th:text-left prose-td:border-t prose-td:border-border prose-strong:text-foreground prose-headings:text-foreground">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {message.content || "\u200b"}
                </ReactMarkdown>
              </div>
              {streaming && <span className="ml-0.5 inline-block h-4 w-1.5 animate-pulse rounded-sm bg-primary align-middle" />}
            </div>
            {!streaming && message.content && (
              <div className="mt-2 flex items-center gap-1 pl-1">
                <ActionButton onClick={onCopy} label={copied ? "Copied" : "Copy"}>
                  {copied ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
                </ActionButton>
                <ActionButton onClick={onRegenerate} label="Regenerate">
                  <RefreshCcw className="h-3.5 w-3.5" />
                </ActionButton>
                <ActionButton onClick={() => onFeedback("up")} label="Like" active={feedback === "up"}>
                  <ThumbsUp className="h-3.5 w-3.5" />
                </ActionButton>
                <ActionButton onClick={() => onFeedback("down")} label="Dislike" active={feedback === "down"}>
                  <ThumbsDown className="h-3.5 w-3.5" />
                </ActionButton>
              </div>
            )}
          </>
        )}
      </div>
    </motion.div>
  );
}

function ActionButton({ children, onClick, label, active }: { children: React.ReactNode; onClick: () => void; label: string; active?: boolean }) {
  return (
    <button
      onClick={onClick}
      title={label}
      className={`inline-flex items-center gap-1 rounded-md px-2 py-1 text-[11px] transition ${
        active ? "bg-primary/10 text-primary" : "text-muted-foreground hover:bg-white hover:text-foreground"
      }`}
    >
      {children}
    </button>
  );
}

function TypingIndicator() {
  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex gap-3">
      <div className="grid h-8 w-8 place-items-center rounded-xl gradient-medical text-white">
        <Brain className="h-4 w-4" />
      </div>
      <div className="flex items-center gap-2 rounded-2xl bg-white/70 px-4 py-3 shadow-sm">
        <div className="flex gap-1">
          {[0, 1, 2].map((i) => (
            <motion.span
              key={i}
              className="h-1.5 w-1.5 rounded-full bg-primary"
              animate={{ opacity: [0.3, 1, 0.3], y: [0, -2, 0] }}
              transition={{ duration: 1, repeat: Infinity, delay: i * 0.15 }}
            />
          ))}
        </div>
        <span className="text-xs text-muted-foreground">AI is analyzing your report...</span>
      </div>
    </motion.div>
  );
}

function EmptyDropzone({ dragging, onFile, welcome }: { dragging: boolean; onFile: (f: File) => void; welcome: string }) {
  const inputRef = useRef<HTMLInputElement>(null);
  return (
    <div className="flex min-h-full flex-col items-center justify-center gap-6 py-10 text-center">
      <div className="flex items-center gap-3">
        <div className="grid h-11 w-11 place-items-center rounded-2xl gradient-medical text-white shadow-lg shadow-primary/25">
          <Sparkles className="h-5 w-5" />
        </div>
      </div>
      <div className="max-w-lg">
        <h2 className="text-2xl font-semibold tracking-tight">How can I help?</h2>
        <p className="mt-1.5 text-sm text-muted-foreground">{welcome}</p>
      </div>
      <label
        className={`w-full max-w-lg cursor-pointer rounded-2xl border-2 border-dashed p-8 transition ${
          dragging ? "border-primary bg-primary/5" : "border-border bg-white/60 hover:bg-white"
        }`}
      >
        <input
          ref={inputRef} type="file" accept=".pdf,.jpg,.jpeg,.png" className="sr-only"
          onChange={(e) => e.target.files?.[0] && onFile(e.target.files[0])}
        />
        <div className="flex flex-col items-center gap-2">
          <UploadCloud className="h-8 w-8 text-primary" />
          <div className="text-sm font-medium">Drop your report here</div>
          <div className="text-xs text-muted-foreground">PDF, JPG or PNG · we'll analyze it automatically</div>
        </div>
      </label>
    </div>
  );
}

function Composer({
  value, onChange, onSubmit, onFile, placeholder, disabled, textareaRef,
}: {
  value: string; onChange: (v: string) => void; onSubmit: () => void;
  onFile: (f: File) => void; placeholder: string; disabled: boolean;
  textareaRef: React.RefObject<HTMLTextAreaElement | null>;
}) {
  const fileRef = useRef<HTMLInputElement>(null);

  // Focus on mount + when re-enabled
  useEffect(() => {
    if (!disabled) textareaRef.current?.focus();
  }, [disabled, textareaRef]);

  // auto-grow
  useLayoutEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 200) + "px";
  }, [value, textareaRef]);

  return (
    <div className="border-t border-border/70 px-4 py-4 md:px-8">
      <div className="relative flex items-end gap-2 rounded-2xl border border-border bg-white/80 p-2 shadow-sm transition focus-within:border-primary/40 focus-within:bg-white">
        <input
          ref={fileRef} type="file" accept=".pdf,.jpg,.jpeg,.png" className="sr-only"
          onChange={(e) => { const f = e.target.files?.[0]; if (f) onFile(f); if (fileRef.current) fileRef.current.value = ""; }}
        />
        <button
          type="button"
          onClick={() => fileRef.current?.click()}
          title="Attach file"
          className="grid h-9 w-9 shrink-0 place-items-center rounded-xl text-muted-foreground transition hover:bg-muted hover:text-foreground"
        >
          <Paperclip className="h-4 w-4" />
        </button>
        <textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              onSubmit();
            }
          }}
          rows={1}
          placeholder={placeholder}
          className="min-h-[36px] max-h-[200px] flex-1 resize-none bg-transparent px-2 py-2 text-sm outline-none placeholder:text-muted-foreground"
        />
        <button
          onClick={onSubmit}
          disabled={disabled || !value.trim()}
          className="grid h-9 w-9 shrink-0 place-items-center rounded-xl gradient-medical text-white shadow-md shadow-primary/25 transition hover:opacity-95 disabled:opacity-40"
          title="Send"
        >
          <Send className="h-4 w-4" />
        </button>
      </div>
      <div className="mt-2 text-center text-[10px] text-muted-foreground">
        Enter to send · Shift+Enter for new line · AI can make mistakes, verify medical info with a professional.
      </div>
    </div>
  );
}
