import { render, screen, fireEvent } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import "@testing-library/jest-dom";
import SnapPage from "../app/(dashboard)/snap/page";

// Mock child components
jest.mock("../components/features/camera/CameraCapture", () => ({
  __esModule: true,
  default: ({ onCapture }: { onCapture: (img: string) => void }) => (
    <button onClick={() => onCapture("mock-image-data")}>Capture</button>
  ),
}));

jest.mock("../components/features/camera/ImagePreview", () => ({
  __esModule: true,
  default: ({
    onRetake,
    onConfirm,
  }: {
    onRetake: () => void;
    onConfirm: () => void;
  }) => (
    <div>
      <span>Image Preview</span>
      <button onClick={onRetake}>Retake</button>
      <button onClick={onConfirm}>Confirm</button>
    </div>
  ),
}));

jest.mock("../components/features/voice/VoiceCaptureButton", () => ({
  VoiceCaptureButton: ({
    onRecordingComplete,
  }: {
    onRecordingComplete: (blob: Blob) => void;
  }) => (
    <button
      onClick={() =>
        onRecordingComplete(new Blob(["audio"], { type: "audio/webm" }))
      }
    >
      Record Voice
    </button>
  ),
}));

jest.mock("@/components/features/input/TextEntryModal", () => ({
  TextEntryModal: ({
    isOpen,
    onClose,
  }: {
    isOpen: boolean;
    onClose: () => void;
  }) => (isOpen ? <div role="dialog">Text Entry Modal <button onClick={onClose}>Close</button></div> : null),
}));

// Mock useAgent
jest.mock("@/hooks/use-agent", () => ({
  useAgent: () => ({
    status: "idle",
    thoughts: [],
    startStreaming: jest.fn(),
    submitText: jest.fn(),
  }),
}));

// Mock services/upload-service
jest.mock("@/services/upload-service", () => ({
  uploadFile: jest.fn(),
  generateUploadPath: jest.fn(() => "mock-path"),
  deleteFile: jest.fn(),
}));

// Mock lib/api
jest.mock("@/lib/api", () => ({
  analysisApi: {
    upload: jest.fn(),
  },
}));

// Mock lib/supabase
jest.mock("@/lib/supabase", () => ({
  supabase: {
    auth: {
      getUser: jest.fn(() => Promise.resolve({ data: { user: { id: "test-user" } } })),
      getSession: jest.fn(() => Promise.resolve({ data: { session: { access_token: "token" } } })),
    },
  },
}));

describe("SnapPage Integration", () => {
  it("navigates through the capture flow", () => {
    const queryClient = new QueryClient();
    render(
      <QueryClientProvider client={queryClient}>
        <SnapPage />
      </QueryClientProvider>,
    );

    // 1. Initial State: Camera Capture
    const captureBtn = screen.getByText("Capture");
    expect(captureBtn).toBeInTheDocument();
    expect(screen.queryByText("Image Preview")).not.toBeInTheDocument();

    // 2. Capture Image -> Preview State
    fireEvent.click(captureBtn);
    expect(screen.getByText("Image Preview")).toBeInTheDocument();
    expect(screen.queryByText("Capture")).not.toBeInTheDocument();

    // 3. Confirm Image -> Record State
    const confirmBtn = screen.getByText("Confirm");
    fireEvent.click(confirmBtn);

    // Check for Record step elements
    expect(screen.getByText("What's in this meal?")).toBeInTheDocument();
    expect(screen.getByText("Record Voice")).toBeInTheDocument();
    expect(screen.queryByText("Image Preview")).not.toBeInTheDocument();

    // 4. Record Voice -> Complete (Console log check not practical, but flow ends here for now)
    const recordBtn = screen.getByText("Record Voice");
    fireEvent.click(recordBtn);
    // Verified it renders and is clickable
  });

  it("allows retaking photo", () => {
    const queryClient = new QueryClient();
    render(
      <QueryClientProvider client={queryClient}>
        <SnapPage />
      </QueryClientProvider>,
    );

    // Capture
    fireEvent.click(screen.getByText("Capture"));
    expect(screen.getByText("Image Preview")).toBeInTheDocument();

    // Retake
    fireEvent.click(screen.getByText("Retake"));
    expect(screen.getByText("Capture")).toBeInTheDocument();
    expect(screen.queryByText("Image Preview")).not.toBeInTheDocument();
    expect(screen.getByText("Capture")).toBeInTheDocument();
    expect(screen.queryByText("Image Preview")).not.toBeInTheDocument();
  });

  it("opens text entry modal when keyboard icon is clicked", () => {
    const queryClient = new QueryClient();
    render(
      <QueryClientProvider client={queryClient}>
        <SnapPage />
      </QueryClientProvider>,
    );

    // Initial state (Capture)
    const keyboardBtn = screen.getByLabelText("Open text entry");
    expect(keyboardBtn).toBeInTheDocument();

    // Open Modal
    fireEvent.click(keyboardBtn);
    expect(screen.getByRole("dialog")).toHaveTextContent("Text Entry Modal");

    // Close Modal
    fireEvent.click(screen.getByText("Close"));
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });
});
