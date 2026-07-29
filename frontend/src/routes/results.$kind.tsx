import { createFileRoute, Link } from "@tanstack/react-router";
import { motion } from "motion/react";
import { Sparkles, CheckCircle2, AlertTriangle, Info, Heart, Stethoscope, ArrowLeft, ShieldAlert } from "lucide-react";
import { Nav, Footer, ScrollProgress, EyebrowChip } from "@/components/site/shell";

export const Route = createFileRoute("/results/$kind")({
  head: () => ({
    meta: [
      { title: "AI Analysis Results — MedSimplify AI" },
      { name: "description", content: "Your medical document explained in plain language." },
    ],
  }),
  component: Results,
});

const DATA = {
  scan: {
    title: "MRI Lumbar Spine",
    summary: "Your MRI shows a small disc bulge at L4-L5 with mild degenerative changes. This is a common finding and usually improves with physiotherapy. A follow-up with your orthopedic doctor is recommended.",
    findings: [
      "Mild disc bulge at L4-L5",
      "Degenerative changes typical for age",
      "No nerve compression detected",
      "Rest of the spine appears normal",
    ],
    terms: [
      ["Disc bulge", "The cushion between bones sticks out slightly."],
      ["L4-L5", "The 4th and 5th bones of the lower back."],
      ["Degenerative changes", "Normal wear and tear over time."],
      ["Nerve compression", "Pressure on a nerve that can cause pain."],
    ],
    values: [
      { name: "Disc height L4-L5", value: "6.2 mm", status: "low" },
      { name: "Spinal canal width", value: "14 mm", status: "normal" },
      { name: "Nerve root clearance", value: "Adequate", status: "normal" },
    ],
  },
  lab: {
    title: "Complete Blood Panel",
    summary: "Your report shows mild anemia and elevated cholesterol. Most other values are within a healthy range. Small lifestyle changes should help, and it's a good idea to discuss iron and lipid levels with your doctor.",
    findings: [
      "Hemoglobin slightly below normal",
      "Cholesterol elevated",
      "White blood cells normal",
      "Blood sugar within range",
    ],
    terms: [
      ["Hemoglobin", "Protein in red blood cells that carries oxygen."],
      ["WBC", "White blood cells that fight infection."],
      ["Cholesterol", "A type of fat in the blood."],
      ["Glucose", "Sugar in the blood that gives energy."],
    ],
    values: [
      { name: "Hemoglobin", value: "11.2 g/dL", status: "low" },
      { name: "WBC Count", value: "6.8 K/µL", status: "normal" },
      { name: "Cholesterol", value: "232 mg/dL", status: "high" },
      { name: "Glucose", value: "94 mg/dL", status: "normal" },
    ],
  },
  prescription: {
    title: "Prescription — Dr. R. Kapoor",
    summary: "Your prescription contains a blood pressure medicine and a vitamin supplement. Take them at the same times each day, watch for the noted side effects, and let your doctor know if anything feels off.",
    findings: [
      "Amlodipine 5mg — once daily",
      "Vitamin D3 60,000 IU — once weekly",
      "Duration: 30 days",
      "Follow-up in 4 weeks",
    ],
    terms: [
      ["Amlodipine", "Medicine that helps lower high blood pressure."],
      ["Vitamin D3", "Supplement that supports bone and immune health."],
      ["Once daily", "Take one dose every day, ideally at the same time."],
      ["Follow-up", "A future check-in with your doctor."],
    ],
    values: [
      { name: "Amlodipine dose", value: "5 mg", status: "normal" },
      { name: "Vitamin D3 dose", value: "60,000 IU / week", status: "normal" },
      { name: "Course length", value: "30 days", status: "normal" },
    ],
  },
} as const;

type Kind = keyof typeof DATA;

function Results() {
  const { kind } = Route.useParams();
  const k = (kind as Kind) in DATA ? (kind as Kind) : "scan";
  const d = DATA[k];

  return (
    <div className="relative min-h-screen bg-background">
      <ScrollProgress />
      <Nav />
      <div className="mesh-bg pt-32 pb-16">
        <div className="mx-auto max-w-5xl px-6">
          <Link to="/upload/$kind" params={{ kind: k }} className="inline-flex items-center gap-1.5 text-sm text-muted-foreground transition hover:text-foreground">
            <ArrowLeft className="h-4 w-4" /> Upload another
          </Link>

          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="mt-6">
            <EyebrowChip>Analysis complete</EyebrowChip>
            <h1 className="mt-4 text-4xl font-semibold tracking-tight md:text-5xl">
              {d.title}
            </h1>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}
            className="glass mt-8 overflow-hidden rounded-3xl p-8"
          >
            <div className="flex items-center gap-2 text-xs font-semibold text-primary">
              <Sparkles className="h-4 w-4" /> AI Summary
            </div>
            <p className="mt-3 text-lg leading-relaxed text-foreground/90">{d.summary}</p>
          </motion.div>

          <div className="mt-6 grid grid-cols-1 gap-6 md:grid-cols-2">
            <Card delay={0.15} icon={CheckCircle2} title="Key findings">
              <ul className="space-y-3">
                {d.findings.map((f) => (
                  <li key={f} className="flex items-start gap-2 text-sm">
                    <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-teal" />
                    <span>{f}</span>
                  </li>
                ))}
              </ul>
            </Card>

            <Card delay={0.2} icon={AlertTriangle} title="Highlighted values">
              <div className="space-y-2">
                {d.values.map((v) => (
                  <div key={v.name} className="flex items-center justify-between rounded-xl bg-white/60 px-3 py-2.5 text-sm">
                    <span className="text-muted-foreground">{v.name}</span>
                    <span className="font-medium">{v.value}</span>
                    <StatusBadge status={v.status} />
                  </div>
                ))}
              </div>
            </Card>
          </div>

          <Card className="mt-6" delay={0.25} icon={Info} title="Medical terms explained">
            <div className="overflow-hidden rounded-2xl border border-border">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-muted/60 text-left text-xs uppercase tracking-wider text-muted-foreground">
                    <th className="px-4 py-3">Medical term</th>
                    <th className="px-4 py-3">Simple meaning</th>
                  </tr>
                </thead>
                <tbody>
                  {d.terms.map(([term, meaning]) => (
                    <tr key={term} className="border-t border-border/70">
                      <td className="px-4 py-3 font-medium">{term}</td>
                      <td className="px-4 py-3 text-muted-foreground">{meaning}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>

          <div className="mt-6 grid grid-cols-1 gap-6 md:grid-cols-3">
            <Card delay={0.3} icon={Heart} title="Lifestyle">
              <p className="text-sm text-muted-foreground">Stay hydrated, keep light activity daily, and prefer iron- and fiber-rich foods.</p>
            </Card>
            <Card delay={0.35} icon={Stethoscope} title="Follow-up">
              <p className="text-sm text-muted-foreground">Book a check-in with your doctor within 2–4 weeks to review progress.</p>
            </Card>
            <Card delay={0.4} icon={ShieldAlert} title="Precautions">
              <p className="text-sm text-muted-foreground">Avoid heavy lifting and self-medicating. Reach out if symptoms change.</p>
            </Card>
          </div>

          <motion.div
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.5 }}
            className="mt-10 rounded-2xl border border-amber-200 bg-amber-50 p-5 text-sm text-amber-800"
          >
            <div className="flex items-start gap-2">
              <ShieldAlert className="mt-0.5 h-4 w-4 shrink-0" />
              <p>This AI-generated explanation is for educational purposes only and does not replace professional medical advice.</p>
            </div>
          </motion.div>
        </div>
      </div>
      <Footer />
    </div>
  );
}

function Card({ children, title, icon: Icon, delay = 0, className = "" }: any) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }} transition={{ delay, duration: 0.5 }}
      className={`glass rounded-3xl p-6 ${className}`}
    >
      <div className="mb-4 flex items-center gap-2">
        <div className="grid h-9 w-9 place-items-center rounded-xl bg-primary/10 text-primary">
          <Icon className="h-4 w-4" />
        </div>
        <h3 className="font-semibold">{title}</h3>
      </div>
      {children}
    </motion.div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const map: Record<string, string> = {
    normal: "bg-muted text-muted-foreground",
    low: "bg-amber-100 text-amber-700",
    high: "bg-red-100 text-red-700",
  };
  return <span className={`rounded-md px-2 py-0.5 text-[10px] font-semibold uppercase ${map[status] ?? map.normal}`}>{status}</span>;
}
