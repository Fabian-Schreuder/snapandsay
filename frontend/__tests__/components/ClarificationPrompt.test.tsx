import "@testing-library/jest-dom";
import { render, screen, fireEvent, act } from "@testing-library/react";
import {
  ClarificationPrompt,
  ClarificationAnswer,
} from "@/components/features/analysis/ClarificationPrompt";

// Mock VoiceCaptureButton
jest.mock("@/components/features/voice/VoiceCaptureButton", () => ({
  VoiceCaptureButton: ({
    onRecordingComplete,
  }: {
    onRecordingComplete: (blob: Blob) => void;
  }) => (
    <button
      data-testid="voice-capture-button"
      onClick={() => onRecordingComplete(new Blob())}
    >
      Hold to speak
    </button>
  ),
}));

// Mock upload service
jest.mock("@/services/upload-service", () => ({
  uploadFile: jest.fn().mockResolvedValue(undefined),
  generateUploadPath: jest.fn().mockReturnValue("audio/test.webm"),
}));

// Mock supabase
jest.mock("@/lib/supabase", () => ({
  supabase: {
    auth: {
      getUser: jest.fn().mockResolvedValue({
        data: { user: { id: "test-user-id" } },
      }),
    },
  },
}));

// Mock timers for countdown
jest.useFakeTimers();

describe("ClarificationPrompt", () => {
  const mockOnSubmitAll = jest.fn();
  const mockOnSkip = jest.fn();

  const singleQuestionProps = {
    questions: [
      {
        item_name: "Portion",
        question: "How big was the portion?",
        options: ["Small", "Medium", "Large"],
      },
    ],
    timeoutSeconds: 30,
    onSubmitAll: mockOnSubmitAll,
    onSkip: mockOnSkip,
  };

  const multiQuestionProps = {
    questions: [
      {
        item_name: "Burger",
        question: "What kind of burger?",
        options: ["Beef", "Veggie"],
      },
      {
        item_name: "Milk",
        question: "What kind of milk?",
        options: ["Whole", "Skim"],
      },
    ],
    timeoutSeconds: 30,
    onSubmitAll: mockOnSubmitAll,
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

  it("renders question and options", () => {
    render(<ClarificationPrompt {...singleQuestionProps} />);

    expect(screen.getByText("How big was the portion?")).toBeInTheDocument();
    expect(screen.getByText("Small")).toBeInTheDocument();
    expect(screen.getByText("Medium")).toBeInTheDocument();
    expect(screen.getByText("Large")).toBeInTheDocument();
  });

  it("calls onSubmitAll with answer when single-question option clicked", () => {
    render(<ClarificationPrompt {...singleQuestionProps} />);

    fireEvent.click(screen.getByText("Medium"));

    expect(mockOnSubmitAll).toHaveBeenCalledWith([
      { item_name: "Portion", response: "Medium" },
    ]);
  });

  it("shows voice capture button by default", () => {
    render(<ClarificationPrompt {...singleQuestionProps} />);

    expect(screen.getByTestId("voice-capture-button")).toBeInTheDocument();
  });

  it('shows text input when "Type instead" is clicked', () => {
    render(<ClarificationPrompt {...singleQuestionProps} />);

    fireEvent.click(screen.getByText("Type answer instead"));

    expect(
      screen.getByPlaceholderText("Type your answer..."),
    ).toBeInTheDocument();
  });

  it("calls onSubmitAll when text is submitted for single question", () => {
    render(<ClarificationPrompt {...singleQuestionProps} />);

    // Switch to text input
    fireEvent.click(screen.getByText("Type answer instead"));

    const input = screen.getByPlaceholderText("Type your answer...");
    fireEvent.change(input, { target: { value: "About half a cup" } });
    fireEvent.click(screen.getByRole("button", { name: /send/i }));

    expect(mockOnSubmitAll).toHaveBeenCalledWith([
      { item_name: "Portion", response: "About half a cup" },
    ]);
  });

  it("submits on Enter key press in text input", () => {
    render(<ClarificationPrompt {...singleQuestionProps} />);

    // Switch to text input
    fireEvent.click(screen.getByText("Type answer instead"));

    const input = screen.getByPlaceholderText("Type your answer...");
    fireEvent.change(input, { target: { value: "Two slices" } });
    fireEvent.keyDown(input, { key: "Enter" });

    expect(mockOnSubmitAll).toHaveBeenCalledWith([
      { item_name: "Portion", response: "Two slices" },
    ]);
  });

  it("does not submit empty text", () => {
    render(<ClarificationPrompt {...singleQuestionProps} />);

    // Switch to text input
    fireEvent.click(screen.getByText("Type answer instead"));

    const sendButton = screen.getByRole("button", { name: /send/i });
    expect(sendButton).toBeDisabled();
  });

  it("shows skip button when remaining time is 10 seconds or less", () => {
    render(<ClarificationPrompt {...singleQuestionProps} />);

    // Initial render - skip button should not be visible
    expect(screen.queryByText(/Taking too long/i)).not.toBeInTheDocument();

    // Advance timer to 21 seconds (9 seconds remaining)
    act(() => {
      jest.advanceTimersByTime(21000);
    });

    expect(screen.getByText(/Taking too long/i)).toBeInTheDocument();
  });

  it("calls onSkip when skip button is clicked", () => {
    render(<ClarificationPrompt {...singleQuestionProps} />);

    // Advance to show skip button
    act(() => {
      jest.advanceTimersByTime(21000);
    });

    fireEvent.click(screen.getByText(/Taking too long/i));

    expect(mockOnSkip).toHaveBeenCalledTimes(1);
  });

  it("renders with empty options", () => {
    render(
      <ClarificationPrompt
        {...singleQuestionProps}
        questions={[
          {
            item_name: "Portion",
            question: "How big was the portion?",
            options: [],
          },
        ]}
      />,
    );

    expect(screen.getByText("How big was the portion?")).toBeInTheDocument();
    expect(screen.queryByText("Small")).not.toBeInTheDocument();
  });

  // --- Multi-page tests ---

  it("shows progress indicator for multi-question", () => {
    render(<ClarificationPrompt {...multiQuestionProps} />);

    expect(screen.getByText("1/2")).toBeInTheDocument();
    expect(screen.getByText("What kind of burger?")).toBeInTheDocument();
  });

  it("advances to next question on option click without submitting", () => {
    render(<ClarificationPrompt {...multiQuestionProps} />);

    // Answer first question
    fireEvent.click(screen.getByText("Beef"));

    // Should NOT have submitted yet
    expect(mockOnSubmitAll).not.toHaveBeenCalled();

    // Should now show second question
    expect(screen.getByText("What kind of milk?")).toBeInTheDocument();
    expect(screen.getByText("2/2")).toBeInTheDocument();
  });

  it("submits all answers after last question", () => {
    render(<ClarificationPrompt {...multiQuestionProps} />);

    // Answer first question
    fireEvent.click(screen.getByText("Beef"));

    // Answer second question
    fireEvent.click(screen.getByText("Skim"));

    // Should have submitted both answers
    expect(mockOnSubmitAll).toHaveBeenCalledWith([
      { item_name: "Burger", response: "Beef" },
      { item_name: "Milk", response: "Skim" },
    ]);
  });

  it("does not show progress indicator for single question", () => {
    render(<ClarificationPrompt {...singleQuestionProps} />);

    expect(screen.queryByText("1/1")).not.toBeInTheDocument();
  });
});
