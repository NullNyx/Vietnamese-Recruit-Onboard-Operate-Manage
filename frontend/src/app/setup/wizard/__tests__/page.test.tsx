import '@testing-library/jest-dom';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach, Mock } from 'vitest';
import WizardPage, { WIZARD_STEPS } from '../page';
import { useRouter } from 'next/navigation';

vi.mock('next/navigation', () => ({
  useRouter: vi.fn(),
}));

describe('WizardPage Integration', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (useRouter as Mock).mockReturnValue({ push: vi.fn() });
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({}),
    });
  });

  it('renders the wizard shell with all steps', () => {
    render(<WizardPage />);
    expect(screen.getByText('System Configuration')).toBeInTheDocument();
    
    WIZARD_STEPS.forEach((step) => {
      expect(screen.getByText(step.title)).toBeInTheDocument();
    });
  });

  it('navigates through steps when forms are submitted', async () => {
    render(<WizardPage />);
    const user = userEvent.setup();

    // Step 1: Organization
    expect(screen.getByText('Organization Configuration')).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: 'Save & Continue' }));

    // Step 2: Domains
    await waitFor(() => {
      expect(screen.getByText('Domains Configuration')).toBeInTheDocument();
    });
    await user.type(screen.getByRole('textbox'), 'example.com');
    await user.click(screen.getByRole('button', { name: 'Save & Continue' }));

    // Step 3: Whitelist
    await waitFor(() => {
      expect(screen.getByText('Whitelist Configuration')).toBeInTheDocument();
    });
    await user.type(screen.getByRole('textbox'), 'admin@example.com');
    await user.click(screen.getByRole('button', { name: 'Save & Continue' }));

    // Step 4: OAuth
    await waitFor(() => {
      expect(screen.getByText('Google OAuth Configuration')).toBeInTheDocument();
    });
    const inputs = screen.getAllByRole('textbox');
    const secretInput = screen.getByPlaceholderText(/Client Secret/); // getByRole for password input doesn't work as well, but placeholder is fine
    await user.type(inputs[0], 'client-id');
    await user.type(secretInput, 'client-secret');
    await user.click(screen.getByRole('button', { name: 'Continue to Test' }));

    // Step 5: Finish
    await waitFor(() => {
      expect(screen.getByText('Test Login with Google')).toBeInTheDocument();
    });
  });
});
