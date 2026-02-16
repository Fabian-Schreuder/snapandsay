import "@testing-library/jest-dom";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
// @ts-ignore - Component doesn't exist yet
import { TextEntryModal } from "@/components/features/input/TextEntryModal";

// Mock the useAgent hook
const mockSubmitText = jest.fn();
jest.mock("@/hooks/use-agent", () => ({
    useAgent: () => ({
        submitText: mockSubmitText,
        isProcessing: false,
    }),
}));

describe("TextEntryModal", () => {
    const defaultProps = {
        isOpen: true,
        onClose: jest.fn(),
    };

    beforeEach(() => {
        mockSubmitText.mockClear();
        defaultProps.onClose.mockClear();
    });

    it("should render when open", () => {
        render(<TextEntryModal {...defaultProps} />);
        // Dialog content usually has a role of dialog or alertdialog
        expect(screen.getByRole("dialog")).toBeInTheDocument();
        expect(screen.getByPlaceholderText(/Type what you ate/i)).toBeInTheDocument();
    });

    it("should not render when closed", () => {
        render(<TextEntryModal {...defaultProps} isOpen={false} />);
        expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    });

    it("should submit text when button is clicked", async () => {
        render(<TextEntryModal {...defaultProps} />);

        const input = screen.getByPlaceholderText(/Type what you ate/i);
        const submitBtn = screen.getByRole("button", { name: /log meal/i });

        fireEvent.change(input, { target: { value: "Grilled Cheese" } });
        fireEvent.click(submitBtn);

        await waitFor(() => {
            expect(mockSubmitText).toHaveBeenCalledWith("Grilled Cheese");
        });
        expect(defaultProps.onClose).toHaveBeenCalled();
    });

    it("should not submit empty text", async () => {
        render(<TextEntryModal {...defaultProps} />);

        const submitBtn = screen.getByRole("button", { name: /log meal/i });
        fireEvent.click(submitBtn);

        expect(mockSubmitText).not.toHaveBeenCalled();
    });
});
