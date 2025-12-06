import { render, screen, fireEvent, act } from '@testing-library/react';
import '@testing-library/jest-dom';
import { VoiceCaptureButton } from '../components/features/voice/VoiceCaptureButton';
import { useAudio } from '../hooks/use-audio';

// Mock useAudio
jest.mock('../hooks/use-audio');
const mockUseAudio = useAudio as jest.Mock;

describe('VoiceCaptureButton', () => {
  const mockStartRecording = jest.fn();
  const mockStopRecording = jest.fn();
  const mockOnRecordingComplete = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    mockUseAudio.mockReturnValue({
      startRecording: mockStartRecording,
      stopRecording: mockStopRecording,
      isRecording: false,
      audioBlob: null,
      error: null,
      isPermissionDenied: false,
    });
  });

  it('renders correctly in idle state', () => {
    render(<VoiceCaptureButton onRecordingComplete={mockOnRecordingComplete} />);
    const button = screen.getByRole('button', { name: /hold to record/i });
    expect(button).toBeInTheDocument();
    // Check for mic icon presence (class check or svg presence)
    expect(button.querySelector('svg')).toBeInTheDocument();
  });

  it('starts recording on mouse down', async () => {
    render(<VoiceCaptureButton onRecordingComplete={mockOnRecordingComplete} />);
    const button = screen.getByRole('button');

    fireEvent.mouseDown(button);
    expect(mockStartRecording).toHaveBeenCalled();
  });

  it('stops recording on mouse up', () => {
    mockUseAudio.mockReturnValue({
      startRecording: mockStartRecording,
      stopRecording: mockStopRecording,
      isRecording: true,
      audioBlob: null,
    });
    render(<VoiceCaptureButton onRecordingComplete={mockOnRecordingComplete} />);
    const button = screen.getByRole('button');

    fireEvent.mouseUp(button);
    expect(mockStopRecording).toHaveBeenCalled();
  });

  it('calls onRecordingComplete when blob is available', () => {
    const mockBlob = new Blob(['audio'], { type: 'audio/webm' });
    mockUseAudio.mockReturnValue({
        startRecording: mockStartRecording,
      stopRecording: mockStopRecording,
      isRecording: false,
      audioBlob: mockBlob, 
    });

    render(<VoiceCaptureButton onRecordingComplete={mockOnRecordingComplete} />);
    
    // We expect onRecordingComplete to be called in a useEffect when audioBlob changes
    expect(mockOnRecordingComplete).toHaveBeenCalledWith(mockBlob);
  });

  it('shows permission denied error', () => {
    mockUseAudio.mockReturnValue({
      startRecording: mockStartRecording,
      stopRecording: mockStopRecording,
      isRecording: false,
      isPermissionDenied: true,
    });

    render(<VoiceCaptureButton onRecordingComplete={mockOnRecordingComplete} />);
    expect(screen.getByText(/microphone needed/i)).toBeInTheDocument();
  });
  
  it('applies pulsing animation when recording', () => {
       mockUseAudio.mockReturnValue({
      startRecording: mockStartRecording,
      stopRecording: mockStopRecording,
      isRecording: true,
      audioBlob: null
    });
    
    render(<VoiceCaptureButton onRecordingComplete={mockOnRecordingComplete} />);
    const button = screen.getByRole('button');
    expect(button.className).toContain('animate-pulse');
  });
});
