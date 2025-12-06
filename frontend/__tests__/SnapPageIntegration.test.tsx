import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import SnapPage from '../app/(dashboard)/snap/page';

// Mock child components
jest.mock('../components/features/camera/CameraCapture', () => ({
  __esModule: true,
  default: ({ onCapture }: { onCapture: (img: string) => void }) => (
    <button onClick={() => onCapture('mock-image-data')}>Capture</button>
  ),
}));

jest.mock('../components/features/camera/ImagePreview', () => ({
  __esModule: true,
  default: ({ onRetake, onConfirm }: { onRetake: () => void, onConfirm: () => void }) => (
    <div>
      <span>Image Preview</span>
      <button onClick={onRetake}>Retake</button>
      <button onClick={onConfirm}>Confirm</button>
    </div>
  ),
}));

jest.mock('../components/features/voice/VoiceCaptureButton', () => ({
  VoiceCaptureButton: ({ onRecordingComplete }: { onRecordingComplete: (blob: Blob) => void }) => (
    <button onClick={() => onRecordingComplete(new Blob(['audio'], { type: 'audio/webm' }))}>
      Record Voice
    </button>
  ),
}));

describe('SnapPage Integration', () => {
  it('navigates through the capture flow', () => {
    render(<SnapPage />);

    // 1. Initial State: Camera Capture
    const captureBtn = screen.getByText('Capture');
    expect(captureBtn).toBeInTheDocument();
    expect(screen.queryByText('Image Preview')).not.toBeInTheDocument();

    // 2. Capture Image -> Preview State
    fireEvent.click(captureBtn);
    expect(screen.getByText('Image Preview')).toBeInTheDocument();
    expect(screen.queryByText('Capture')).not.toBeInTheDocument();

    // 3. Confirm Image -> Record State
    const confirmBtn = screen.getByText('Confirm');
    fireEvent.click(confirmBtn);
    
    // Check for Record step elements
    expect(screen.getByText("What's in this meal?")).toBeInTheDocument();
    expect(screen.getByText('Record Voice')).toBeInTheDocument();
    expect(screen.queryByText('Image Preview')).not.toBeInTheDocument();

    // 4. Record Voice -> Complete (Console log check not practical, but flow ends here for now)
    const recordBtn = screen.getByText('Record Voice');
    fireEvent.click(recordBtn);
    // Verified it renders and is clickable
  });

  it('allows retaking photo', () => {
    render(<SnapPage />);
    
    // Capture
    fireEvent.click(screen.getByText('Capture'));
    expect(screen.getByText('Image Preview')).toBeInTheDocument();

    // Retake
    fireEvent.click(screen.getByText('Retake'));
    expect(screen.getByText('Capture')).toBeInTheDocument();
    expect(screen.queryByText('Image Preview')).not.toBeInTheDocument();
  });
});
