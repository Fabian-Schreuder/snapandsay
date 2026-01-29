import "@testing-library/jest-dom";
import { render, screen } from "@testing-library/react";
import { ThinkingIndicator } from "@/components/features/analysis/ThinkingIndicator";

describe("ThinkingIndicator", () => {
  it("should not render when status is idle", () => {
    const { container } = render(
      <ThinkingIndicator thoughts={[]} status="idle" />,
    );

    expect(container.firstChild).toBeNull();
  });

  it("should render with connecting status", () => {
    render(<ThinkingIndicator thoughts={[]} status="connecting" />);

    expect(screen.getByRole("status")).toBeInTheDocument();
    expect(screen.getByText("Connecting...")).toBeInTheDocument();
  });

  it("should render with streaming status and thoughts", () => {
    const thoughts = ["Looking at your meal...", "Identifying ingredients..."];

    render(<ThinkingIndicator thoughts={thoughts} status="streaming" />);

    expect(screen.getByRole("status")).toBeInTheDocument();
    expect(screen.getByText("Looking at your meal...")).toBeInTheDocument();
    expect(screen.getByText("Identifying ingredients...")).toBeInTheDocument();
  });

  it("should render completion state with checkmark", () => {
    render(<ThinkingIndicator thoughts={["Done!"]} status="complete" />);

    expect(screen.getByRole("status")).toBeInTheDocument();
    // Check for completion screen reader text
    expect(
      screen.getByText("Analysis complete. Your meal has been logged."),
    ).toBeInTheDocument();
  });

  it("should render error state", () => {
    render(<ThinkingIndicator thoughts={[]} status="error" />);

    expect(screen.getByRole("status")).toBeInTheDocument();
  });

  it("should have correct aria-label for processing", () => {
    render(<ThinkingIndicator thoughts={[]} status="streaming" />);

    expect(screen.getByRole("status")).toHaveAttribute(
      "aria-label",
      "AI is analyzing your meal",
    );
  });

  it("should have correct aria-label for complete", () => {
    render(<ThinkingIndicator thoughts={[]} status="complete" />);

    expect(screen.getByRole("status")).toHaveAttribute(
      "aria-label",
      "Analysis complete",
    );
  });

  it("should have correct aria-label for error", () => {
    render(<ThinkingIndicator thoughts={[]} status="error" />);

    expect(screen.getByRole("status")).toHaveAttribute(
      "aria-label",
      "An error occurred",
    );
  });

  it("should accept custom className", () => {
    render(
      <ThinkingIndicator
        thoughts={[]}
        status="streaming"
        className="custom-class"
      />,
    );

    expect(screen.getByRole("status")).toHaveClass("custom-class");
  });
});
