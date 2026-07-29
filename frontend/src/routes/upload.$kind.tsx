import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { motion, AnimatePresence } from "motion/react";
import { useCallback, useRef, useState } from "react";
import {
  UploadCloud, FileText, X, Sparkles, ScanLine, Brain, ArrowRight,
  ScanSearch, FlaskConical, Pill, ArrowLeft,
} from "lucide-react";
import { Nav, Footer, ScrollProgress, EyebrowChip } from "@/components/site/shell";

const KINDS = {
  scan: { title: "Scan Report", icon: ScanSearch, desc: "Upload MRI, CT, X-Ray or Ultrasound reports." },
  lab: { title: "Lab Report", icon: FlaskConical, desc: "Blood tests and lab work with abnormal values highlighted." },
  prescription: { title: "Prescription", icon: Pill, desc: "Get medicines, dosage and side effects explained." },
} as const;

type Kind = keyof typeof KINDS;

export const Route = createFileRoute("/upload/$kind")({
  head: ({ params }) => ({
    meta: [
      { title: `Analyze ${KINDS[(params.kind as Kind)]?.title ?? "Document"} — MedSimplify AI` },
      { name: "description", content: "Upload your medical document and get a simple, AI-generated explanation." },
    ],
  }),
  component: UploadPage,
});

function UploadPage() {
  const { kind } = Route.useParams();
  const navigate = useNavigate();
  const meta = KINDS[kind as Kind] ?? KINDS.scan;
  const Icon = meta.icon;

  const [file, setFile] = useState<File | null>(null);
  const [progress, setProgress] = useState(0);
  const [dragging, setDragging] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [analyzePhase, setAnalyzePhase] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFile = useCallback((f: File) => {
    setFile(f);
    setProgress(0);
    let p = 0;
    const id = setInterval(() => {
      p += 6 + Math.random() * 10;
      if (p >= 100) { p = 100; clearInterval(id); }
      setProgress(p);
    }, 90);
  }, []);

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault(); setDragging(false);
    const f = e.dataTransfer.files?.[0];
    if (f) handleFile(f);
  };

  const analyze = () => {
    setAnalyzing(true);
    setAnalyzePhase(0);
    const timers = [
      setTimeout(() => setAnalyzePhase(1), 900),
      setTimeout(() => setAnalyzePhase(2), 2000),
      setTimeout(() => setAnalyzePhase(3), 3200),
      setTimeout(() => navigate({ to: "/results/$kind", params: { kind } }), 4200),
    ];
    return () => timers.forEach(clearTimeout);
  };

  const preview = file && file.type.startsWith("image/") ? URL.createObjectURL(file) : null;

  return (
    <div className="relative min-h-screen bg-background">
      <ScrollProgress />
      <Nav />
      <div className="mesh-bg pt-32 pb-20">
        <div className="mx-auto max-w-4xl px-6">
          <Link to="/" className="inline-flex items-center gap-1.5 text-sm text-muted-foreground transition hover:text-foreground">
            <ArrowLeft className="h-4 w-4" /> Back to home
          </Link>

          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }} className="mt-6">
            <EyebrowChip>Upload · {meta.title}</EyebrowChip>
            <h1 className="mt-4 text-4xl font-semibold tracking-tight md:text-5xl">
              Analyze your <span className="text-gradient">{meta.title.toLowerCase()}</span>
            </h1>
            <p className="mt-3 max-w-2xl text-muted-foreground">{meta.desc}</p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15, duration: 0.6 }}
            className="mt-10"
          >
            {!file ? (
              <label
                onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
                onDragLeave={() => setDragging(false)}
                onDrop={onDrop}
                className={`relative flex min-h-[320px] cursor-pointer flex-col items-center justify-center rounded-3xl border-2 border-dashed p-10 text-center transition ${
                  dragging ? "border-primary bg-primary/5" : "border-border bg-white/60 hover:bg-white"
                }`}
              >
                <input
                  ref={inputRef} type="file" accept=".pdf,.jpg,.jpeg,.png" className="sr-only"
                  onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
                />
                <motion.div
                  animate={{ y: [0, -6, 0] }} transition={{ repeat: Infinity, duration: 3, ease: "easeInOut" }}
                  className="grid h-16 w-16 place-items-center rounded-2xl gradient-medical text-white shadow-xl shadow-primary/25"
                >
                  <UploadCloud className="h-7 w-7" />
                </motion.div>
                <div className="mt-5 text-lg font-semibold">Drop your file here</div>
                <div className="mt-1 text-sm text-muted-foreground">or click to browse · PDF, JPG, PNG</div>
                <div className="mt-6 inline-flex items-center gap-2 rounded-xl gradient-medical px-5 py-2.5 text-sm font-medium text-white">
                  <Icon className="h-4 w-4" /> Choose file
                </div>
              </label>
            ) : (
              <div className="glass rounded-3xl p-6">
                <div className="flex items-start gap-4">
                  <div className="grid h-14 w-14 shrink-0 place-items-center overflow-hidden rounded-2xl bg-primary/10 text-primary">
                    {preview ? <img src={preview} alt="preview" className="h-full w-full object-cover" /> : <FileText className="h-6 w-6" />}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-3">
                      <div className="truncate font-medium">{file.name}</div>
                      <button
                        onClick={() => { setFile(null); setProgress(0); }}
                        className="rounded-lg p-1.5 text-muted-foreground transition hover:bg-muted"
                      >
                        <X className="h-4 w-4" />
                      </button>
                    </div>
                    <div className="mt-1 text-xs text-muted-foreground">{(file.size / 1024).toFixed(1)} KB</div>
                    <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-muted">
                      <motion.div
                        className="h-full gradient-medical"
                        initial={{ width: 0 }} animate={{ width: `${progress}%` }} transition={{ ease: "easeOut" }}
                      />
                    </div>
                    <div className="mt-1 text-xs text-muted-foreground">{progress < 100 ? `Uploading ${Math.floor(progress)}%` : "Upload complete"}</div>
                  </div>
                </div>

                <div className="mt-6 flex flex-wrap items-center justify-end gap-3">
                  <button
                    onClick={() => { setFile(null); setProgress(0); }}
                    className="rounded-xl border border-border bg-white px-5 py-3 text-sm font-medium transition hover:bg-muted"
                  >
                    Change file
                  </button>
                  <button
                    onClick={analyze}
                    disabled={progress < 100 || analyzing}
                    className="inline-flex items-center gap-2 rounded-xl gradient-medical px-6 py-3 text-sm font-medium text-white shadow-lg shadow-primary/25 transition hover:opacity-95 disabled:opacity-50"
                  >
                    <Sparkles className="h-4 w-4" /> Analyze with AI <ArrowRight className="h-4 w-4" />
                  </button>
                </div>
              </div>
            )}
          </motion.div>
        </div>
      </div>

      <AnimatePresence>
        {analyzing && <AnalyzingOverlay phase={analyzePhase} />}
      </AnimatePresence>

      <Footer />
    </div>
  );
}

function AnalyzingOverlay({ phase }: { phase: number }) {
  const steps = [
    { icon: UploadCloud, label: "Preparing document" },
    { icon: ScanLine, label: "OCR scanning" },
    { icon: Brain, label: "AI understanding" },
    { icon: Sparkles, label: "Generating explanation" },
  ];
  return (
    <motion.div
      initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
      className="fixed inset-0 z-[70] grid place-items-center bg-background/80 backdrop-blur-md"
    >
      <div className="glass w-[min(440px,90vw)] rounded-3xl p-8">
        <div className="relative mx-auto grid h-24 w-24 place-items-center">
          <motion.div
            className="absolute inset-0 rounded-full"
            style={{ background: "conic-gradient(from 0deg, oklch(0.55 0.22 265), oklch(0.72 0.14 190), oklch(0.55 0.22 265))" }}
            animate={{ rotate: 360 }} transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
          />
          <div className="relative grid h-20 w-20 place-items-center rounded-full bg-background">
            <Brain className="h-8 w-8 text-primary" />
          </div>
        </div>
        <div className="mt-6 space-y-2">
          {steps.map((s, i) => (
            <div key={s.label} className={`flex items-center gap-3 rounded-xl px-3 py-2 transition ${phase >= i ? "bg-primary/5" : "opacity-40"}`}>
              <div className={`grid h-8 w-8 place-items-center rounded-lg ${phase >= i ? "gradient-medical text-white" : "bg-muted text-muted-foreground"}`}>
                <s.icon className="h-4 w-4" />
              </div>
              <div className="text-sm font-medium">{s.label}</div>
              {phase === i && (
                <motion.div className="ml-auto h-1.5 w-1.5 rounded-full bg-primary" animate={{ opacity: [0.3, 1, 0.3] }} transition={{ duration: 1, repeat: Infinity }} />
              )}
            </div>
          ))}
        </div>
      </div>
    </motion.div>
  );
}
