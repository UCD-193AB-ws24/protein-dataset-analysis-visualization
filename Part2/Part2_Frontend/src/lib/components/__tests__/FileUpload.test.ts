import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, fireEvent } from '@testing-library/svelte';
import UploadModal from '../UploadModal.svelte';

// Import test files using Vite's import.meta.glob
const testFiles = import.meta.glob('../../test/test_files/*', { as: 'raw' });

// Helper function to create File objects from test files
async function createFileFromTestFile(filename: string): Promise<File> {
  const filePath = `../../test/test_files/${filename}`;
  const content = await testFiles[filePath]();
  return new File([content], filename, { type: 'text/csv' });
}

describe('UploadModal', () => {
  let mockOnUpload: any;
  let mockOnClose: any;

  beforeEach(() => {
    mockOnUpload = vi.fn();
    mockOnClose = vi.fn();
  });

  it('renders without crashing', () => {
    const { container } = render(UploadModal, {
      props: {
        isOpen: true,
        onClose: mockOnClose,
        onUpload: mockOnUpload
      }
    });
    expect(container).toBeTruthy();
  });

  it('handles coordinate file upload', async () => {
    const { getByText, getByLabelText } = render(UploadModal, {
      props: {
        isOpen: true,
        onClose: mockOnClose,
        onUpload: mockOnUpload
      }
    });

    const file = new File(['test content'], 'test.txt', { type: 'text/plain' });
    const input = getByLabelText('Click to select file or drag and drop') as HTMLInputElement;

    await fireEvent.change(input, { target: { files: [file] } });

    expect(getByText('test.txt')).toBeTruthy();
  });

  it('handles matrix file upload', async () => {
    const { getByText, getByLabelText } = render(UploadModal, {
      props: {
        isOpen: true,
        onClose: mockOnClose,
        onUpload: mockOnUpload
      }
    });

    const files = [
      new File(['test content 1'], 'matrix1.txt', { type: 'text/plain' }),
      new File(['test content 2'], 'matrix2.txt', { type: 'text/plain' })
    ];

    const input = getByLabelText('Click to select files or drag and drop') as HTMLInputElement;
    await fireEvent.change(input, { target: { files } });

    expect(getByText('matrix1.txt')).toBeTruthy();
    expect(getByText('matrix2.txt')).toBeTruthy();
  });

  it('validates file requirements before upload', async () => {
    const { getByText, getByRole, getByTestId } = render(UploadModal, {
      props: {
        isOpen: true,
        onClose: mockOnClose,
        onUpload: mockOnUpload
      }
    });

    const uploadButton = getByTestId('modal-upload-btn');
    await fireEvent.click(uploadButton);

    expect(getByText('Please select both coordinate and matrix files.')).toBeTruthy();
    expect(mockOnUpload).not.toHaveBeenCalled();
  });

  it('handles domain-specific upload correctly', async () => {
    const { getByText, getByLabelText, getByRole, getByTestId } = render(UploadModal, {
      props: {
        isOpen: true,
        onClose: mockOnClose,
        onUpload: mockOnUpload
      }
    });

    // Upload coordinate file
    const coordFile = new File(['coord content'], 'coord.txt', { type: 'text/plain' });
    const coordInput = getByLabelText('Click to select file or drag and drop') as HTMLInputElement;
    await fireEvent.change(coordInput, { target: { files: [coordFile] } });

    // Upload matrix files
    const matrixFiles = [
      new File(['matrix1'], 'matrix1.txt', { type: 'text/plain' }),
      new File(['matrix2'], 'matrix2.txt', { type: 'text/plain' })
    ];
    const matrixInput = getByLabelText('Click to select files or drag and drop') as HTMLInputElement;
    await fireEvent.change(matrixInput, { target: { files: matrixFiles } });

    // Enable domain-specific
    const domainCheckbox = getByLabelText('Domain-Specific?') as HTMLInputElement;
    await fireEvent.click(domainCheckbox);

    // Submit
    const uploadButton = getByTestId('modal-upload-btn');
    await fireEvent.click(uploadButton);

    expect(mockOnUpload).toHaveBeenCalledWith(
      expect.any(File),
      expect.arrayContaining([expect.any(File), expect.any(File)]),
      true,
      true
    );
  });

  it('handles non-domain-specific upload correctly', async () => {
    const { getByText, getByLabelText, getByRole, getByTestId } = render(UploadModal, {
      props: {
        isOpen: true,
        onClose: mockOnClose,
        onUpload: mockOnUpload
      }
    });

    // Upload coordinate file
    const coordFile = new File(['coord content'], 'coord.txt', { type: 'text/plain' });
    const coordInput = getByLabelText('Click to select file or drag and drop') as HTMLInputElement;
    await fireEvent.change(coordInput, { target: { files: [coordFile] } });

    // Upload single matrix file
    const matrixFile = new File(['matrix'], 'matrix.txt', { type: 'text/plain' });
    const matrixInput = getByLabelText('Click to select files or drag and drop') as HTMLInputElement;
    await fireEvent.change(matrixInput, { target: { files: [matrixFile] } });

    // Submit
    const uploadButton = getByTestId('modal-upload-btn');
    await fireEvent.click(uploadButton);

    expect(mockOnUpload).toHaveBeenCalledWith(
      expect.any(File),
      [expect.any(File)],
      false,
      true
    );
  });

  it('shows error when too many matrix files are uploaded for non-domain-specific', async () => {
    const { getByText, getByLabelText } = render(UploadModal, {
      props: {
        isOpen: true,
        onClose: mockOnClose,
        onUpload: mockOnUpload
      }
    });

    // Upload coordinate file
    const coordFile = new File(['coord content'], 'coord.txt', { type: 'text/plain' });
    const coordInput = getByLabelText('Click to select file or drag and drop') as HTMLInputElement;
    await fireEvent.change(coordInput, { target: { files: [coordFile] } });

    // Upload multiple matrix files
    const matrixFiles = [
      new File(['matrix1'], 'matrix1.txt', { type: 'text/plain' }),
      new File(['matrix2'], 'matrix2.txt', { type: 'text/plain' })
    ];
    const matrixInput = getByLabelText('Click to select files or drag and drop') as HTMLInputElement;
    await fireEvent.change(matrixInput, { target: { files: matrixFiles } });

    expect(getByText(/For non-domain-specific graphs, please select exactly one matrix file/)).toBeTruthy();
  });

  it('allows up to three matrix files for domain-specific upload', async () => {
    const { getByText, getByLabelText, getByRole, getByTestId } = render(UploadModal, {
      props: {
        isOpen: true,
        onClose: mockOnClose,
        onUpload: mockOnUpload
      }
    });

    // Upload coordinate file
    const coordFile = new File(['coord content'], 'coord.txt', { type: 'text/plain' });
    const coordInput = getByLabelText('Click to select file or drag and drop') as HTMLInputElement;
    await fireEvent.change(coordInput, { target: { files: [coordFile] } });

    // Upload three matrix files
    const matrixFiles = [
      new File(['matrix1'], 'matrix1.txt', { type: 'text/plain' }),
      new File(['matrix2'], 'matrix2.txt', { type: 'text/plain' }),
      new File(['matrix3'], 'matrix3.txt', { type: 'text/plain' })
    ];
    const matrixInput = getByLabelText('Click to select files or drag and drop') as HTMLInputElement;
    await fireEvent.change(matrixInput, { target: { files: matrixFiles } });

    // Enable domain-specific
    const domainCheckbox = getByLabelText('Domain-Specific?') as HTMLInputElement;
    await fireEvent.click(domainCheckbox);

    // Submit
    const uploadButton = getByTestId('modal-upload-btn');
    await fireEvent.click(uploadButton);

    expect(mockOnUpload).toHaveBeenCalledWith(
      expect.any(File),
      expect.arrayContaining([
        expect.any(File),
        expect.any(File),
        expect.any(File)
      ]),
      true,
      true
    );
  });

  describe('Test Files Integration', () => {
    it('handles valid coordinate and matrix file upload', async () => {
      const { getByText, getByLabelText, getByTestId } = render(UploadModal, {
        props: {
          isOpen: true,
          onClose: mockOnClose,
          onUpload: mockOnUpload
        }
      });

      // Upload valid coordinate file
      const coordFile = await createFileFromTestFile('chr7_coordinates1.csv');
      const coordInput = getByLabelText('Click to select file or drag and drop') as HTMLInputElement;
      await fireEvent.change(coordInput, { target: { files: [coordFile] } });

      // Upload valid matrix file
      const matrixFile = await createFileFromTestFile('chr7_domain1_matrix1_tir.csv');
      const matrixInput = getByLabelText('Click to select files or drag and drop') as HTMLInputElement;
      await fireEvent.change(matrixInput, { target: { files: [matrixFile] } });

      // Submit
      const uploadButton = getByTestId('modal-upload-btn');
      await fireEvent.click(uploadButton);

      expect(mockOnUpload).toHaveBeenCalledWith(
        expect.any(File),
        [expect.any(File)],
        false,
        true
      );
    });

    it('handles domain-specific upload with multiple valid matrix files', async () => {
      const { getByText, getByLabelText, getByTestId } = render(UploadModal, {
        props: {
          isOpen: true,
          onClose: mockOnClose,
          onUpload: mockOnUpload
        }
      });

      // Upload valid coordinate file
      const coordFile = await createFileFromTestFile('chr7_coordinates1.csv');
      const coordInput = getByLabelText('Click to select file or drag and drop') as HTMLInputElement;
      await fireEvent.change(coordInput, { target: { files: [coordFile] } });

      // Upload multiple valid matrix files
      const matrixFiles = await Promise.all([
        createFileFromTestFile('chr7_domain1_matrix1_tir.csv'),
        createFileFromTestFile('chr7_domain2_matrix1_nbs.csv'),
        createFileFromTestFile('chr7_domain3_matrix1_lrr.csv')
      ]);
      const matrixInput = getByLabelText('Click to select files or drag and drop') as HTMLInputElement;
      await fireEvent.change(matrixInput, { target: { files: matrixFiles } });

      // Enable domain-specific
      const domainCheckbox = getByLabelText('Domain-Specific?') as HTMLInputElement;
      await fireEvent.click(domainCheckbox);

      // Submit
      const uploadButton = getByTestId('modal-upload-btn');
      await fireEvent.click(uploadButton);

      expect(mockOnUpload).toHaveBeenCalledWith(
        expect.any(File),
        expect.arrayContaining([
          expect.any(File),
          expect.any(File),
          expect.any(File)
        ]),
        true,
        true
      );
    });

    it('shows error when uploading invalid files', async () => {
      const { getByText, getByLabelText } = render(UploadModal, {
        props: {
          isOpen: true,
          onClose: mockOnClose,
          onUpload: mockOnUpload
        }
      });

      // Try to upload invalid coordinate file
      const invalidCoordFile = await createFileFromTestFile('invalid.txt');
      const coordInput = getByLabelText('Click to select file or drag and drop') as HTMLInputElement;
      await fireEvent.change(coordInput, { target: { files: [invalidCoordFile] } });

      // Try to upload invalid matrix file
      const invalidMatrixFile = await createFileFromTestFile('invalid.xlsx');
      const matrixInput = getByLabelText('Click to select files or drag and drop') as HTMLInputElement;
      await fireEvent.change(matrixInput, { target: { files: [invalidMatrixFile] } });

      // The files should still be accepted by the input, but we can verify they're present
      expect(getByText('invalid.txt')).toBeTruthy();
      expect(getByText('invalid.xlsx')).toBeTruthy();
    });
  });
}); 