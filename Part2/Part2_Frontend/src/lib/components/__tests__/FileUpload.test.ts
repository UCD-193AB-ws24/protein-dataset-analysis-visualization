import { render, fireEvent } from '@testing-library/svelte';
import { describe, it, expect, vi } from 'vitest';
import UploadModal from '../UploadModal.svelte';
import { loadTestFile, mockFileReader, mockFileSystem } from '../../../test/utils/fileUtils';

describe('UploadModal', () => {
  const fileSystem = mockFileSystem();
  const { mockReadAsText, mockReadAsArrayBuffer } = mockFileReader();

  beforeEach(() => {
    fileSystem.clearFiles();
    vi.clearAllMocks();
  });

  it('renders upload buttons', () => {
    const { getByText } = render(UploadModal);
    expect(getByText('Upload Matrix File')).toBeInTheDocument();
    expect(getByText('Upload Coordinate File')).toBeInTheDocument();
  });

  it('handles matrix file selection', async () => {
    const { getByLabelText, getByText } = render(UploadModal);
    const file = loadTestFile('chr7_domain1_matrix1_tir.csv');
    fileSystem.addFile(file);
    
    const input = getByLabelText('Upload Matrix File');
    await fireEvent.change(input, { target: { files: [file] } });
    
    expect(mockReadAsArrayBuffer).toHaveBeenCalledWith(file);
    expect(getByText('Matrix file uploaded')).toBeInTheDocument();
  });

  it('handles coordinate file selection', async () => {
    const { getByLabelText, getByText } = render(UploadModal);
    const file = loadTestFile('chr7_coordinates1.csv');
    fileSystem.addFile(file);
    
    const input = getByLabelText('Upload Coordinate File');
    await fireEvent.change(input, { target: { files: [file] } });
    
    expect(mockReadAsArrayBuffer).toHaveBeenCalledWith(file);
    expect(getByText('Coordinate file uploaded')).toBeInTheDocument();
  });

  it('validates file types', async () => {
    const { getByLabelText, getByText } = render(UploadModal);
    const invalidFiles = [
      loadTestFile('invalid.txt'),
      loadTestFile('invalid.xlsx')
    ];
    
    invalidFiles.forEach(file => fileSystem.addFile(file));
    
    const input = getByLabelText('Upload Matrix File');
    await fireEvent.change(input, { target: { files: [invalidFiles[0]] } });
    expect(getByText('Invalid file type')).toBeInTheDocument();
    
    await fireEvent.change(input, { target: { files: [invalidFiles[1]] } });
    expect(getByText('Invalid file type')).toBeInTheDocument();
  });

  it('handles multiple file uploads', async () => {
    const { getByLabelText, getByText } = render(UploadModal);
    const matrixFile = loadTestFile('chr7_domain1_matrix1_tir.csv');
    const coordFile = loadTestFile('chr7_coordinates1.csv');
    
    fileSystem.addFile(matrixFile);
    fileSystem.addFile(coordFile);
    
    const matrixInput = getByLabelText('Upload Matrix File');
    const coordInput = getByLabelText('Upload Coordinate File');
    
    await fireEvent.change(matrixInput, { target: { files: [matrixFile] } });
    await fireEvent.change(coordInput, { target: { files: [coordFile] } });
    
    expect(getByText('Matrix file uploaded')).toBeInTheDocument();
    expect(getByText('Coordinate file uploaded')).toBeInTheDocument();
  });

  it('handles domain-specific matrix uploads', async () => {
    const { getByLabelText, getByText } = render(UploadModal);
    const domainFiles = [
      loadTestFile('chr7_domain1_matrix1_tir.csv'),
      loadTestFile('chr7_domain2_matrix1_nbs.csv'),
      loadTestFile('chr7_domain3_matrix1_lrr.csv')
    ];
    
    domainFiles.forEach(file => fileSystem.addFile(file));
    
    const input = getByLabelText('Upload Matrix File');
    for (const file of domainFiles) {
      await fireEvent.change(input, { target: { files: [file] } });
      expect(mockReadAsArrayBuffer).toHaveBeenCalledWith(file);
      expect(getByText('Matrix file uploaded')).toBeInTheDocument();
    }
  });

  it('handles file read errors', async () => {
    const { getByLabelText, getByText } = render(UploadModal);
    const file = loadTestFile('chr7_domain1_matrix1_tir.csv');
    fileSystem.addFile(file);
    
    // Simulate file read error
    mockReadAsArrayBuffer.mockImplementationOnce(() => {
      throw new Error('File read error');
    });
    
    const input = getByLabelText('Upload Matrix File');
    await fireEvent.change(input, { target: { files: [file] } });
    
    expect(getByText('Error reading file')).toBeInTheDocument();
  });
}); 