import '@testing-library/jest-dom';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach, Mock } from 'vitest';
import SetupPage from '../page';
import { useRouter } from 'next/navigation';

vi.mock('next/navigation', () => ({
  useRouter: vi.fn(),
}));

describe('SetupPage', () => {
  const pushMock = vi.fn();
  
  beforeEach(() => {
    vi.clearAllMocks();
    (useRouter as Mock).mockReturnValue({ push: pushMock });
    global.fetch = vi.fn();
  });

  it('renders the setup page correctly', () => {
    render(<SetupPage />);
    expect(screen.getByText('First-Run Setup')).toBeInTheDocument();
    expect(screen.getByLabelText('Setup Token')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Verify Token' })).toBeInTheDocument();
  });

  it('disables the button when token is empty', () => {
    render(<SetupPage />);
    const button = screen.getByRole('button', { name: 'Verify Token' });
    expect(button).toBeDisabled();
  });

  it('enables the button when token is entered', async () => {
    render(<SetupPage />);
    const user = userEvent.setup();
    const input = screen.getByLabelText('Setup Token');
    const button = screen.getByRole('button', { name: 'Verify Token' });
    
    await user.type(input, '123456');
    expect(button).toBeEnabled();
  });

  it('shows an error message on API failure', async () => {
    (global.fetch as Mock).mockResolvedValueOnce({
      ok: false,
      json: async () => ({ detail: { message: 'Invalid token' } }),
    });

    render(<SetupPage />);
    const user = userEvent.setup();
    
    await user.type(screen.getByLabelText('Setup Token'), 'wrong-token');
    await user.click(screen.getByRole('button', { name: 'Verify Token' }));

    await waitFor(() => {
      expect(screen.getByText('Invalid token')).toBeInTheDocument();
    });
    expect(pushMock).not.toHaveBeenCalled();
  });

  it('redirects to wizard on API success', async () => {
    (global.fetch as Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({}),
    });

    render(<SetupPage />);
    const user = userEvent.setup();
    
    await user.type(screen.getByLabelText('Setup Token'), 'valid-token');
    await user.click(screen.getByRole('button', { name: 'Verify Token' }));

    await waitFor(() => {
      expect(pushMock).toHaveBeenCalledWith('/setup/wizard');
    });
  });
});
