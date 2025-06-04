import { vi } from 'vitest';
import fs from 'fs';
import path from 'path';

export const loadTestFile = (fileName: string): File => {
  const filePath = path.join(process.cwd(), 'test', 'test_files', fileName);
  const content = fs.readFileSync(filePath, 'utf-8');
  const fileType = fileName.endsWith('.xlsx') 
    ? 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    : 'text/csv';
  return new File([content], fileName, { type: fileType });
};

export const mockFileReader = () => {
  const mockReadAsText = vi.fn();
  const mockReadAsArrayBuffer = vi.fn();
  
  global.FileReader = vi.fn().mockImplementation(() => ({
    readAsText: mockReadAsText,
    readAsArrayBuffer: mockReadAsArrayBuffer,
    result: null,
    onload: null,
    onerror: null
  }));

  return {
    mockReadAsText,
    mockReadAsArrayBuffer
  };
};

export const mockFileSystem = () => {
  const mockFiles = new Map<string, File>();
  
  return {
    addFile: (file: File) => {
      mockFiles.set(file.name, file);
    },
    getFile: (name: string) => mockFiles.get(name),
    getAllFiles: () => Array.from(mockFiles.values()),
    clearFiles: () => mockFiles.clear()
  };
}; 