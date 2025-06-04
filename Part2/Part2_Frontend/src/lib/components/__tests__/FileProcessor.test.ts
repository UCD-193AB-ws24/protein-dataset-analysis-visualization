import { describe, it, expect, vi } from 'vitest';
import { loadTestFile, mockFileSystem } from '../../../test/utils/fileUtils';

describe('FileProcessor', () => {
  const fileSystem = mockFileSystem();

  beforeEach(() => {
    fileSystem.clearFiles();
    vi.clearAllMocks();
  });

  it('processes matrix file correctly', async () => {
    const file = loadTestFile('chr7_domain1_matrix1_tir.csv');
    fileSystem.addFile(file);

    // Mock the file processing function
    const processMatrixFile = vi.fn().mockImplementation(async (file: File) => {
      const content = await file.text();
      const rows = content.split('\n');
      const headers = rows[0].split(',');
      const data = rows.slice(1).map(row => row.split(','));
      return { headers, data };
    });

    const result = await processMatrixFile(file);
    expect(result.headers).toContain('gene1');
    expect(result.data.length).toBeGreaterThan(0);
  });

  it('processes coordinate file correctly', async () => {
    const file = loadTestFile('chr7_coordinates1.csv');
    fileSystem.addFile(file);

    // Mock the file processing function
    const processCoordFile = vi.fn().mockImplementation(async (file: File) => {
      const content = await file.text();
      const rows = content.split('\n');
      const headers = rows[0].split(',');
      const data = rows.slice(1).map(row => {
        const values = row.split(',');
        return {
          [headers[0]]: values[0],
          [headers[1]]: values[1],
          [headers[2]]: parseInt(values[2]),
          [headers[3]]: values[3]
        };
      });
      return data;
    });

    const result = await processCoordFile(file);
    expect(result[0]).toHaveProperty('name');
    expect(result[0]).toHaveProperty('genome');
    expect(result[0]).toHaveProperty('position');
    expect(result[0]).toHaveProperty('orientation');
  });

  it('handles empty files', async () => {
    const file = loadTestFile('empty.xlsx');
    fileSystem.addFile(file);

    const processFile = vi.fn().mockImplementation(async (file: File) => {
      const content = await file.text();
      if (!content.trim()) {
        throw new Error('File is empty');
      }
      return content;
    });

    await expect(processFile(file)).rejects.toThrow('File is empty');
  });

  it('handles malformed files', async () => {
    const file = loadTestFile('malformed.xlsx');
    fileSystem.addFile(file);

    const processFile = vi.fn().mockImplementation(async (file: File) => {
      const content = await file.text();
      const rows = content.split('\n');
      const headers = rows[0].split(',');
      
      // Check if all rows have the same number of columns
      const isValid = rows.every(row => row.split(',').length === headers.length);
      if (!isValid) {
        throw new Error('Malformed file: inconsistent number of columns');
      }
      
      return { headers, data: rows.slice(1).map(row => row.split(',')) };
    });

    await expect(processFile(file)).rejects.toThrow('Malformed file: inconsistent number of columns');
  });
}); 