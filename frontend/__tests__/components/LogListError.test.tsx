import '@testing-library/jest-dom';
import { render, screen, fireEvent } from '@testing-library/react';
import { LogListError } from '@/components/features/logs/LogListError';

describe('LogListError', () => {
  it('renders error message', () => {
    render(<LogListError onRetry={() => {}} />);
    expect(screen.getByText('Unable to load meals')).toBeInTheDocument();
  });

  it('renders retry button', () => {
    render(<LogListError onRetry={() => {}} />);
    expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument();
  });

  it('calls onRetry when retry button is clicked', () => {
    const mockRetry = jest.fn();
    render(<LogListError onRetry={mockRetry} />);
    
    fireEvent.click(screen.getByRole('button', { name: /retry/i }));
    
    expect(mockRetry).toHaveBeenCalledTimes(1);
  });

  it('renders helpful message text', () => {
    render(<LogListError onRetry={() => {}} />);
    expect(screen.getByText(/something went wrong/i)).toBeInTheDocument();
  });
});
