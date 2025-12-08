import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import SnapPage from '../app/(dashboard)/snap/page'
import '@testing-library/jest-dom'

// Mock useRouter
const mockPush = jest.fn();
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
  }),
}));

// Mock useQueryClient
const mockInvalidateQueries = jest.fn();
jest.mock('@tanstack/react-query', () => ({
  useQueryClient: () => ({
    invalidateQueries: mockInvalidateQueries,
  }),
}));

// Mock ThinkingIndicator
jest.mock('../components/features/analysis/ThinkingIndicator', () => {
  const MockThinkingIndicator = ({ thoughts }: { thoughts: string[] }) => (
    <div data-testid="thinking-indicator">
      {thoughts.map((t, i) => <div key={i}>{t}</div>)}
    </div>
  );
  return {
    __esModule: true,
    ThinkingIndicator: MockThinkingIndicator,
    default: MockThinkingIndicator,
  };
});

// Mock ClarificationPrompt
jest.mock('../components/features/analysis/ClarificationPrompt', () => {
  const MockClarificationPrompt = ({ question, onSubmit, onSkip }: any) => (
    <div data-testid="clarification-prompt">
      <p>{question}</p>
      <button onClick={() => onSubmit('Yes', false)}>Yes</button>
      <button onClick={onSkip}>Skip</button>
    </div>
  );
  return {
    __esModule: true,
    ClarificationPrompt: MockClarificationPrompt,
    default: MockClarificationPrompt,
  };
});

// Mock services
jest.mock('../components/features/camera/CameraCapture', () => ({
    __esModule: true,
    default: ({ onCapture }: { onCapture: (src: string) => void }) => (
        <div data-testid="camera-capture">
            <button onClick={() => onCapture("data:fake-image")}>Snap</button>
        </div>
    )
}));

jest.mock('../components/features/camera/ImagePreview', () => ({
    __esModule: true,
    default: ({ onRetake, onConfirm }: { onRetake: () => void, onConfirm: () => void }) => (
        <div data-testid="image-preview">
            <button onClick={onRetake}>Retake</button>
            <button onClick={onConfirm}>Confirm</button>
        </div>
    )
}));

jest.mock('@/services/upload-service', () => ({
  uploadFile: jest.fn().mockResolvedValue(undefined),
  generateUploadPath: jest.fn((userId, type) => `users/${userId}/${type}/file`),
  deleteFile: jest.fn().mockResolvedValue(undefined)
}));

jest.mock('@/lib/api', () => ({
  analysisApi: {
    upload: jest.fn().mockResolvedValue({ log_id: 'test-log-id' })
  }
}));

jest.mock('@/lib/supabase', () => ({
  supabase: {
    auth: {
      getUser: jest.fn().mockResolvedValue({ data: { user: { id: 'test-user' } } })
    }
  }
}));

// Mock useAgent
const mockStartStreaming = jest.fn();
const mockReset = jest.fn();
const mockUseAgent = jest.fn(() => ({
    status: 'idle',
    thoughts: [],
    result: null,
    error: null,
    clarification: null,
    startStreaming: mockStartStreaming,
    reset: mockReset,
    submitClarificationResponse: jest.fn(),
    skipClarification: jest.fn()
}));

jest.mock('@/hooks/use-agent', () => ({
  useAgent: () => mockUseAgent()
}));

// Mock VoiceCaptureButton
jest.mock('../components/features/voice/VoiceCaptureButton', () => ({
  VoiceCaptureButton: ({ onRecordingComplete }: { onRecordingComplete: (blob: Blob) => void }) => (
    <button onClick={() => onRecordingComplete(new Blob(['audio'], { type: 'audio/webm' }))}>
      Finish Recording
    </button>
  )
}));

describe('SnapPage', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        global.fetch = jest.fn(() =>
          Promise.resolve({
            blob: () => Promise.resolve(new Blob(['fake-image'], { type: 'image/jpeg' })),
          })
        ) as jest.Mock;
        window.alert = jest.fn();
    });

    it('shows camera capture by default', () => {
        render(<SnapPage />)
        expect(screen.getByTestId('camera-capture')).toBeInTheDocument()
        expect(screen.queryByTestId('image-preview')).not.toBeInTheDocument()
    })

    it('transitions to preview on capture', async () => {
        render(<SnapPage />)
        
        // Find "Snap" button from mock and click it
        fireEvent.click(screen.getByText('Snap'))

        await waitFor(() => {
             expect(screen.getByTestId('image-preview')).toBeInTheDocument()
             expect(screen.queryByTestId('camera-capture')).not.toBeInTheDocument()
        })
    })

    it('returns to camera on retake', async () => {
        render(<SnapPage />)
        
        // Capture first
        fireEvent.click(screen.getByText('Snap'))
        await screen.findByTestId('image-preview')

        // Click Retake
        fireEvent.click(screen.getByText('Retake'))

        await waitFor(() => {
             expect(screen.getByTestId('camera-capture')).toBeInTheDocument()
             expect(screen.queryByTestId('image-preview')).not.toBeInTheDocument()
        })
    })

    it('calls startStreaming and transitions to streaming state on successful upload', async () => {
      render(<SnapPage />)

      // 1. Capture
      fireEvent.click(screen.getByText('Snap'))
      await screen.findByTestId('image-preview')

      // 2. Confirm
      fireEvent.click(screen.getByText('Confirm'))
      await screen.findByText('What\'s in this meal?')

      // 3. Record & Upload
      fireEvent.click(screen.getByText('Finish Recording'))

      await waitFor(() => {
        // Should have called startStreaming with log_id from api mock
        expect(mockStartStreaming).toHaveBeenCalledWith(
          'test-log-id', 
          expect.stringContaining('users/test-user/image/file'),
          expect.stringContaining('users/test-user/audio/file')
        );
      });
    })

    it('displays ThinkingIndicator when streaming', async () => {
      // Setup agent to return thoughts
      mockUseAgent.mockReturnValue({
        status: 'streaming',
        thoughts: ['Analyzing image...', 'Detecting food items...'],
        result: null,
        error: null,
        clarification: null,
        startStreaming: mockStartStreaming,
        reset: mockReset,
        submitClarificationResponse: jest.fn(),
        skipClarification: jest.fn()
      });

      render(<SnapPage />);

      // Go through flow to reach 'streaming' step
      fireEvent.click(screen.getByText('Snap'));
      await screen.findByTestId('image-preview');
      fireEvent.click(screen.getByText('Confirm'));
      await screen.findByText('What\'s in this meal?');
      fireEvent.click(screen.getByText('Finish Recording'));

      await waitFor(() => {
        expect(screen.getByTestId('thinking-indicator')).toBeInTheDocument();
        expect(screen.getByText('Analyzing image...')).toBeInTheDocument();
      });
    })

    it('displays ClarificationPrompt when agent requests clarification', async () => {
        mockUseAgent.mockReturnValue({
            status: 'clarifying',
            thoughts: [],
            result: null,
            error: null,
            clarification: { 
                question: 'Is it spicy?', 
                options: ['Yes', 'No'],
                context: {},
                log_id: 'clarification-id' 
            },
            startStreaming: mockStartStreaming,
            reset: mockReset,
            submitClarificationResponse: jest.fn(),
            skipClarification: jest.fn()
        });
  
        // We need to render SnapPage. 
        // Note: step state is internal. 
        // If status is clarifying, SnapPage should automatically show ClarificationPrompt 
        // OR step should be updated.
        // Assuming SnapPage reacts to useAgent status or we transition step manually.
        // Let's assume SnapPage will be updated to handle 'clarifying' status directly or sync step.
        
        // But for step to be 'streaming' or 'clarifying', we need to trigger it if we rely on step.
        // If we implement step sync in useEffect, it should work.
        // For the test, we can just trigger the flow to reach streaming.
  
        render(<SnapPage />);
        // Trigger flow
        fireEvent.click(screen.getByText('Snap'));
        await screen.findByTestId('image-preview');
        fireEvent.click(screen.getByText('Confirm'));
        await screen.findByText('What\'s in this meal?');
        fireEvent.click(screen.getByText('Finish Recording'));
  
        await waitFor(() => {
             expect(screen.getByTestId('clarification-prompt')).toBeInTheDocument();
        });
        await waitFor(() => {
             expect(screen.getByTestId('clarification-prompt')).toBeInTheDocument();
        });
      })

    it('redirects to dashboard when analysis is complete', async () => {
        mockUseAgent.mockReturnValue({
            status: 'complete',
            thoughts: [],
            result: { log_id: 'completed-log-id' } as any,
            error: null,
            clarification: null,
            startStreaming: mockStartStreaming,
            reset: mockReset,
            submitClarificationResponse: jest.fn(),
            skipClarification: jest.fn()
        });

        // Use fake timers to fast forward the delay
        jest.useFakeTimers();
        
        render(<SnapPage />);
        
        // Wait for invalidate
        await waitFor(() => {
            expect(mockInvalidateQueries).toHaveBeenCalledWith({ queryKey: ['logs'] });
        });

        // Fast forward
        jest.advanceTimersByTime(1500);

        await waitFor(() => {
            expect(mockPush).toHaveBeenCalledWith('/');
        });

        jest.useRealTimers();
    })

    it('shows error message when agent errors', async () => {
        mockUseAgent.mockReturnValue({
            status: 'error',
            thoughts: [],
            result: null,
            error: 'AI Connection Failed',
            clarification: null,
            startStreaming: mockStartStreaming,
            reset: mockReset,
            submitClarificationResponse: jest.fn(),
            skipClarification: jest.fn()
        });

        render(<SnapPage />);
        
        // Trigger flow to get to streaming/error state?
        // If error replaces the UI, verify it happens.
        // Assuming SnapPage displays error from agent.
        
        // Transtion to streaming to see if error logic activates in that view
        fireEvent.click(screen.getByText('Snap'));
        await screen.findByTestId('image-preview');
        fireEvent.click(screen.getByText('Confirm'));
        // ...
        
        // Actually, if status is error, we expect Error Overlay (errorMessage state) or ThinkingIndicator error state.
        // The current implementation uses `setErrorMessage` for upload errors.
        // We should probably sync `errorMessage` with `agentError`.
        
        await waitFor(() => {
            expect(screen.getByText('AI Connection Failed')).toBeInTheDocument();
        });

        // Test Retry
        const retryBtn = screen.getByText('Retry');
        fireEvent.click(retryBtn);

        expect(mockReset).toHaveBeenCalled();
        // Should go back to capture (camera capture visible)
        expect(screen.getByTestId('camera-capture')).toBeInTheDocument();
  })
})
