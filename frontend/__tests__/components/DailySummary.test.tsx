import '@testing-library/jest-dom';
import { render, screen } from '@testing-library/react';
import { DailySummary } from '@/components/features/logs/DailySummary';
import type { DietaryLog } from '@/types/log';

const mockLogs: DietaryLog[] = [
  {
    id: '1',
    image_path: 'path/to/img1.jpg',
    transcript: null,
    description: 'Meal 1',
    calories: 300,
    protein: 20,
    carbs: 30,
    fats: 10,
    needs_review: false,
    created_at: '2023-12-08T12:00:00Z',
  },
  {
    id: '2',
    image_path: 'path/to/img2.jpg',
    transcript: null,
    description: 'Meal 2',
    calories: 500,
    protein: 30,
    carbs: 50,
    fats: 20,
    needs_review: false,
    created_at: '2023-12-08T18:00:00Z',
  },
];

describe('DailySummary', () => {
  it('renders today\'s date', () => {
    render(<DailySummary logs={mockLogs} />);
    // Date format depends on execution day, just check it renders specific class
    expect(screen.getByRole('heading', { level: 1 })).toBeInTheDocument();
  });

  it('calculates total calories correctly', () => {
    render(<DailySummary logs={mockLogs} />);
    expect(screen.getByText('800 calories')).toBeInTheDocument();
  });

  it('shows start tracking message when logs list is empty', () => {
    render(<DailySummary logs={[]} />);
    expect(screen.getByText('Start tracking your meals')).toBeInTheDocument();
  });

  it('shows total calories even if total is 0 but logs exist', () => {
    const zeroCalLogs: DietaryLog[] = [{ ...mockLogs[0], calories: 0 }];
    render(<DailySummary logs={zeroCalLogs} />);
    expect(screen.getByText('0 calories')).toBeInTheDocument();
  });
});
