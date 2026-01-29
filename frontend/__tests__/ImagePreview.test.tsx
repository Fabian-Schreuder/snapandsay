import { render, screen, fireEvent } from "@testing-library/react";
import ImagePreview from "../components/features/camera/ImagePreview";
import "@testing-library/jest-dom";

describe("ImagePreview", () => {
  const mockImageSrc = "data:image/jpeg;base64,testimage";
  const mockOnRetake = jest.fn();
  const mockOnConfirm = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("displays the captured image", () => {
    render(
      <ImagePreview
        imageSrc={mockImageSrc}
        onRetake={mockOnRetake}
        onConfirm={mockOnConfirm}
      />,
    );
    const img = screen.getByRole("img", { name: /captured/i });
    expect(img).toBeInTheDocument();
    expect(img).toHaveAttribute("src", mockImageSrc);
  });

  it("calls onRetake when retake button is clicked", () => {
    render(
      <ImagePreview
        imageSrc={mockImageSrc}
        onRetake={mockOnRetake}
        onConfirm={mockOnConfirm}
      />,
    );
    const retakeBtn = screen.getByRole("button", { name: /retake/i }); // Case insensitive match for Retake/X/Cancel
    fireEvent.click(retakeBtn);
    expect(mockOnRetake).toHaveBeenCalled();
  });

  it("calls onConfirm when confirm button is clicked", () => {
    render(
      <ImagePreview
        imageSrc={mockImageSrc}
        onRetake={mockOnRetake}
        onConfirm={mockOnConfirm}
      />,
    );
    const confirmBtn = screen.getByRole("button", {
      name: /confirm|next|check/i,
    });
    fireEvent.click(confirmBtn);
    expect(mockOnConfirm).toHaveBeenCalled();
  });
});
