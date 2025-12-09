import '@testing-library/jest-dom';
import { render, screen } from '@testing-library/react';
import { FoodEntryCard } from '@/components/features/logs/FoodEntryCard';
import type { DietaryLog } from '@/types/log';

// Mock next/image
jest.mock('next/image', () => ({
  __esModule: true,
  default: ({ alt, ...props }: { alt: string }) => <img alt={alt} {...props} />,
}));

const mockLog: DietaryLog = {
  id: '123',
  image_path: 'user123/meal.jpg',
  transcript: 'Chicken salad with ranch dressing',
  description: 'A healthy chicken salad',
  calories: 320,
  protein: 25,
  carbs: 15,
  fats: 18,
  needs_review: false,
  created_at: '2024-01-15T12:30:00Z',
  user_id: 'user-123',
  status: 'completed',
};

describe('FoodEntryCard', () => {
  it('renders meal description', () => {
    render(<FoodEntryCard log={mockLog} />);
    expect(screen.getByText('A healthy chicken salad')).toBeInTheDocument();
  });

  it('renders calorie badge', () => {
    render(<FoodEntryCard log={mockLog} />);
    expect(screen.getByText('320 cal')).toBeInTheDocument();
  });

  it('shows transcript when no description', () => {
    const logWithoutDescription = { ...mockLog, description: null };
    render(<FoodEntryCard log={logWithoutDescription} />);
    expect(screen.getByText('Chicken salad with ranch dressing')).toBeInTheDocument();
  });

  it('shows needs review indicator when applicable', () => {
    const logNeedsReview = { ...mockLog, needs_review: true };
    render(<FoodEntryCard log={logNeedsReview} />);
    expect(screen.getByLabelText('Needs review')).toBeInTheDocument();
  });

  it('does not show needs review indicator when not needed', () => {
    render(<FoodEntryCard log={mockLog} />);
    expect(screen.queryByLabelText('Needs review')).not.toBeInTheDocument();
  });

  it('renders time in correct format', () => {
    render(<FoodEntryCard log={mockLog} />);
    // Time display depends on locale, just check it exists
    const timeElement = screen.getByText(/PM|AM/i);
    expect(timeElement).toBeInTheDocument();
  });
});
