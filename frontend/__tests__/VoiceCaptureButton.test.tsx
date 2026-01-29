import { render, screen, fireEvent, act } from "@testing-library/react";
import "@testing-library/jest-dom";
import { VoiceCaptureButton } from "../components/features/voice/VoiceCaptureButton";
import { useAudio } from "../hooks/use-audio";

// Mock useAudio
jest.mock("../hooks/use-audio");
const mockUseAudio = useAudio as jest.Mock;

// Mock ResizeObserver
global.ResizeObserver = class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
};

describe("VoiceCaptureButton", () => {
  const mockStartRecording = jest.fn();
  const mockStopRecording = jest.fn();
  const mockOnRecordingComplete = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    mockUseAudio.mockReturnValue({
      startRecording: mockStartRecording,
      stopRecording: mockStopRecording,
      cancelRecording: jest.fn(),
      isRecording: false,
      audioBlob: null,
      error: null,
      isPermissionDenied: false,
    });
  });

  it("renders correctly in idle state", () => {
    render(
      <VoiceCaptureButton onRecordingComplete={mockOnRecordingComplete} />,
    );
    const button = screen.getByRole("button", {
      name: /start voice recording/i,
    });
    expect(button).toBeInTheDocument();
    // Check for mic icon presence (class check or svg presence)
    expect(button.querySelector("svg")).toBeInTheDocument();
  });

  it("starts recording on click", async () => {
    // Start with idle state
    mockUseAudio.mockReturnValue({
      startRecording: mockStartRecording,
      stopRecording: mockStopRecording,
      cancelRecording: jest.fn(),
      isRecording: false,
      audioBlob: null,
      error: null,
      isPermissionDenied: false,
    });

    render(
      <VoiceCaptureButton onRecordingComplete={mockOnRecordingComplete} />,
    );
    const button = screen.getByRole("button", {
      name: /start voice recording/i,
    });

    // Click should trigger start
    await act(async () => {
      fireEvent.click(button);
    });

    expect(mockStartRecording).toHaveBeenCalled();
  });

  it("stops recording on click when recording", async () => {
    // Start with recording state
    mockUseAudio.mockReturnValue({
      startRecording: mockStartRecording,
      stopRecording: mockStopRecording,
      isRecording: true, // Simulate recording state
      audioBlob: null,
    });
    render(
      <VoiceCaptureButton onRecordingComplete={mockOnRecordingComplete} />,
    );

    // Should see "Stop voice recording" label
    const button = screen.getByRole("button", {
      name: /stop voice recording/i,
    });

    fireEvent.click(button);
    expect(mockStopRecording).toHaveBeenCalled();
  });

  it("calls onRecordingComplete when blob is available", () => {
    const mockBlob = new Blob(["audio"], { type: "audio/webm" });
    mockUseAudio.mockReturnValue({
      startRecording: mockStartRecording,
      stopRecording: mockStopRecording,
      isRecording: false,
      audioBlob: mockBlob,
    });

    render(
      <VoiceCaptureButton onRecordingComplete={mockOnRecordingComplete} />,
    );

    // We expect onRecordingComplete to be called in a useEffect when audioBlob changes
    expect(mockOnRecordingComplete).toHaveBeenCalledWith(mockBlob);
  });

  it("shows permission denied dialog when permission is denied", () => {
    mockUseAudio.mockReturnValue({
      startRecording: mockStartRecording,
      stopRecording: mockStopRecording,
      cancelRecording: jest.fn(),
      isRecording: false,
      isPermissionDenied: true,
      audioBlob: null,
      error: null,
    });

    render(
      <VoiceCaptureButton onRecordingComplete={mockOnRecordingComplete} />,
    );
    expect(screen.getByText(/Microphone Access Blocked/i)).toBeInTheDocument();
    expect(screen.getByText(/We need microphone access/i)).toBeInTheDocument();
  });

  it("applies pulsing animation when recording", () => {
    mockUseAudio.mockReturnValue({
      startRecording: mockStartRecording,
      stopRecording: mockStopRecording,
      cancelRecording: jest.fn(),
      isRecording: true,
      audioBlob: null,
      error: null,
      isPermissionDenied: false,
    });

    render(
      <VoiceCaptureButton onRecordingComplete={mockOnRecordingComplete} />,
    );
    // Check for stop recording label since we are recording
    const button = screen.getByRole("button", {
      name: /stop voice recording/i,
    });
    // Verify recording state via class that VoiceButton applies (bg-primary/10 or similar)
    // or checks that the inner container has specific recording classes
    const innerContainer = button.querySelector("div");
    expect(innerContainer?.className).toContain("bg-primary/10");
  });

  it("reloads the page on retry when permission was denied", () => {
    const reloadMock = jest.fn();
    Object.defineProperty(window, "location", {
      value: { reload: reloadMock },
      writable: true,
    });

    mockUseAudio.mockReturnValue({
      startRecording: mockStartRecording,
      stopRecording: mockStopRecording,
      cancelRecording: jest.fn(),
      isRecording: false,
      isPermissionDenied: true,
      audioBlob: null,
      error: null,
    });

    render(
      <VoiceCaptureButton onRecordingComplete={mockOnRecordingComplete} />,
    );

    fireEvent.click(screen.getByText(/Reload & Try Again/i));
    expect(reloadMock).toHaveBeenCalled();
  });
});
