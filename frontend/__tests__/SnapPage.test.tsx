import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import SnapPage from '../app/(dashboard)/snap/page'
import '@testing-library/jest-dom'

// Mock sub-components
jest.mock('../components/features/camera/CameraCapture', () => ({
    __esModule: true,
    default: ({ onCapture }: { onCapture: (src: string) => void }) => (
        <div data-testid="camera-capture">
            <button onClick={() => onCapture("data:fake-image")}>Snap</button>
        </div>
    )
}));

jest.mock('../components/features/camera/ImagePreview', () => ({
    __esModule: true,
    default: ({ onRetake, onConfirm }: { onRetake: () => void, onConfirm: () => void }) => (
        <div data-testid="image-preview">
            <button onClick={onRetake}>Retake</button>
            <button onClick={onConfirm}>Confirm</button>
        </div>
    )
}));

describe('SnapPage', () => {
    it('shows camera capture by default', () => {
        render(<SnapPage />)
        expect(screen.getByTestId('camera-capture')).toBeInTheDocument()
        expect(screen.queryByTestId('image-preview')).not.toBeInTheDocument()
    })

    it('transitions to preview on capture', async () => {
        render(<SnapPage />)
        
        // Find "Snap" button from mock and click it
        fireEvent.click(screen.getByText('Snap'))

        await waitFor(() => {
             expect(screen.getByTestId('image-preview')).toBeInTheDocument()
             expect(screen.queryByTestId('camera-capture')).not.toBeInTheDocument()
        })
    })

    it('returns to camera on retake', async () => {
        render(<SnapPage />)
        
        // Capture first
        fireEvent.click(screen.getByText('Snap'))
        await screen.findByTestId('image-preview')

        // Click Retake
        fireEvent.click(screen.getByText('Retake'))

        await waitFor(() => {
             expect(screen.getByTestId('camera-capture')).toBeInTheDocument()
             expect(screen.queryByTestId('image-preview')).not.toBeInTheDocument()
        })
    })
})
