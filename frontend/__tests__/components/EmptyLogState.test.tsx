import "@testing-library/jest-dom";
import { render, screen } from "@testing-library/react";
import { EmptyLogState } from "@/components/features/logs/EmptyLogState";

describe("EmptyLogState", () => {
  it("renders empty state message", () => {
    render(<EmptyLogState />);
    expect(screen.getByText("No meals logged yet today")).toBeInTheDocument();
  });

  it("renders call-to-action button linking to snap page", () => {
    render(<EmptyLogState />);
    const link = screen.getByRole("link", { name: /log a meal/i });
    expect(link).toBeInTheDocument();
    expect(link).toHaveAttribute("href", "/snap");
  });

  it("renders encouragement text", () => {
    render(<EmptyLogState />);
    expect(screen.getByText(/capture your first meal/i)).toBeInTheDocument();
  });
});
