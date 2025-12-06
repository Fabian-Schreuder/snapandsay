import { render, screen, fireEvent } from '@testing-library/react'
import CameraCapture from '../components/features/camera/CameraCapture'
import '@testing-library/jest-dom'

// Mock react-webcam
jest.mock('react-webcam', () => {
    const React = require('react');
    return {
        __esModule: true,
        default: React.forwardRef((props: any, ref: any) => {
             React.useImperativeHandle(ref, () => ({
                getScreenshot: () => 'data:image/jpeg;base64,fakeimage'
             }));
             return <div data-testid="webcam-mock">Webcam Mock</div>;
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

    it('captures image when shutter button is clicked', () => {
        const onCaptureMock = jest.fn()
        render(<CameraCapture onCapture={onCaptureMock} />)
        
        const shutterBtn = screen.getByRole('button', { name: /shutter/i })
        fireEvent.click(shutterBtn)
        
        expect(onCaptureMock).toHaveBeenCalledWith('data:image/jpeg;base64,fakeimage')
    })
})
