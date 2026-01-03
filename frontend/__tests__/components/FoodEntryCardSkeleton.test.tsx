import '@testing-library/jest-dom';
import { render } from '@testing-library/react';
import { FoodEntryCardSkeleton } from '@/components/features/logs/FoodEntryCardSkeleton';

describe('FoodEntryCardSkeleton', () => {
  it('renders skeleton container', () => {
    const { container } = render(<FoodEntryCardSkeleton />);
    expect(container.firstChild).toHaveClass('min-h-[100px]', 'rounded-xl');
  });

  it('renders thumbnail skeleton', () => {
    const { container } = render(<FoodEntryCardSkeleton />);
    // Thumbnail skeleton should be 80x80
    const thumbnailSkeleton = container.querySelector('.h-20.w-20');
    expect(thumbnailSkeleton).toBeInTheDocument();
  });

  it('renders content skeletons', () => {
    const { container } = render(<FoodEntryCardSkeleton />);
    // Should have multiple skeleton elements for text content
    const skeletons = container.querySelectorAll('[class*="animate-pulse"], [class*="bg-"]');
    expect(skeletons.length).toBeGreaterThan(0);
  });

  it('renders badge skeleton', () => {
    const { container } = render(<FoodEntryCardSkeleton />);
    // Badge skeleton should be rounded-full
    const badgeSkeleton = container.querySelector('.rounded-full');
    expect(badgeSkeleton).toBeInTheDocument();
  });
});
