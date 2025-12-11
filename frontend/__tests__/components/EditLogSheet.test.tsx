import '@testing-library/jest-dom';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { EditLogSheet } from '@/components/features/logs/EditLogSheet';
import { useUpdateLog } from '@/hooks/use-logs';
import type { DietaryLog } from '@/types/log';

// Mock the hooks
jest.mock('@/hooks/use-logs', () => ({
  useUpdateLog: jest.fn(),
}));

// Mock Radix UI Sheet components
jest.mock('@/components/ui/sheet', () => ({
  Sheet: ({ children, open }: { children: React.ReactNode; open: boolean }) =>
    open ? <div data-testid="sheet">{children}</div> : null,
  SheetContent: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="sheet-content">{children}</div>
  ),
  SheetHeader: ({ children }: { children: React.ReactNode }) => (
    <div>{children}</div>
  ),
  SheetTitle: ({ children }: { children: React.ReactNode }) => (
    <h2>{children}</h2>
  ),
  SheetDescription: ({ children }: { children: React.ReactNode }) => (
    <p>{children}</p>
  ),
}));

const mockLog: DietaryLog = {
  id: 'log-123',
  image_path: 'user123/meal.jpg',
  transcript: 'Chicken salad',
  description: 'A healthy chicken salad with greens',
  calories: 350,
  protein: 30,
  carbs: 15,
  fats: 18,
  needs_review: false,
  created_at: '2024-01-15T12:30:00Z',
  user_id: 'user-123',
  status: 'completed',
  title: 'Test Meal Title',
};

describe('EditLogSheet', () => {
  const mockOnOpenChange = jest.fn();
  const mockMutate = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    (useUpdateLog as jest.Mock).mockReturnValue({
      mutate: mockMutate,
      isPending: false,
    });
  });

  it('renders sheet with form fields when open', () => {
    render(
      <EditLogSheet log={mockLog} open={true} onOpenChange={mockOnOpenChange} />
    );

    expect(screen.getByText('Edit Meal')).toBeInTheDocument();
    expect(screen.getByLabelText('Description')).toBeInTheDocument();
    expect(screen.getByLabelText('Calories')).toBeInTheDocument();
    expect(screen.getByLabelText('Protein (g)')).toBeInTheDocument();
    expect(screen.getByLabelText('Carbs (g)')).toBeInTheDocument();
    expect(screen.getByLabelText('Fats (g)')).toBeInTheDocument();
  });

  it('does not render when closed', () => {
    render(
      <EditLogSheet log={mockLog} open={false} onOpenChange={mockOnOpenChange} />
    );

    expect(screen.queryByText('Edit Meal')).not.toBeInTheDocument();
  });

  it('populates form fields with log data', () => {
    render(
      <EditLogSheet log={mockLog} open={true} onOpenChange={mockOnOpenChange} />
    );

    expect(screen.getByLabelText('Description')).toHaveValue(mockLog.description);
    expect(screen.getByLabelText('Calories')).toHaveValue(mockLog.calories);
    expect(screen.getByLabelText('Protein (g)')).toHaveValue(mockLog.protein);
    expect(screen.getByLabelText('Carbs (g)')).toHaveValue(mockLog.carbs);
    expect(screen.getByLabelText('Fats (g)')).toHaveValue(mockLog.fats);
  });

  it('cancel button calls onOpenChange with false', () => {
    render(
      <EditLogSheet log={mockLog} open={true} onOpenChange={mockOnOpenChange} />
    );

    const cancelButton = screen.getByRole('button', { name: /cancel/i });
    fireEvent.click(cancelButton);

    expect(mockOnOpenChange).toHaveBeenCalledWith(false);
  });

  it('save button is disabled when form has no changes', () => {
    render(
      <EditLogSheet log={mockLog} open={true} onOpenChange={mockOnOpenChange} />
    );

    const saveButton = screen.getByRole('button', { name: /save/i });
    expect(saveButton).toBeDisabled();
  });

  it('save button is enabled when form has changes', async () => {
    render(
      <EditLogSheet log={mockLog} open={true} onOpenChange={mockOnOpenChange} />
    );

    const descriptionInput = screen.getByLabelText('Description');
    fireEvent.change(descriptionInput, { target: { value: 'Updated description' } });

    const saveButton = screen.getByRole('button', { name: /save/i });
    expect(saveButton).not.toBeDisabled();
  });

  it('calls updateLog.mutate when save is clicked with changes', async () => {
    render(
      <EditLogSheet log={mockLog} open={true} onOpenChange={mockOnOpenChange} />
    );

    const caloriesInput = screen.getByLabelText('Calories');
    fireEvent.change(caloriesInput, { target: { value: '400' } });

    const saveButton = screen.getByRole('button', { name: /save/i });
    fireEvent.click(saveButton);

    expect(mockMutate).toHaveBeenCalledWith(
      { logId: 'log-123', data: { calories: 400 } },
      expect.any(Object)
    );
  });

  it('shows loading state when saving', () => {
    (useUpdateLog as jest.Mock).mockReturnValue({
      mutate: mockMutate,
      isPending: true,
    });

    render(
      <EditLogSheet log={mockLog} open={true} onOpenChange={mockOnOpenChange} />
    );

    // Change something to enable save button
    const descriptionInput = screen.getByLabelText('Description');
    fireEvent.change(descriptionInput, { target: { value: 'Changed' } });

    expect(screen.getByText('Saving...')).toBeInTheDocument();
  });
});
