import { motion, useScroll, useSpring } from "motion/react";
import { Link } from "@tanstack/react-router";
import { Activity } from "lucide-react";
import type { ReactNode } from "react";

export function ScrollProgress() {
  const { scrollYProgress } = useScroll();
  const scaleX = useSpring(scrollYProgress, { stiffness: 120, damping: 30, mass: 0.2 });
  return (
    <motion.div
      style={{ scaleX }}
      className="fixed left-0 right-0 top-0 z-[60] h-[3px] origin-left gradient-medical"
    />
  );
}

export function Nav() {
  return (
    <motion.header
      initial={{ y: -20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.6, ease: "easeOut" }}
      className="fixed left-1/2 top-4 z-50 w-[min(1200px,calc(100%-1.5rem))] -translate-x-1/2"
    >
      <div className="glass flex items-center justify-between rounded-2xl px-5 py-3">
        <Link to="/" className="flex items-center gap-2">
          <div className="grid h-8 w-8 place-items-center rounded-xl gradient-medical text-white">
            <Activity className="h-4 w-4" strokeWidth={2.5} />
          </div>
          <span className="font-semibold tracking-tight">MedSimplify <span className="text-gradient">AI</span></span>
        </Link>
        <nav className="hidden items-center gap-7 text-sm text-muted-foreground md:flex">
          <a href="/#how" className="transition hover:text-foreground">How it works</a>
          <a href="/#features" className="transition hover:text-foreground">Features</a>
          <a href="/#demo" className="transition hover:text-foreground">Demo</a>
          <a href="/#stats" className="transition hover:text-foreground">Impact</a>
        </nav>
        <Link
          to="/chat/$kind"
          params={{ kind: "scan" }}
          className="rounded-xl gradient-medical px-4 py-2 text-sm font-medium text-white shadow-lg shadow-primary/20 transition hover:opacity-90"
        >
          Try it now
        </Link>

      </div>
    </motion.header>
  );
}

export function Footer() {
  return (
    <footer className="border-t border-border/60 bg-surface/50">
      <div className="mx-auto flex max-w-6xl flex-col items-start justify-between gap-6 px-6 py-10 md:flex-row md:items-center">
        <div className="flex items-center gap-2">
          <div className="grid h-8 w-8 place-items-center rounded-xl gradient-medical text-white">
            <Activity className="h-4 w-4" strokeWidth={2.5} />
          </div>
          <span className="font-semibold">MedSimplify AI</span>
        </div>
        <nav className="flex flex-wrap gap-x-6 gap-y-2 text-sm text-muted-foreground">
          <Link to="/" className="hover:text-foreground">Home</Link>
          <a href="/#features" className="hover:text-foreground">Features</a>
          <a href="/#how" className="hover:text-foreground">About</a>
          <a href="#" className="hover:text-foreground">Privacy Policy</a>
          <a href="#" className="hover:text-foreground">Contact</a>
          <a href="https://github.com" className="hover:text-foreground">GitHub</a>
        </nav>
        <p className="text-xs text-muted-foreground">© {new Date().getFullYear()} MedSimplify AI</p>
      </div>
    </footer>
  );
}

export function SectionShell({ id, children, className = "" }: { id?: string; children: ReactNode; className?: string }) {
  return (
    <section id={id} className={`relative mx-auto w-full max-w-6xl px-6 py-24 md:py-32 ${className}`}>
      {children}
    </section>
  );
}

export function EyebrowChip({ children }: { children: ReactNode }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-80px" }}
      className="inline-flex items-center gap-2 rounded-full border border-border bg-white/60 px-3 py-1 text-xs font-medium text-muted-foreground backdrop-blur"
    >
      <span className="h-1.5 w-1.5 rounded-full gradient-medical" />
      {children}
    </motion.div>
  );
}
