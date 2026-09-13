import Navigation      from "@/components/landing/Navigation";
import HeroSection     from "@/components/landing/HeroSection";
import StatsSection    from "@/components/landing/StatsSection";
import ProblemSection  from "@/components/landing/ProblemSection";
import HowItWorks      from "@/components/landing/HowItWorks";
import ImpactSection   from "@/components/landing/ImpactSection";
import FeatureBento    from "@/components/landing/FeatureBento";
import ScienceSection  from "@/components/landing/ScienceSection";
import ComparisonTable from "@/components/landing/ComparisonTable";
import Testimonials    from "@/components/landing/Testimonials";
import InvestorSection from "@/components/landing/InvestorSection";
import CTASection      from "@/components/landing/CTASection";
import Footer          from "@/components/landing/Footer";

export default function LandingPage() {
  return (
    <main style={{ background: "var(--land-bg)", minHeight: "100vh" }}>
      <Navigation />
      <HeroSection />
      <StatsSection />
      <ProblemSection />
      <HowItWorks />
      <ImpactSection />
      <FeatureBento />
      <ScienceSection />
      <ComparisonTable />
      <Testimonials />
      <InvestorSection />
      <CTASection />
      <Footer />
    </main>
  );
}
