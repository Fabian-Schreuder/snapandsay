import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import SnapPage from '../app/(dashboard)/snap/page';
import { analysisApi } from '../lib/api';
import * as uploadService from '../services/upload-service';
import { supabase } from '../lib/supabase';
import { useRouter } from 'next/navigation';

// Mock dependencies
// jest.mock('next/navigation'); // handled in jest.setup.ts
jest.mock('../lib/api');
jest.mock('../services/upload-service');
jest.mock('../lib/supabase', () => ({
  supabase: {
    auth: {
      getUser: jest.fn()
    }
  }
}));
jest.mock('@/components/features/camera/CameraCapture', () => {
    return function MockCameraCapture({ onCapture }: any) {
        return <button onClick={() => onCapture('data:image/jpeg;base64,fake')}>Capture Photo</button>
    }
});
jest.mock('@/components/features/camera/ImagePreview', () => {
    return function MockImagePreview({ onConfirm }: any) {
        return <button onClick={onConfirm}>Confirm Photo</button>
    }
});
jest.mock('@/components/features/voice/VoiceCaptureButton', () => ({
    VoiceCaptureButton: function MockVoiceCaptureButton({ onRecordingComplete }: any) {
        return <button onClick={() => onRecordingComplete(new Blob(['audio'], { type: 'audio/webm' }))}>Finish Recording</button>
    }
}));

describe('SnapPage Upload Flow', () => {
  const mockPush = jest.fn();
  const queryClient = new QueryClient();

  const renderWithProviders = (ui: React.ReactNode) => {
    return render(
      <QueryClientProvider client={queryClient}>
        {ui}
      </QueryClientProvider>
    );
  };
  
  beforeEach(() => {
    jest.clearAllMocks();
    (useRouter as jest.Mock).mockReturnValue({ push: mockPush });
    (supabase.auth.getUser as jest.Mock).mockResolvedValue({ 
        data: { user: { id: 'test-user-id' } }, 
        error: null 
    });
    (uploadService.uploadFile as jest.Mock).mockResolvedValue('path/to/file');
    (uploadService.generateUploadPath as jest.Mock).mockImplementation((uid, type) => `${uid}/mock_${type}`);
    (analysisApi.upload as jest.Mock).mockResolvedValue({ log_id: '123', status: 'processing' });
    
    // Mock global fetch
    global.fetch = jest.fn((url: string | Request) => {
        if (typeof url === 'string' && url.includes('/api/v1/analysis/stream')) {
             return Promise.resolve({
                ok: true,
                status: 200,
                headers: new Headers(),
                body: {
                    getReader: () => ({
                        read: jest.fn()
                            .mockResolvedValueOnce({ 
                                done: false, 
                                value: new TextEncoder().encode('event: complete\ndata: {"summary": "Done"}\n\n') 
                            })
                            .mockResolvedValueOnce({ done: true })
                    })
                }
            });
        }
        return Promise.resolve({
            ok: true,
            status: 200,
            blob: () => Promise.resolve(new Blob(['fake-image'], { type: 'image/jpeg' }))
        });
    }) as jest.Mock;
    
    // Mock global alert (though unused now, keep just in case of regressions)
    global.alert = jest.fn();
  });

  it('completes the full flow: capture -> confirm -> record -> upload', async () => {
    renderWithProviders(<SnapPage />);

    // 1. Capture
    fireEvent.click(screen.getByText('Capture Photo'));
    
    // 2. Confirm
    fireEvent.click(screen.getByText('Confirm Photo'));
    
    // 3. Record & Upload
    fireEvent.click(screen.getByText('Finish Recording'));

    // Verify "Thinking" state appears
    await waitFor(() => {
        expect(supabase.auth.getUser).toHaveBeenCalled();
    });

    // Verify uploads
    expect(uploadService.uploadFile).toHaveBeenCalledTimes(2); // Image + Audio
    expect(uploadService.uploadFile).toHaveBeenCalledWith('raw_uploads', 'test-user-id/mock_image', expect.any(Blob));
    expect(uploadService.uploadFile).toHaveBeenCalledWith('raw_uploads', 'test-user-id/mock_audio', expect.any(Blob));

    // Verify API call
    expect(analysisApi.upload).toHaveBeenCalledWith({
        image_path: 'test-user-id/mock_image',
        audio_path: 'test-user-id/mock_audio',
        client_timestamp: expect.any(String)
    });

    // Verify Success Handling (Router push)
    await waitFor(() => {
       expect(mockPush).toHaveBeenCalledWith('/');
    }, { timeout: 3000 }); // Increase timeout for the 1500ms delay in component
  });

  it('handles upload errors gracefully', async () => {
    (analysisApi.upload as jest.Mock).mockRejectedValue(new Error('API Error'));

    renderWithProviders(<SnapPage />);

    // Fast forward to upload
    fireEvent.click(screen.getByText('Capture Photo'));
    fireEvent.click(screen.getByText('Confirm Photo'));
    fireEvent.click(screen.getByText('Finish Recording'));

    await waitFor(() => {
        expect(screen.getByText("We couldn't save that. Please try again.")).toBeInTheDocument();
    });

    expect(global.alert).not.toHaveBeenCalled();
    expect(mockPush).not.toHaveBeenCalled();
  });
});
