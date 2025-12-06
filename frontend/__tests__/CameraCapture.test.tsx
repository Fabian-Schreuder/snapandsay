import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import CameraCapture from '../components/features/camera/CameraCapture'
import '@testing-library/jest-dom'

// Mock react-webcam
jest.mock('react-webcam', () => {
    const React = require('react');
    return {
        __esModule: true,
        default: React.forwardRef((props: any, ref: any) => {
             // Expose a way to trigger error from outside if needed, 
             // or just check that the props are passed correctly.
             // We can also render a buttons to trigger the props for testing.
             return (
                 <div data-testid="webcam-mock">
                     <button onClick={() => props.onUserMediaError && props.onUserMediaError('Permission denied')}>Trigger Error</button>
                     <button onClick={() => ref.current = { getScreenshot: () => 'data:image/jpeg;base64,fakeimage' }}>Init Ref</button>
                 </div>
             );
        })
    }
});

describe('CameraCapture', () => {
    it('renders the webcam', () => {
        render(<CameraCapture onCapture={jest.fn()} />)
        expect(screen.getByTestId('webcam-mock')).toBeInTheDocument()
    })
    
    it('renders the shutter button', () => {
        render(<CameraCapture onCapture={jest.fn()} />)
        expect(screen.getByRole('button', { name: /shutter/i })).toBeInTheDocument()
    })

    // This test is tricky with the mock above because ref interaction is complex in mocks. 
    // We'll skip deep functional testing of the external library and focus on our logic.
    // The key thing we added is error handling.

    it('shows error UI when camera permission is denied', async () => {
        render(<CameraCapture onCapture={jest.fn()} />)
        
        // Find the trigger button from our mock
        fireEvent.click(screen.getByText('Trigger Error'))

        await waitFor(() => {
            expect(screen.getByText(/Camera Access Needed/i)).toBeInTheDocument()
            expect(screen.getByText(/We need camera access/i)).toBeInTheDocument()
        })
    })

    it('renders retry button in error state', async () => {
         render(<CameraCapture onCapture={jest.fn()} />)
         fireEvent.click(screen.getByText('Trigger Error'))
         
         await waitFor(() => {
             expect(screen.getByRole('button', { name: /Try Again/i })).toBeInTheDocument()
         })
    })
})
