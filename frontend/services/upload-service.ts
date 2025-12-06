import { supabase } from '@/lib/supabase';
import { v4 as uuidv4 } from 'uuid';

export const uploadFile = async (
  bucket: string, 
  path: string, 
  file: Blob
): Promise<string> => {
  const { data, error } = await supabase.storage
    .from(bucket)
    .upload(path, file);

  if (error) {
    console.error(`Upload failed for ${path}:`, error);
    throw error;
  }

  return data.path;
};

export const generateUploadPath = (userId: string, type: 'image' | 'audio'): string => {
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  const ext = type === 'image' ? 'jpg' : 'webm';
  return `${userId}/${timestamp}_${type}.${ext}`;
};
