"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";

async function fetchSetupStatus() {
  const res = await fetch("/api/setup/status");
  if (!res.ok) throw new Error("Failed to fetch setup status");
  return res.json();
}

async function submitOrganization(data: { name: string; tax_code: string; timezone: string }) {
  const res = await fetch("/api/setup/organization", {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("Failed to save organization");
  return res.json();
}

async function completeSetup() {
  const res = await fetch("/api/setup/complete", {
    method: "POST", headers: { "Content-Type": "application/json" },
  });
  if (!res.ok) throw new Error("Failed to complete setup");
  return res.json();
}

const STEPS = ["welcome", "organization", "access-control", "review", "complete"];

function StepIndicator({ currentStep }: { currentStep: number }) {
  return (
    <div className="flex items-center justify-center mb-8 gap-2">
      {STEPS.slice(0, -1).map((step, index) => (
        <div key={step} className="flex items-center">
          <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
            index < currentStep ? "bg-blue-600 text-white"
            : index === currentStep ? "bg-blue-100 text-blue-600 border-2 border-blue-600"
            : "bg-gray-200 text-gray-500"
          }`}>
            {index < currentStep ? "✓" : index + 1}
          </div>
          {index < STEPS.length - 2 && <div className={`w-12 h-1 mx-1 ${index < currentStep ? "bg-blue-600" : "bg-gray-200"}`} />}
        </div>
      ))}
    </div>
  );
}

export default function SetupPage() {
  const router = useRouter();
  const [step, setStep] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [orgName, setOrgName] = useState("");
  const [orgTaxCode, setOrgTaxCode] = useState("");
  const [timezone, setTimezone] = useState("Asia/Ho_Chi_Minh");

  useEffect(() => {
    async function check() {
      try {
        const status = await fetchSetupStatus();
        if (status.setup_complete) { router.replace("/login"); return; }
        setStep(status.org_configured ? 3 : 1);
      } catch { setError("Failed to load setup status"); }
      finally { setLoading(false); }
    }
    check();
  }, [router]);

  const handleOrgSubmit = async (e: React.FormEvent) => {
    e.preventDefault(); setLoading(true);
    try { await submitOrganization({ name: orgName, tax_code: orgTaxCode, timezone }); setStep(3); }
    catch { setError("Failed to save organization"); }
    finally { setLoading(false); }
  };

  const handleComplete = async () => {
    setLoading(true);
    try { await completeSetup(); setStep(4); }
    catch { setError("Failed to complete setup"); }
    finally { setLoading(false); }
  };

  if (loading) return <div className="min-h-screen flex items-center justify-center text-gray-500">Loading...</div>;
  if (error) return <div className="min-h-screen flex items-center justify-center text-red-500">{error}</div>;

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="w-full max-w-xl">
        <StepIndicator currentStep={step} />

        {step === 0 && (
          <div className="bg-white rounded-lg shadow-sm border p-8 text-center">
            <h1 className="text-2xl font-bold mb-4">Welcome to Vroom HR</h1>
            <p className="text-gray-600 mb-6">Set up your organization to get started.</p>
            <button onClick={() => setStep(1)} className="w-full py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700">Get Started</button>
          </div>
        )}

        {step === 1 && (
          <form onSubmit={handleOrgSubmit} className="bg-white rounded-lg shadow-sm border p-8">
            <h2 className="text-xl font-bold mb-6">Organization Basics</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">Organization Name</label>
                <input type="text" value={orgName} onChange={e => setOrgName(e.target.value)} required
                  className="w-full border rounded-lg px-4 py-2 focus:ring-2 focus:ring-blue-500" placeholder="Your Company Name" />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Tax Code</label>
                <input type="text" value={orgTaxCode} onChange={e => setOrgTaxCode(e.target.value)}
                  className="w-full border rounded-lg px-4 py-2 focus:ring-2 focus:ring-blue-500" placeholder="MST (optional)" />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Timezone</label>
                <select value={timezone} onChange={e => setTimezone(e.target.value)}
                  className="w-full border rounded-lg px-4 py-2 focus:ring-2 focus:ring-blue-500">
                  <option value="Asia/Ho_Chi_Minh">Asia/Ho_Chi_Minh (ICT)</option>
                  <option value="Asia/Bangkok">Asia/Bangkok (ICT)</option>
                  <option value="Asia/Singapore">Asia/Singapore (SGT)</option>
                </select>
              </div>
            </div>
            <button type="submit" disabled={loading} className="w-full mt-8 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50">
              Continue
            </button>
          </form>
        )}

        {step === 3 && (
          <div className="bg-white rounded-lg shadow-sm border p-8">
            <h2 className="text-xl font-bold mb-6">Review & Complete</h2>
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-8">
              <p className="text-sm text-yellow-800"><strong>Important:</strong> Once completed, the wizard locks permanently.</p>
            </div>
            <button onClick={handleComplete} disabled={loading} className="w-full py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50">
              Complete Setup
            </button>
          </div>
        )}

        {step === 4 && (
          <div className="bg-white rounded-lg shadow-sm border p-8 text-center">
            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-green-600" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" /></svg>
            </div>
            <h2 className="text-2xl font-bold mb-2">Setup Complete!</h2>
            <p className="text-gray-600 mb-6">Redirecting to login...</p>
            <button onClick={() => router.push("/login")} className="py-3 px-6 bg-blue-600 text-white rounded-lg hover:bg-blue-700">Go to Login</button>
          </div>
        )}
      </div>
    </div>
  );
}
