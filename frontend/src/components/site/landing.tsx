import { motion, useMotionValue, useSpring, useTransform, useScroll, useInView } from "motion/react";
import { Link } from "@tanstack/react-router";
import { useEffect, useRef, useState } from "react";
import {
  ArrowRight, Upload, ScanLine, Brain, Sparkles, FlaskConical, Pill,
  ScanSearch, ShieldCheck, Zap, Languages, FileText, Stethoscope,
  CheckCircle2, Quote, Activity, ChevronRight,
} from "lucide-react";
import { EyebrowChip, SectionShell } from "./shell";

/* ---------------- HERO ---------------- */
export function Hero() {
  const ref = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({ target: ref, offset: ["start start", "end start"] });
  const yText = useTransform(scrollYProgress, [0, 1], [0, -80]);
  const opacity = useTransform(scrollYProgress, [0, 0.8], [1, 0]);
  const scaleArt = useTransform(scrollYProgress, [0, 1], [1, 1.08]);

  // mouse follow
  const mx = useMotionValue(0);
  const my = useMotionValue(0);
  const rx = useSpring(useTransform(my, [-0.5, 0.5], [8, -8]), { stiffness: 120, damping: 15 });
  const ry = useSpring(useTransform(mx, [-0.5, 0.5], [-8, 8]), { stiffness: 120, damping: 15 });

  return (
    <div
      ref={ref}
      onMouseMove={(e) => {
        const r = e.currentTarget.getBoundingClientRect();
        mx.set((e.clientX - r.left) / r.width - 0.5);
        my.set((e.clientY - r.top) / r.height - 0.5);
      }}
      className="relative min-h-[100svh] overflow-hidden mesh-bg"
    >
      <FloatingParticles />
      <div className="pointer-events-none absolute inset-0">
        <FloatingIcon Icon={Stethoscope} className="left-[8%] top-[22%]" delay={0} />
        <FloatingIcon Icon={FlaskConical} className="right-[12%] top-[18%]" delay={0.6} />
        <FloatingIcon Icon={Pill} className="left-[14%] bottom-[18%]" delay={1.2} />
        <FloatingIcon Icon={Activity} className="right-[8%] bottom-[24%]" delay={1.8} />
      </div>

      <div className="relative mx-auto grid max-w-6xl grid-cols-1 items-center gap-12 px-6 pb-24 pt-40 md:grid-cols-2 md:pt-44">
        <motion.div style={{ y: yText, opacity }} className="relative z-10">
          <EyebrowChip>AI-powered medical understanding</EyebrowChip>
          <motion.h1
            initial="hidden" animate="show"
            variants={{ hidden: {}, show: { transition: { staggerChildren: 0.08 } } }}
            className="mt-5 text-5xl font-semibold leading-[1.05] tracking-tight md:text-6xl lg:text-7xl"
          >
            {["Understand", "your", "medical reports", "in seconds."].map((w, i) => (
              <motion.span
                key={i}
                variants={{ hidden: { opacity: 0, y: 24 }, show: { opacity: 1, y: 0 } }}
                transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
                className={`mr-3 inline-block ${i === 2 ? "text-gradient" : ""}`}
              >
                {w}
              </motion.span>
            ))}
          </motion.h1>
          <motion.p
            initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5, duration: 0.7 }}
            className="mt-6 max-w-xl text-lg text-muted-foreground"
          >
            Upload scan reports, lab reports, or prescriptions and let AI translate complex medical information into clear, simple language.
          </motion.p>
          <motion.div
            initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.7, duration: 0.7 }}
            className="mt-8 flex flex-wrap items-center gap-3"
          >
            <Link
              to="/chat/$kind" params={{ kind: "scan" }}
              className="group inline-flex items-center gap-2 rounded-2xl gradient-medical px-6 py-3.5 text-sm font-medium text-white shadow-xl shadow-primary/30 transition hover:shadow-2xl hover:shadow-primary/40"
            >
              Try it now
              <ArrowRight className="h-4 w-4 transition group-hover:translate-x-0.5" />
            </Link>

            <a
              href="#how"
              className="inline-flex items-center gap-2 rounded-2xl border border-border bg-white/70 px-6 py-3.5 text-sm font-medium backdrop-blur transition hover:bg-white"
            >
              Learn more
            </a>
          </motion.div>
        </motion.div>

        <motion.div style={{ scale: scaleArt, rotateX: rx, rotateY: ry, transformPerspective: 1200 }} className="relative">
          <HeroReportCard />
        </motion.div>
      </div>
    </div>
  );
}

function FloatingIcon({ Icon, className, delay }: { Icon: any; className: string; delay: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.8 }}
      animate={{ opacity: 0.6, scale: 1, y: [0, -12, 0] }}
      transition={{ opacity: { delay, duration: 1 }, scale: { delay, duration: 1 }, y: { repeat: Infinity, duration: 5, ease: "easeInOut", delay } }}
      className={`absolute ${className}`}
    >
      <div className="glass grid h-12 w-12 place-items-center rounded-2xl text-primary">
        <Icon className="h-5 w-5" />
      </div>
    </motion.div>
  );
}

function FloatingParticles() {
  const dots = Array.from({ length: 24 });
  return (
    <div className="pointer-events-none absolute inset-0 overflow-hidden">
      {dots.map((_, i) => {
        const size = 4 + (i % 5) * 3;
        const left = (i * 37) % 100;
        const top = (i * 53) % 100;
        const dur = 6 + (i % 6);
        return (
          <motion.span
            key={i}
            className="absolute rounded-full"
            style={{
              left: `${left}%`, top: `${top}%`, width: size, height: size,
              background: "radial-gradient(circle, oklch(0.72 0.14 190 / 0.7), transparent 70%)",
              filter: "blur(1px)",
            }}
            animate={{ y: [0, -30, 0], opacity: [0.3, 0.9, 0.3] }}
            transition={{ duration: dur, repeat: Infinity, ease: "easeInOut", delay: i * 0.15 }}
          />
        );
      })}
    </div>
  );
}

function HeroReportCard() {
  return (
    <div className="relative mx-auto w-full max-w-md">
      <motion.div
        animate={{ y: [0, -10, 0] }} transition={{ duration: 6, repeat: Infinity, ease: "easeInOut" }}
        className="glass relative rounded-3xl p-6"
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-xs font-medium text-muted-foreground">
            <FileText className="h-4 w-4 text-primary" /> Lab Report · #A-2481
          </div>
          <span className="rounded-full bg-teal/15 px-2 py-0.5 text-[10px] font-semibold text-teal">Analyzed</span>
        </div>
        <div className="mt-5 space-y-3">
          {[
            { k: "Hemoglobin", v: "11.2 g/dL", flag: "Low" },
            { k: "WBC Count", v: "6.8 K/µL", flag: "Normal" },
            { k: "Cholesterol", v: "232 mg/dL", flag: "High" },
            { k: "Glucose", v: "94 mg/dL", flag: "Normal" },
          ].map((r, i) => (
            <motion.div
              key={r.k}
              initial={{ opacity: 0, x: 10 }} animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.4 + i * 0.1 }}
              className="flex items-center justify-between rounded-xl bg-white/70 px-3 py-2.5"
            >
              <span className="text-sm text-muted-foreground">{r.k}</span>
              <span className="text-sm font-medium">{r.v}</span>
              <span className={`rounded-md px-2 py-0.5 text-[10px] font-semibold ${
                r.flag === "Normal" ? "bg-muted text-muted-foreground" :
                r.flag === "Low" ? "bg-amber-100 text-amber-700" : "bg-red-100 text-red-700"
              }`}>{r.flag}</span>
            </motion.div>
          ))}
        </div>
        <motion.div
          initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 1 }}
          className="mt-5 rounded-2xl bg-gradient-to-br from-primary/10 to-teal/10 p-4"
        >
          <div className="flex items-center gap-2 text-xs font-semibold text-primary">
            <Sparkles className="h-3.5 w-3.5" /> AI Summary
          </div>
          <p className="mt-2 text-sm leading-relaxed text-foreground/80">
            Your report shows mild anemia and elevated cholesterol. Consider iron-rich foods and a follow-up with your physician.
          </p>
        </motion.div>
      </motion.div>

      <motion.div
        animate={{ y: [0, 10, 0] }} transition={{ duration: 5, repeat: Infinity, ease: "easeInOut", delay: 1 }}
        className="glass absolute -bottom-6 -left-6 flex items-center gap-2 rounded-2xl px-4 py-3"
      >
        <div className="grid h-8 w-8 place-items-center rounded-lg gradient-medical text-white">
          <Brain className="h-4 w-4" />
        </div>
        <div className="text-xs">
          <div className="font-semibold">AI Analysis</div>
          <div className="text-muted-foreground">Completed in 3.4s</div>
        </div>
      </motion.div>
    </div>
  );
}

/* ---------------- HOW IT WORKS ---------------- */
export function HowItWorks() {
  const steps = [
    { icon: Upload, title: "Upload Document", desc: "Drop your scan, lab report or prescription." },
    { icon: ScanLine, title: "OCR Extracts Text", desc: "Every letter, digit and value read precisely." },
    { icon: Brain, title: "AI Understands", desc: "Medical terminology parsed and contextualized." },
    { icon: Sparkles, title: "Simple Explanation", desc: "Plain-language summary you can actually use." },
  ];
  return (
    <SectionShell id="how">
      <div className="mb-14 text-center">
        <EyebrowChip>How it works</EyebrowChip>
        <motion.h2
          initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }} transition={{ duration: 0.7 }}
          className="mt-4 text-4xl font-semibold tracking-tight md:text-5xl"
        >
          From paperwork to <span className="text-gradient">clarity</span>.
        </motion.h2>
      </div>
      <div className="relative">
        <div className="pointer-events-none absolute left-0 right-0 top-16 hidden h-px md:block">
          <motion.div
            initial={{ scaleX: 0 }} whileInView={{ scaleX: 1 }} viewport={{ once: true }}
            transition={{ duration: 1.4, ease: "easeInOut" }}
            className="h-px origin-left bg-gradient-to-r from-primary/50 via-teal/50 to-transparent"
          />
        </div>
        <div className="grid grid-cols-1 gap-6 md:grid-cols-4">
          {steps.map((s, i) => (
            <motion.div
              key={s.title}
              initial={{ opacity: 0, y: 30 }} whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-60px" }}
              transition={{ delay: i * 0.12, duration: 0.6, ease: "easeOut" }}
              className="relative"
            >
              <div className="glass rounded-3xl p-6">
                <div className="grid h-12 w-12 place-items-center rounded-2xl gradient-medical text-white shadow-lg shadow-primary/20">
                  <s.icon className="h-5 w-5" />
                </div>
                <div className="mt-4 text-xs font-semibold uppercase tracking-wider text-muted-foreground">Step {i + 1}</div>
                <h3 className="mt-1 text-lg font-semibold">{s.title}</h3>
                <p className="mt-2 text-sm text-muted-foreground">{s.desc}</p>
              </div>
              {i < 3 && (
                <ChevronRight className="absolute -right-2 top-1/2 hidden h-5 w-5 -translate-y-1/2 text-primary/40 md:block" />
              )}
            </motion.div>
          ))}
        </div>
      </div>
    </SectionShell>
  );
}

/* ---------------- UPLOAD CARDS ---------------- */
export function UploadOptions() {
  const options = [
    { kind: "scan", icon: ScanSearch, title: "Scan Report", desc: "Upload MRI, CT, X-Ray, Ultrasound or other scan reports.", cta: "Analyze Scan" },
    { kind: "lab", icon: FlaskConical, title: "Lab Report", desc: "Blood tests and lab reports with abnormal values highlighted and explained.", cta: "Analyze Lab Report" },
    { kind: "prescription", icon: Pill, title: "Prescription", desc: "Explain medicines, dosage, purpose, side effects and precautions.", cta: "Analyze Prescription" },
  ] as const;
  return (
    <SectionShell id="upload">
      <div className="mb-14 text-center">
        <EyebrowChip>Choose your document</EyebrowChip>
        <h2 className="mt-4 text-4xl font-semibold tracking-tight md:text-5xl">
          One place for every <span className="text-gradient">medical document</span>.
        </h2>
      </div>
      <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
        {options.map((o, i) => (
          <TiltCard key={o.kind} delay={i * 0.1}>
            <Link to="/chat/$kind" params={{ kind: o.kind }} className="group block h-full">
              <div className="glass relative h-full overflow-hidden rounded-3xl p-7 transition-all duration-500 hover:-translate-y-1.5 hover:shadow-2xl hover:shadow-primary/20">
                <div className="pointer-events-none absolute inset-0 rounded-3xl opacity-0 transition group-hover:opacity-100"
                  style={{ background: "radial-gradient(circle at 30% 0%, oklch(0.72 0.14 190 / 0.15), transparent 60%)" }}
                />
                <div className="grid h-14 w-14 place-items-center rounded-2xl gradient-medical text-white shadow-lg shadow-primary/30">
                  <o.icon className="h-6 w-6" />
                </div>
                <h3 className="mt-5 text-xl font-semibold">{o.title}</h3>
                <p className="mt-2 text-sm text-muted-foreground">{o.desc}</p>
                <div className="mt-6 inline-flex items-center gap-2 text-sm font-medium text-primary">
                  {o.cta} <ArrowRight className="h-4 w-4 transition group-hover:translate-x-0.5" />
                </div>
              </div>
            </Link>
          </TiltCard>
        ))}
      </div>
    </SectionShell>
  );
}

function TiltCard({ children, delay = 0 }: { children: React.ReactNode; delay?: number }) {
  const ref = useRef<HTMLDivElement>(null);
  const mx = useMotionValue(0);
  const my = useMotionValue(0);
  const rx = useSpring(useTransform(my, [-0.5, 0.5], [6, -6]), { stiffness: 200, damping: 20 });
  const ry = useSpring(useTransform(mx, [-0.5, 0.5], [-6, 6]), { stiffness: 200, damping: 20 });
  return (
    <motion.div
      ref={ref}
      onMouseMove={(e) => {
        const r = e.currentTarget.getBoundingClientRect();
        mx.set((e.clientX - r.left) / r.width - 0.5);
        my.set((e.clientY - r.top) / r.height - 0.5);
      }}
      onMouseLeave={() => { mx.set(0); my.set(0); }}
      initial={{ opacity: 0, y: 30 }} whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-60px" }}
      transition={{ delay, duration: 0.6 }}
      style={{ rotateX: rx, rotateY: ry, transformPerspective: 1200 }}
    >
      {children}
    </motion.div>
  );
}

/* ---------------- DEMO ---------------- */
export function InteractiveDemo() {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true, margin: "-100px" });
  const [phase, setPhase] = useState(0);
  const [typed, setTyped] = useState("");
  const summary = "Your MRI shows a small disc bulge at L4-L5. This is common and often improves with physiotherapy. Follow up with your orthopedic specialist.";

  useEffect(() => {
    if (!inView) return;
    const timers: ReturnType<typeof setTimeout>[] = [];
    timers.push(setTimeout(() => setPhase(1), 600));
    timers.push(setTimeout(() => setPhase(2), 1800));
    timers.push(setTimeout(() => setPhase(3), 3200));
    return () => timers.forEach(clearTimeout);
  }, [inView]);

  useEffect(() => {
    if (phase < 3) return;
    let i = 0;
    const id = setInterval(() => {
      i++;
      setTyped(summary.slice(0, i));
      if (i >= summary.length) clearInterval(id);
    }, 22);
    return () => clearInterval(id);
  }, [phase]);

  return (
    <SectionShell id="demo">
      <div className="mb-14 text-center">
        <EyebrowChip>Live demo</EyebrowChip>
        <h2 className="mt-4 text-4xl font-semibold tracking-tight md:text-5xl">
          Watch it work <span className="text-gradient">in real time</span>.
        </h2>
      </div>
      <div ref={ref} className="glass relative overflow-hidden rounded-3xl p-8 md:p-10">
        <div className="grid grid-cols-1 gap-8 md:grid-cols-2">
          {/* Left: document */}
          <div className="relative min-h-[320px] rounded-2xl border border-border bg-white/70 p-5">
            <div className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Document</div>
            <div className="mt-3 space-y-2">
              {["Patient: J. Doe", "Study: MRI Lumbar Spine", "Findings: Mild disc bulge L4-L5", "Impression: Degenerative changes", "Recommendation: Physiotherapy"].map((line, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0 }} animate={phase >= 1 ? { opacity: 1 } : {}}
                  transition={{ delay: i * 0.15 }}
                  className="h-3 rounded bg-muted"
                  style={{ width: `${60 + (i * 8) % 40}%` }}
                />
              ))}
            </div>
            {phase >= 1 && phase < 3 && (
              <motion.div
                initial={{ top: 0 }} animate={{ top: "100%" }}
                transition={{ duration: 1.4, repeat: phase < 3 ? Infinity : 0, ease: "linear" }}
                className="pointer-events-none absolute left-0 right-0 h-16"
                style={{ background: "linear-gradient(to bottom, transparent, oklch(0.72 0.14 190 / 0.35), transparent)" }}
              />
            )}
            {phase >= 2 && (
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="mt-4 flex flex-wrap gap-1.5">
                {["disc bulge", "L4-L5", "degenerative", "physiotherapy"].map((t, i) => (
                  <motion.span
                    key={t}
                    initial={{ scale: 0.6, opacity: 0 }} animate={{ scale: 1, opacity: 1 }}
                    transition={{ delay: i * 0.15 }}
                    className="rounded-md bg-primary/10 px-2 py-1 text-xs font-medium text-primary"
                  >
                    {t}
                  </motion.span>
                ))}
              </motion.div>
            )}
          </div>
          {/* Right: AI summary */}
          <div className="relative min-h-[320px] rounded-2xl bg-gradient-to-br from-primary/10 to-teal/10 p-6">
            <div className="flex items-center gap-2 text-xs font-semibold text-primary">
              <Sparkles className="h-4 w-4" /> AI Simplified Explanation
            </div>
            <div className="mt-4 min-h-[140px] text-base leading-relaxed text-foreground/85">
              {typed}
              {phase >= 3 && typed.length < summary.length && (
                <span className="ml-0.5 inline-block h-4 w-0.5 animate-pulse bg-primary align-middle" />
              )}
            </div>
            {phase >= 3 && typed.length === summary.length && (
              <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="mt-4 inline-flex items-center gap-1.5 text-xs font-medium text-teal">
                <CheckCircle2 className="h-4 w-4" /> Explanation ready
              </motion.div>
            )}
          </div>
        </div>
      </div>
    </SectionShell>
  );
}

/* ---------------- FEATURES ---------------- */
export function Features() {
  const items = [
    { icon: ScanLine, title: "OCR Text Extraction", desc: "Reads scanned PDFs, images and handwriting." },
    { icon: Brain, title: "AI Medical Simplification", desc: "Turns jargon into plain language." },
    { icon: Pill, title: "Prescription Understanding", desc: "Dosage, purpose, side effects." },
    { icon: FlaskConical, title: "Lab Report Analysis", desc: "Flags abnormal values instantly." },
    { icon: ScanSearch, title: "Scan Report Analysis", desc: "MRI, CT, X-Ray, Ultrasound." },
    { icon: ShieldCheck, title: "Secure Processing", desc: "Encrypted end-to-end, never shared." },
    { icon: Zap, title: "Fast Results", desc: "Answers in under 5 seconds." },
    { icon: Languages, title: "Plain Language", desc: "Written for humans, not doctors." },
  ];
  return (
    <SectionShell id="features">
      <div className="mb-14 text-center">
        <EyebrowChip>Features</EyebrowChip>
        <h2 className="mt-4 text-4xl font-semibold tracking-tight md:text-5xl">
          Built to make medicine <span className="text-gradient">approachable</span>.
        </h2>
      </div>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {items.map((f, i) => (
          <motion.div
            key={f.title}
            initial={{ opacity: 0, y: 24 }} whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-40px" }}
            transition={{ delay: (i % 4) * 0.08, duration: 0.55 }}
            className="glass group rounded-3xl p-6 transition hover:-translate-y-1 hover:shadow-xl hover:shadow-primary/10"
          >
            <div className="grid h-11 w-11 place-items-center rounded-xl bg-primary/10 text-primary transition group-hover:gradient-medical group-hover:text-white">
              <f.icon className="h-5 w-5" />
            </div>
            <h3 className="mt-4 font-semibold">{f.title}</h3>
            <p className="mt-1.5 text-sm text-muted-foreground">{f.desc}</p>
          </motion.div>
        ))}
      </div>
    </SectionShell>
  );
}

/* ---------------- STATS ---------------- */
function Counter({ to, suffix = "", prefix = "", duration = 1.8 }: { to: number; suffix?: string; prefix?: string; duration?: number }) {
  const ref = useRef<HTMLSpanElement>(null);
  const inView = useInView(ref, { once: true, margin: "-40px" });
  const [n, setN] = useState(0);
  useEffect(() => {
    if (!inView) return;
    const start = performance.now();
    let raf = 0;
    const tick = (t: number) => {
      const p = Math.min(1, (t - start) / (duration * 1000));
      const eased = 1 - Math.pow(1 - p, 3);
      setN(Math.floor(eased * to));
      if (p < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [inView, to, duration]);
  return <span ref={ref}>{prefix}{n.toLocaleString()}{suffix}</span>;
}

export function Stats() {
  const stats = [
    { label: "Accuracy", value: 98, suffix: "%" },
    { label: "Reports simplified", value: 15000, suffix: "+" },
    { label: "Medical terms explained", value: 50, suffix: "+" },
    { label: "Avg analysis time", value: 5, prefix: "<", suffix: "s" },
  ];
  return (
    <SectionShell id="stats">
      <div className="glass rounded-3xl px-6 py-14 md:px-12">
        <div className="grid grid-cols-2 gap-8 md:grid-cols-4">
          {stats.map((s, i) => (
            <motion.div
              key={s.label} className="text-center"
              initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }} transition={{ delay: i * 0.1 }}
            >
              <div className="text-4xl font-semibold tracking-tight md:text-5xl text-gradient">
                <Counter to={s.value} suffix={s.suffix} prefix={s.prefix ?? ""} />
              </div>
              <div className="mt-2 text-sm text-muted-foreground">{s.label}</div>
            </motion.div>
          ))}
        </div>
      </div>
    </SectionShell>
  );
}

/* ---------------- TESTIMONIALS ---------------- */
export function Testimonials() {
  const quotes = [
    { name: "Priya S.", role: "Patient", text: "I finally understood my blood report without waiting for the doctor. It felt like having a friend translate everything." },
    { name: "Dr. Aman K.", role: "Medical Student", text: "A brilliant learning companion. The term explanations are accurate and actually helpful." },
    { name: "Marcus T.", role: "Caregiver", text: "I use it to explain my mother's prescriptions to her. It's changed how our family talks about her health." },
    { name: "Elena R.", role: "Patient", text: "The MRI summary was so clear I walked into my follow-up already knowing the right questions to ask." },
    { name: "Kenji O.", role: "Nursing Student", text: "Beautiful UI, fast, and the abnormal value flags are exactly what I need while studying cases." },
  ];
  return (
    <SectionShell>
      <div className="mb-14 text-center">
        <EyebrowChip>Loved by patients & students</EyebrowChip>
        <h2 className="mt-4 text-4xl font-semibold tracking-tight md:text-5xl">
          Real stories from <span className="text-gradient">real people</span>.
        </h2>
      </div>
      <div className="relative overflow-hidden">
        <motion.div
          className="flex gap-6"
          animate={{ x: ["0%", "-50%"] }}
          transition={{ duration: 40, repeat: Infinity, ease: "linear" }}
        >
          {[...quotes, ...quotes].map((q, i) => (
            <div key={i} className="glass w-[340px] shrink-0 rounded-3xl p-6">
              <Quote className="h-5 w-5 text-primary/60" />
              <p className="mt-3 text-sm leading-relaxed text-foreground/85">{q.text}</p>
              <div className="mt-5 flex items-center gap-3">
                <div className="grid h-9 w-9 place-items-center rounded-full gradient-medical text-xs font-semibold text-white">
                  {q.name.split(" ").map(s => s[0]).join("")}
                </div>
                <div>
                  <div className="text-sm font-semibold">{q.name}</div>
                  <div className="text-xs text-muted-foreground">{q.role}</div>
                </div>
              </div>
            </div>
          ))}
        </motion.div>
      </div>
    </SectionShell>
  );
}

/* ---------------- CTA ---------------- */
export function FinalCTA() {
  return (
    <section className="relative overflow-hidden">
      <div className="absolute inset-0 gradient-medical" />
      <div className="absolute inset-0 opacity-70"
        style={{ background: "radial-gradient(circle at 20% 30%, oklch(0.72 0.14 190 / 0.5), transparent 50%), radial-gradient(circle at 80% 70%, oklch(0.55 0.22 265 / 0.5), transparent 50%)" }}
      />
      {[...Array(12)].map((_, i) => (
        <motion.span
          key={i}
          className="absolute rounded-full bg-white/40 blur-xl"
          style={{ width: 60 + (i * 13) % 90, height: 60 + (i * 13) % 90, left: `${(i * 29) % 100}%`, top: `${(i * 47) % 100}%` }}
          animate={{ y: [0, -30, 0], opacity: [0.2, 0.5, 0.2] }}
          transition={{ duration: 8 + (i % 4), repeat: Infinity, ease: "easeInOut", delay: i * 0.3 }}
        />
      ))}
      <div className="relative mx-auto max-w-4xl px-6 py-28 text-center text-white md:py-36">
        <motion.h2
          initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }} transition={{ duration: 0.7 }}
          className="text-4xl font-semibold leading-[1.1] tracking-tight md:text-6xl"
        >
          Medical reports shouldn't be difficult to understand.
        </motion.h2>
        <motion.p
          initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }} transition={{ delay: 0.15, duration: 0.7 }}
          className="mx-auto mt-5 max-w-xl text-white/80"
        >
          Try MedSimplify AI and turn your next report into something you can actually read.
        </motion.p>
        <motion.div
          initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }} transition={{ delay: 0.3, duration: 0.7 }}
          className="mt-10"
        >
          <Link
            to="/upload/$kind" params={{ kind: "scan" }}
            className="inline-flex items-center gap-2 rounded-2xl bg-white px-7 py-4 text-sm font-semibold text-primary shadow-2xl transition hover:scale-[1.02]"
          >
            Start simplifying reports <ArrowRight className="h-4 w-4" />
          </Link>
        </motion.div>
      </div>
    </section>
  );
}
