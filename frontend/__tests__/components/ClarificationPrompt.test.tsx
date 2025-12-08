import '@testing-library/jest-dom';
import { render, screen, fireEvent, act } from '@testing-library/react';
import { ClarificationPrompt } from '@/components/features/analysis/ClarificationPrompt';

// Mock VoiceCaptureButton
jest.mock('@/components/features/voice/VoiceCaptureButton', () => ({
  VoiceCaptureButton: ({ onRecordingComplete }: { onRecordingComplete: (blob: Blob) => void }) => (
    <button
      data-testid="voice-capture-button"
      onClick={() => onRecordingComplete(new Blob())}
    >
      Hold to speak
    </button>
  ),
}));

// Mock timers for countdown
jest.useFakeTimers();

describe('ClarificationPrompt', () => {
  const mockOnSubmit = jest.fn();
  const mockOnSkip = jest.fn();
  const defaultProps = {
    question: 'How big was the portion?',
    options: ['Small', 'Medium', 'Large'],
    timeoutSeconds: 30,
    onSubmit: mockOnSubmit,
    onSkip: mockOnSkip,
  };

  beforeEach(() => {
    jest.clearAllMocks();
    jest.clearAllTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
    jest.useFakeTimers();
  });

  it('renders question and options', () => {
    render(<ClarificationPrompt {...defaultProps} />);

    expect(screen.getByText('How big was the portion?')).toBeInTheDocument();
    expect(screen.getByText('Small')).toBeInTheDocument();
    expect(screen.getByText('Medium')).toBeInTheDocument();
    expect(screen.getByText('Large')).toBeInTheDocument();
  });

  it('calls onSubmit with option when clicked', () => {
    render(<ClarificationPrompt {...defaultProps} />);

    fireEvent.click(screen.getByText('Medium'));

    expect(mockOnSubmit).toHaveBeenCalledWith('Medium', false);
  });

  it('shows voice capture button by default', () => {
    render(<ClarificationPrompt {...defaultProps} />);

    expect(screen.getByTestId('voice-capture-button')).toBeInTheDocument();
  });

  it('shows text input when "Type instead" is clicked', () => {
    render(<ClarificationPrompt {...defaultProps} />);

    fireEvent.click(screen.getByText('Type instead'));

    expect(screen.getByPlaceholderText('Type your answer...')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /send/i })).toBeInTheDocument();
  });

  it('calls onSubmit when text is submitted', () => {
    render(<ClarificationPrompt {...defaultProps} />);

    // Switch to text input
    fireEvent.click(screen.getByText('Type instead'));

    const input = screen.getByPlaceholderText('Type your answer...');
    fireEvent.change(input, { target: { value: 'About half a cup' } });
    fireEvent.click(screen.getByRole('button', { name: /send/i }));

    expect(mockOnSubmit).toHaveBeenCalledWith('About half a cup', false);
  });

  it('submits on Enter key press in text input', () => {
    render(<ClarificationPrompt {...defaultProps} />);

    // Switch to text input
    fireEvent.click(screen.getByText('Type instead'));

    const input = screen.getByPlaceholderText('Type your answer...');
    fireEvent.change(input, { target: { value: 'Two slices' } });
    fireEvent.keyDown(input, { key: 'Enter' });

    expect(mockOnSubmit).toHaveBeenCalledWith('Two slices', false);
  });

  it('does not submit empty text', () => {
    render(<ClarificationPrompt {...defaultProps} />);

    // Switch to text input
    fireEvent.click(screen.getByText('Type instead'));

    const sendButton = screen.getByRole('button', { name: /send/i });
    expect(sendButton).toBeDisabled();
  });

  it('shows skip button when remaining time is 10 seconds or less', () => {
    render(<ClarificationPrompt {...defaultProps} />);

    // Initial render - skip button should not be visible
    expect(screen.queryByText(/Taking too long/i)).not.toBeInTheDocument();

    // Advance timer to 21 seconds (9 seconds remaining)
    act(() => {
      jest.advanceTimersByTime(21000);
    });

    expect(screen.getByText(/Taking too long/i)).toBeInTheDocument();
  });

  it('calls onSkip when skip button is clicked', () => {
    render(<ClarificationPrompt {...defaultProps} />);

    // Advance to show skip button
    act(() => {
      jest.advanceTimersByTime(21000);
    });

    fireEvent.click(screen.getByText(/Taking too long/i));

    expect(mockOnSkip).toHaveBeenCalledTimes(1);
  });

  it('renders with empty options', () => {
    render(<ClarificationPrompt {...defaultProps} options={[]} />);

    expect(screen.getByText('How big was the portion?')).toBeInTheDocument();
    // Options section should just not render options, but component should still work
    expect(screen.queryByText('Small')).not.toBeInTheDocument();
  });
});
