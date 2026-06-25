"use client";

import { useState } from "react";
import { Check } from "lucide-react";

import OrganizationStep from "./components/OrganizationStep";
import DomainsStep from "./components/DomainsStep";
import WhitelistStep from "./components/WhitelistStep";
import OAuthStep from "./components/OAuthStep";
import TestFinishStep from "./components/TestFinishStep";

export const WIZARD_STEPS = [
  { id: "org", title: "Organization" },
  { id: "domains", title: "Domains" },
  { id: "whitelist", title: "Whitelist" },
  { id: "oauth", title: "Google OAuth" },
  { id: "finish", title: "Test & Finish" },
];

export default function WizardPage() {
  const [currentStep, setCurrentStep] = useState(0);

  const nextStep = () => setCurrentStep((prev) => Math.min(prev + 1, WIZARD_STEPS.length - 1));
  const prevStep = () => setCurrentStep((prev) => Math.max(prev - 1, 0));

  const renderStepContent = () => {
    switch (currentStep) {
      case 0:
        return <OrganizationStep onNext={nextStep} onBack={prevStep} />;
      case 1:
        return <DomainsStep onNext={nextStep} onBack={prevStep} />;
      case 2:
        return <WhitelistStep onNext={nextStep} onBack={prevStep} />;
      case 3:
        return <OAuthStep onNext={nextStep} onBack={prevStep} />;
      case 4:
        return <TestFinishStep onBack={prevStep} />;
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="mx-auto max-w-3xl space-y-8 mt-10">
        
        {/* Header */}
        <div className="space-y-2 text-center">
          <h1 className="text-3xl font-semibold tracking-tight">System Configuration</h1>
          <p className="text-muted-foreground">Complete these steps to initialize your Vroom HR instance.</p>
        </div>

        {/* Stepper */}
        <div className="flex items-center justify-between relative mt-8 mb-12 px-2">
          <div className="absolute left-0 top-1/2 h-0.5 w-full -translate-y-1/2 bg-border" />
          <div 
            className="absolute left-0 top-1/2 h-0.5 -translate-y-1/2 bg-primary transition-all duration-300"
            style={{ width: `${(currentStep / (WIZARD_STEPS.length - 1)) * 100}%` }}
          />
          {WIZARD_STEPS.map((step, index) => {
            const isCompleted = index < currentStep;
            const isCurrent = index === currentStep;
            
            return (
              <div key={step.id} className="relative z-10 flex flex-col items-center gap-2">
                <div 
                  data-testid={`step-indicator-${index}`}
                  className={`flex h-8 w-8 items-center justify-center rounded-full border-2 transition-colors duration-300 ${
                    isCompleted ? "border-primary bg-primary text-primary-foreground" : 
                    isCurrent ? "border-primary bg-background text-primary" : 
                    "border-border bg-background text-muted-foreground"
                  }`}
                >
                  {isCompleted ? <Check className="h-4 w-4" /> : <span className="text-xs font-semibold">{index + 1}</span>}
                </div>
                <span className={`text-xs font-medium absolute -bottom-6 w-max text-center ${
                  isCurrent ? "text-foreground" : "text-muted-foreground"
                }`}>
                  {step.title}
                </span>
              </div>
            )
          })}
        </div>

        {/* Step Content Shell */}
        <div className="rounded-lg border border-border bg-card p-6 min-h-[300px] flex flex-col shadow-sm">
          <h2 className="text-xl font-semibold mb-6">{WIZARD_STEPS[currentStep].title} Configuration</h2>
          <div className="flex-1 flex flex-col">
            {renderStepContent()}
          </div>
        </div>
      </div>
    </div>
  );
}
