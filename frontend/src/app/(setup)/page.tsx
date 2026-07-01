"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";

// --- Types ---

interface SetupStatus {
  is_initialized: boolean;
  is_locked: boolean;
  setup_completed_at: string | null;
  current_step: string;
}

// --- API Functions ---

async function fetchSetupStatus(): Promise<SetupStatus> {
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

async function submitAccessControl(data: { allowed_domains: string[]; whitelist_emails: string[] }) {
  const res = await fetch("/api/setup/access-control", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("Failed to save access control");
  return res.json();
}

async function submitIdentityProvider(data: { enable_google_oauth: boolean; oauth_client_id?: string; oauth_redirect_uri?: string }) {
  const res = await fetch("/api/setup/identity-provider", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("Failed to save identity provider");
  return res.json();
}

async function completeSetup(confirmed: boolean) {
  const res = await fetch("/api/setup/complete", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ confirmed }),
  });
  if (!res.ok) throw new Error("Failed to complete setup");
  return res.json();
}

// --- Steps Components ---

function WelcomeStep({ onNext }: { onNext: () => void }) {
  return (
    <div className="bg-white rounded-lg shadow-sm border p-8">
      <div className="text-center mb-8">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Welcome to Vroom HR</h1>
        <p className="text-gray-600">
          Let&apos;s set up your organization. This wizard will guide you through configuring
          your company details, access control, and identity provider.
        </p>
      </div>
      <div className="bg-gray-50 rounded-lg p-6 mb-6">
        <h2 className="font-semibold text-gray-900 mb-3">What we&apos;ll configure:</h2>
        <ul className="space-y-2 text-gray-600">
          <li className="flex items-center gap-2">
            <span className="w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-sm font-medium">1</span>
            Organization basics (name, timezone)
          </li>
          <li className="flex items-center gap-2">
            <span className="w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-sm font-medium">2</span>
            Access control (allowed domains, email whitelist)
          </li>
          <li className="flex items-center gap-2">
            <span className="w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-sm font-medium">3</span>
            Identity provider (Google OAuth)
          </li>
          <li className="flex items-center gap-2">
            <span className="w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-sm font-medium">4</span>
            Review and complete
          </li>
        </ul>
      </div>
      <button
        onClick={onNext}
        className="w-full py-3 px-4 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors"
      >
        Get Started
      </button>
    </div>
  );
}

function OrganizationStep({ onNext, onBack }: { onNext: () => void; onBack: () => void }) {
  const [name, setName] = useState("");
  const [timezone, setTimezone] = useState("Asia/Ho_Chi_Minh");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await submitOrganization({ organization_name: name, timezone });
      onNext();
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow-sm border p-8">
      <h2 className="text-xl font-bold text-gray-900 mb-6">Organization Basics</h2>
      
      <div className="space-y-6">
        <div>
          <label htmlFor="orgName" className="block text-sm font-medium text-gray-700 mb-2">
            Organization Name
          </label>
          <input
            id="orgName"
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            placeholder="Your Company Name"
          />
        </div>
        
        <div>
          <label htmlFor="timezone" className="block text-sm font-medium text-gray-700 mb-2">
            Timezone
          </label>
          <select
            id="timezone"
            value={timezone}
            onChange={(e) => setTimezone(e.target.value)}
            required
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="Asia/Ho_Chi_Minh">Asia/Ho_Chi_Minh (ICT)</option>
            <option value="Asia/Bangkok">Asia/Bangkok (ICT)</option>
            <option value="Asia/Singapore">Asia/Singapore (SGT)</option>
            <option value="Asia/Tokyo">Asia/Tokyo (JST)</option>
            <option value="Asia/Seoul">Asia/Seoul (KST)</option>
            <option value="America/New_York">America/New_York (EST)</option>
            <option value="America/Los_Angeles">America/Los_Angeles (PST)</option>
            <option value="Europe/London">Europe/London (GMT)</option>
            <option value="Europe/Paris">Europe/Paris (CET)</option>
          </select>
        </div>
      </div>

      <div className="flex gap-4 mt-8">
        <button
          type="button"
          onClick={onBack}
          className="flex-1 py-3 px-4 border border-gray-300 text-gray-700 font-medium rounded-lg hover:bg-gray-50 transition-colors"
        >
          Back
        </button>
        <button
          type="submit"
          disabled={loading}
          className="flex-1 py-3 px-4 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors disabled:opacity-50"
        >
          {loading ? "Saving..." : "Continue"}
        </button>
      </div>
    </form>
  );
}

function AccessControlStep({ onNext, onBack }: { onNext: () => void; onBack: () => void }) {
  const [domains, setDomains] = useState("");
  const [whitelist, setWhitelist] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const domainList = domains.split("\n").map(d => d.trim()).filter(d => d);
      const emailList = whitelist.split("\n").map(e => e.trim()).filter(e => e);
      await submitAccessControl({ allowed_domains: domainList, whitelist_emails: emailList });
      onNext();
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow-sm border p-8">
      <h2 className="text-xl font-bold text-gray-900 mb-6">Access Control</h2>
      
      <div className="space-y-6">
        <div>
          <label htmlFor="domains" className="block text-sm font-medium text-gray-700 mb-2">
            Allowed Email Domains
          </label>
          <textarea
            id="domains"
            value={domains}
            onChange={(e) => setDomains(e.target.value)}
            rows={4}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            placeholder="example.com&#10;company.io"
          />
          <p className="mt-2 text-sm text-gray-500">
            Enter one domain per line. Users with emails from these domains can sign in.
          </p>
        </div>
        
        <div>
          <label htmlFor="whitelist" className="block text-sm font-medium text-gray-700 mb-2">
            Whitelist (Optional)
          </label>
          <textarea
            id="whitelist"
            value={whitelist}
            onChange={(e) => setWhitelist(e.target.value)}
            rows={4}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            placeholder="admin@example.com&#10;hr@company.io"
          />
          <p className="mt-2 text-sm text-gray-500">
            Enter exact email addresses to allow even if their domain is not in the allowed list.
          </p>
        </div>
      </div>

      <div className="flex gap-4 mt-8">
        <button
          type="button"
          onClick={onBack}
          className="flex-1 py-3 px-4 border border-gray-300 text-gray-700 font-medium rounded-lg hover:bg-gray-50 transition-colors"
        >
          Back
        </button>
        <button
          type="submit"
          disabled={loading}
          className="flex-1 py-3 px-4 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors disabled:opacity-50"
        >
          {loading ? "Saving..." : "Continue"}
        </button>
      </div>
    </form>
  );
}

function IdentityProviderStep({ onNext, onBack }: { onNext: () => void; onBack: () => void }) {
  const [enableGoogle, setEnableGoogle] = useState(true);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await submitIdentityProvider({ enable_google_oauth: enableGoogle });
      onNext();
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow-sm border p-8">
      <h2 className="text-xl font-bold text-gray-900 mb-6">Identity Provider</h2>
      
      <div className="space-y-6">
        <div className="flex items-center justify-between p-4 border rounded-lg">
          <div>
            <h3 className="font-medium text-gray-900">Google OAuth</h3>
            <p className="text-sm text-gray-500">Allow sign-in with Google accounts</p>
          </div>
          <button
            type="button"
            onClick={() => setEnableGoogle(!enableGoogle)}
            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
              enableGoogle ? "bg-blue-600" : "bg-gray-200"
            }`}
          >
            <span
              className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                enableGoogle ? "translate-x-6" : "translate-x-1"
              }`}
            />
          </button>
        </div>
        
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <p className="text-sm text-yellow-800">
            <strong>Note:</strong> OAuth credentials should be configured via environment variables
            for security. Contact your system administrator to set up Google OAuth credentials.
          </p>
        </div>
      </div>

      <div className="flex gap-4 mt-8">
        <button
          type="button"
          onClick={onBack}
          className="flex-1 py-3 px-4 border border-gray-300 text-gray-700 font-medium rounded-lg hover:bg-gray-50 transition-colors"
        >
          Back
        </button>
        <button
          type="submit"
          disabled={loading}
          className="flex-1 py-3 px-4 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors disabled:opacity-50"
        >
          {loading ? "Saving..." : "Continue"}
        </button>
      </div>
    </form>
  );
}

function ReviewStep({ onComplete, onBack }: { onComplete: () => void; onBack: () => void }) {
  const [loading, setLoading] = useState(false);

  const handleComplete = async () => {
    setLoading(true);
    try {
      await completeSetup(true);
      onComplete();
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border p-8">
      <h2 className="text-xl font-bold text-gray-900 mb-6">Review & Complete</h2>
      
      <div className="space-y-4 mb-8">
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
        <div className="flex items-center gap-3 text-green-600">
          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
          </svg>
          <span>Identity provider configured</span>
        </div>
      </div>
      
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-8">
        <p className="text-sm text-yellow-800">
          <strong>Important:</strong> Once you complete setup, the wizard will be locked permanently.
          You won&apos;t be able to access these settings again without direct database access.
        </p>
      </div>

      <div className="flex gap-4">
        <button
          type="button"
          onClick={onBack}
          className="flex-1 py-3 px-4 border border-gray-300 text-gray-700 font-medium rounded-lg hover:bg-gray-50 transition-colors"
        >
          Back
        </button>
        <button
          onClick={handleComplete}
          disabled={loading}
          className="flex-1 py-3 px-4 bg-green-600 hover:bg-green-700 text-white font-medium rounded-lg transition-colors disabled:opacity-50"
        >
          {loading ? "Completing..." : "Complete Setup"}
        </button>
      </div>
    </div>
  );
}

function CompleteStep() {
  const router = useRouter();

  useEffect(() => {
    // Redirect to login after a short delay
    const timer = setTimeout(() => {
      router.push("/login");
    }, 2000);
    return () => clearTimeout(timer);
  }, [router]);

  return (
    <div className="bg-white rounded-lg shadow-sm border p-8 text-center">
      <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
        <svg className="w-8 h-8 text-green-600" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
        </svg>
      </div>
      <h2 className="text-2xl font-bold text-gray-900 mb-2">Setup Complete!</h2>
      <p className="text-gray-600 mb-6">
        Your organization is now configured. Redirecting to login...
      </p>
      <button
        onClick={() => router.push("/login")}
        className="py-3 px-6 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors"
      >
        Go to Login
      </button>
    </div>
  );
}

// --- Main Component ---

const STEPS = ["welcome", "organization", "access-control", "identity-provider", "review", "complete"];

export default function SetupPage() {
  const [currentStep, setCurrentStep] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function checkStatus() {
      try {
        const status = await fetchSetupStatus();
        if (status.is_locked) {
          // Already set up, redirect to login
          window.location.href = "/login";
          return;
        }
        // Determine starting step based on current_step
        const stepIndex = STEPS.indexOf(status.current_step);
        setCurrentStep(stepIndex >= 0 ? stepIndex : 0);
      } catch (err) {
        setError("Failed to load setup status");
      } finally {
        setLoading(false);
      }
    }
    checkStatus();
  }, []);

  const goNext = () => setCurrentStep((prev) => Math.min(prev + 1, STEPS.length - 1));
  const goBack = () => setCurrentStep((prev) => Math.max(prev - 1, 0));

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-gray-600">Loading...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow-sm border p-8 text-center">
        <p className="text-red-600">{error}</p>
      </div>
    );
  }

  return (
    <div>
      {/* Progress indicator */}
      {currentStep < STEPS.length - 1 && (
        <div className="mb-6">
          <div className="flex items-center justify-between">
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
                  <div className={`w-16 h-1 mx-2 ${index < currentStep ? "bg-blue-600" : "bg-gray-200"}`} />
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Step content */}
      {STEPS[currentStep] === "welcome" && <WelcomeStep onNext={goNext} />}
      {STEPS[currentStep] === "organization" && <OrganizationStep onNext={goNext} onBack={goBack} />}
      {STEPS[currentStep] === "access-control" && <AccessControlStep onNext={goNext} onBack={goBack} />}
      {STEPS[currentStep] === "identity-provider" && <IdentityProviderStep onNext={goNext} onBack={goBack} />}
      {STEPS[currentStep] === "review" && <ReviewStep onComplete={goNext} onBack={goBack} />}
      {STEPS[currentStep] === "complete" && <CompleteStep />}
    </div>
  );
}
