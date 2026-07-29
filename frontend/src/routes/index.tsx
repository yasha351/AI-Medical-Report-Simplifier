import { createFileRoute } from "@tanstack/react-router";
import { Nav, Footer, ScrollProgress } from "@/components/site/shell";
import {
  Hero, HowItWorks, UploadOptions, InteractiveDemo,
  Features, Stats, Testimonials, FinalCTA,
} from "@/components/site/landing";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "MedSimplify AI — Understand your medical reports in seconds" },
      { name: "description", content: "AI-powered platform that turns scan reports, lab reports and prescriptions into clear, simple language." },
      { property: "og:title", content: "MedSimplify AI" },
      { property: "og:description", content: "Understand your medical reports in seconds with AI." },
    ],
  }),
  component: Index,
});

function Index() {
  return (
    <div className="relative bg-background">
      <ScrollProgress />
      <Nav />
      <main>
        <Hero />
        <HowItWorks />
        <UploadOptions />
        <InteractiveDemo />
        <Features />
        <Stats />
        <Testimonials />
        <FinalCTA />
      </main>
      <Footer />
    </div>
  );
}
