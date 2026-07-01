"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";

async function fetchSetupStatus() {
  const res = await fetch("/api/setup/status");
  if (!res.ok) throw new Error("Failed to fetch setup status");
  return res.json();
}

async function submitOrganization(data: { organization_name: string; timezone: string }) {
  const res = await fetch("/api/setup/organization", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("Failed to save organization");
  return res.json();
}

async function submitAccessControl(data: { allowed_domains: string[] }) {
  const res = await fetch("/api/setup/access-control", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("Failed to save access control");
  return res.json();
}

async function completeSetup() {
  const res = await fetch("/api/setup/complete", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ confirmed: true }),
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
          <div
            className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
              index < currentStep
                ? "bg-blue-600 text-white"
                : index === currentStep
                  ? "bg-blue-100 text-blue-600 border-2 border-blue-600"
                  : "bg-gray-200 text-gray-500"
            }`}
          >
            {index < currentStep ? "✓" : index + 1}
          </div>
          {index < STEPS.length - 2 && (
            <div className={`w-12 h-1 mx-1 ${index < currentStep ? "bg-blue-600" : "bg-gray-200"}`} />
          )}
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
  const [timezone, setTimezone] = useState("Asia/Ho_Chi_Minh");
  const [domains, setDomains] = useState("");

  useEffect(() => {
    async function check() {
      try {
        const status = await fetchSetupStatus();
        if (status.is_locked) {
          router.replace("/login");
          return;
        }
        const idx = STEPS.indexOf(status.current_step);
        setStep(idx >= 0 ? idx : 0);
      } catch {
        setError("Failed to load setup status");
      } finally {
        setLoading(false);
      }
    }
    check();
  }, [router]);

  const handleOrgSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await submitOrganization({ organization_name: orgName, timezone });
      setStep(2);
    } catch {
      setError("Failed to save organization");
    } finally {
      setLoading(false);
    }
  };

  const handleAccessSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const domainList = domains.split("\n").map(d => d.trim()).filter(Boolean);
      await submitAccessControl({ allowed_domains: domainList });
      setStep(3);
    } catch {
      setError("Failed to save access control");
    } finally {
      setLoading(false);
    }
  };

  const handleReview = async () => {
    setLoading(true);
    try {
      await completeSetup();
      setStep(4);
    } catch {
      setError("Failed to complete setup");
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="text-center text-gray-500 py-20">Loading...</div>;
  }

  if (error) {
    return <div className="text-center text-red-500 py-20">{error}</div>;
  }

  return (
    <div>
      <StepIndicator currentStep={step} />

      {step === 0 && (
        <div className="bg-white rounded-lg shadow-sm border p-8">
          <h1 className="text-2xl font-bold text-center mb-4">Welcome to Vroom HR</h1>
          <p className="text-gray-600 text-center mb-6">
            Set up your organization to get started. This wizard will configure
            your company details and access control.
          </p>
          <button
            onClick={() => setStep(1)}
            className="w-full py-3 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg"
          >
            Get Started
          </button>
        </div>
      )}

      {step === 1 && (
        <form onSubmit={handleOrgSubmit} className="bg-white rounded-lg shadow-sm border p-8">
          <h2 className="text-xl font-bold mb-6">Organization Basics</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1">Organization Name</label>
              <input
                type="text"
                value={orgName}
                onChange={e => setOrgName(e.target.value)}
                required
                className="w-full border rounded-lg px-4 py-2 focus:ring-2 focus:ring-blue-500"
                placeholder="Your Company Name"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Timezone</label>
              <select
                value={timezone}
                onChange={e => setTimezone(e.target.value)}
                className="w-full border rounded-lg px-4 py-2 focus:ring-2 focus:ring-blue-500"
              >
                <option value="Asia/Ho_Chi_Minh">Asia/Ho_Chi_Minh (ICT)</option>
                <option value="Asia/Bangkok">Asia/Bangkok (ICT)</option>
                <option value="Asia/Singapore">Asia/Singapore (SGT)</option>
              </select>
            </div>
          </div>
          <div className="flex gap-4 mt-8">
            <button type="button" onClick={() => setStep(0)} className="flex-1 py-3 border rounded-lg hover:bg-gray-50">
              Back
            </button>
            <button type="submit" disabled={loading} className="flex-1 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50">
              Continue
            </button>
          </div>
        </form>
      )}

      {step === 2 && (
        <form onSubmit={handleAccessSubmit} className="bg-white rounded-lg shadow-sm border p-8">
          <h2 className="text-xl font-bold mb-6">Access Control</h2>
          <div>
            <label className="block text-sm font-medium mb-1">Allowed Email Domains</label>
            <textarea
              value={domains}
              onChange={e => setDomains(e.target.value)}
              rows={4}
              className="w-full border rounded-lg px-4 py-2 focus:ring-2 focus:ring-blue-500"
              placeholder="example.com&#10;company.io"
            />
            <p className="mt-2 text-sm text-gray-500">
              Users with emails from these domains can sign in. One per line.
            </p>
          </div>
          <div className="flex gap-4 mt-8">
            <button type="button" onClick={() => setStep(1)} className="flex-1 py-3 border rounded-lg hover:bg-gray-50">
              Back
            </button>
            <button type="submit" disabled={loading} className="flex-1 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50">
              Continue
            </button>
          </div>
        </form>
      )}

      {step === 3 && (
        <div className="bg-white rounded-lg shadow-sm border p-8">
          <h2 className="text-xl font-bold mb-6">Review & Complete</h2>
          <div className="space-y-3 mb-8">
            <div className="flex items-center gap-3 text-green-600">
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
              <span>Organization basics configured</span>
            </div>
            <div className="flex items-center gap-3 text-green-600">
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
              <span>Access control configured</span>
            </div>
          </div>
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-8">
            <p className="text-sm text-yellow-800">
              <strong>Important:</strong> Once completed, the wizard locks permanently.
            </p>
          </div>
          <div className="flex gap-4">
            <button type="button" onClick={() => setStep(2)} className="flex-1 py-3 border rounded-lg hover:bg-gray-50">
              Back
            </button>
            <button onClick={handleReview} disabled={loading} className="flex-1 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50">
              Complete Setup
            </button>
          </div>
        </div>
      )}

      {step === 4 && (
        <div className="bg-white rounded-lg shadow-sm border p-8 text-center">
          <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-green-600" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
            </svg>
          </div>
          <h2 className="text-2xl font-bold mb-2">Setup Complete!</h2>
          <p className="text-gray-600 mb-6">Redirecting to login...</p>
          <button onClick={() => router.push("/login")} className="py-3 px-6 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
            Go to Login
          </button>
        </div>
      )}
    </div>
  );
}
