import { renderHook, act } from "@testing-library/react";
import { useAudio } from "../hooks/use-audio";

const mockMediaRecorder = {
  start: jest.fn().mockImplementation(function (this: any) {
    this.state = "recording";
  }),
  stop: jest.fn().mockImplementation(function (this: any) {
    this.state = "inactive";
  }),
  ondataavailable: jest.fn(),
  onerror: jest.fn(),
  state: "inactive",
  stream: {
    getTracks: jest.fn(() => [{ stop: jest.fn() }]),
  },
};

// Mock getUserMedia
const mockGetUserMedia = jest.fn(async () => {
  return {
    getTracks: jest.fn(() => [{ stop: jest.fn() }]),
  } as unknown as MediaStream;
});

Object.defineProperty(global, "navigator", {
  value: {
    mediaDevices: {
      getUserMedia: mockGetUserMedia,
    },
  },
  writable: true,
});

// Mock MediaRecorder constructor
(global as any).MediaRecorder = jest.fn(() => mockMediaRecorder);
(global as any).MediaRecorder.isTypeSupported = jest.fn(() => true);

describe("useAudio", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockMediaRecorder.state = "inactive";
  });

  it("should initialize with default states", () => {
    const { result } = renderHook(() => useAudio());

    expect(result.current.isRecording).toBe(false);
    expect(result.current.audioBlob).toBeNull();
    expect(result.current.error).toBeNull();
  });

  it("should start recording successfully", async () => {
    const { result } = renderHook(() => useAudio());

    await act(async () => {
      await result.current.startRecording();
    });

    expect(mockGetUserMedia).toHaveBeenCalledWith({ audio: true });
    expect(mockMediaRecorder.start).toHaveBeenCalled();
    expect(result.current.isRecording).toBe(true);
    expect(result.current.error).toBeNull();
  });

  it("should handle permission denied", async () => {
    mockGetUserMedia.mockRejectedValueOnce(
      new DOMException("Permission denied", "NotAllowedError"),
    );

    const { result } = renderHook(() => useAudio());

    await act(async () => {
      await result.current.startRecording();
    });

    expect(result.current.isPermissionDenied).toBe(true);
    expect(result.current.error).toBeTruthy();
    expect(result.current.isRecording).toBe(false);
  });

  it("should stop recording and return blob", async () => {
    const { result } = renderHook(() => useAudio());

    // Start first
    await act(async () => {
      await result.current.startRecording();
    });

    // Simulate data available event
    const mockBlob = new Blob(["audio data"], { type: "audio/webm" });
    const dataEvent = { data: mockBlob };

    await act(async () => {
      if ((mockMediaRecorder as any).ondataavailable) {
        (mockMediaRecorder as any).ondataavailable(dataEvent);
      }
    });

    await act(async () => {
      result.current.stopRecording();
      // Simulate onstop event which creates the final blob
      if ((mockMediaRecorder as any).onstop) {
        (mockMediaRecorder as any).onstop();
      }
    });

    expect(mockMediaRecorder.stop).toHaveBeenCalled();
    expect(result.current.isRecording).toBe(false);
    expect(result.current.audioBlob).not.toBeNull();
    expect(result.current.audioBlob?.size).toBe(mockBlob.size);
  });
});
