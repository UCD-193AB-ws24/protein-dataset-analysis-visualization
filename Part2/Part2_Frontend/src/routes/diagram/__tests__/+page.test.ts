import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, fireEvent } from '@testing-library/svelte';
import Page from '../+page.svelte';
import { goto } from '$app/navigation';
import { oidcClient } from '$lib/auth';
import { API_BASE_URL } from '$lib/envs';

// Mock dependencies
vi.mock('$app/navigation', () => ({
  goto: vi.fn()
}));

vi.mock('$lib/auth', () => ({
  oidcClient: {
    getUser: vi.fn()
  }
}));

// Mock fetch
global.fetch = vi.fn();

// Mock test files
const testFiles = import.meta.glob('../../../lib/test/test_files/*', { 
  query: '?raw',
  import: 'default'
});

// Helper function to create File objects from test files
async function createFileFromTestFile(filename: string): Promise<File> {
  const filePath = `../../../lib/test/test_files/${filename}`;
  const content = await testFiles[filePath]() as string;
  return new File([content], filename, { type: 'text/csv' });
}

describe('Diagram Page', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Mock successful authentication with complete User object
    vi.mocked(oidcClient.getUser).mockResolvedValue({
      access_token: 'mock-token',
      expired: false,
      session_state: 'mock-session',
      token_type: 'Bearer',
      profile: {
        sub: 'mock-sub',
        iss: 'mock-iss',
        aud: 'mock-aud',
        exp: 1234567890,
        iat: 1234567890
      },
      state: 'mock-state',
      scope: 'openid',
      id_token: 'mock-id-token',
      expires_at: 1234567890,
      expires_in: 3600,
      scopes: ['openid'],
      toStorageString: () => 'mock-storage-string'
    });
  });

  it('renders without crashing', () => {
    const { container } = render(Page);
    expect(container).toBeTruthy();
  });

  it('handles file upload and graph generation', async () => {
    // Mock successful API response
    const mockGraphData = {
      graphs: [{
        nodes: [
          { id: '1', genome_name: 'genome1', protein_name: 'protein1', direction: 'plus', rel_position: 0, is_present: true },
          { id: '2', genome_name: 'genome2', protein_name: 'protein2', direction: 'minus', rel_position: 1, is_present: true }
        ],
        links: [
          { source: '1', target: '2', score: 80, is_reciprocal: true }
        ],
        genomes: ['genome1', 'genome2']
      }],
      num_genes: 2,
      num_domains: 1,
      is_domain_specific: false
    };

    vi.mocked(fetch).mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockGraphData)
    } as any);

    const { getByText, getByLabelText } = render(Page);

    // Open upload modal
    const uploadButton = getByText('Upload Files');
    await fireEvent.click(uploadButton);

    // Upload coordinate file
    const coordFile = await createFileFromTestFile('chr7_coordinates1.csv');
    const coordInput = getByLabelText('Click to select file or drag and drop') as HTMLInputElement;
    await fireEvent.change(coordInput, { target: { files: [coordFile] } });

    // Upload matrix file
    const matrixFile = await createFileFromTestFile('chr7_domain1_matrix1_tir.csv');
    const matrixInput = getByLabelText('Click to select files or drag and drop') as HTMLInputElement;
    await fireEvent.change(matrixInput, { target: { files: [matrixFile] } });

    // Submit upload
    const submitButton = getByText('Upload');
    await fireEvent.click(submitButton);

    // Verify API call
    expect(fetch).toHaveBeenCalledWith(
      `${API_BASE_URL}/generate_graph`,
      expect.objectContaining({
        method: 'POST',
        body: expect.any(FormData)
      })
    );
  });

  it('handles domain-specific upload with multiple matrix files', async () => {
    // Mock successful API response
    const mockGraphData = {
      graphs: [{
        nodes: [
          { id: '1', genome_name: 'genome1', protein_name: 'protein1', direction: 'plus', rel_position: 0, is_present: true },
          { id: '2', genome_name: 'genome2', protein_name: 'protein2', direction: 'minus', rel_position: 1, is_present: true }
        ],
        links: [
          { source: '1', target: '2', score: 80, is_reciprocal: true }
        ],
        genomes: ['genome1', 'genome2']
      }],
      num_genes: 2,
      num_domains: 3,
      is_domain_specific: true
    };

    vi.mocked(fetch).mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockGraphData)
    } as any);

    const { getByText, getByLabelText } = render(Page);

    // Open upload modal
    const uploadButton = getByText('Upload Files');
    await fireEvent.click(uploadButton);

    // Upload coordinate file
    const coordFile = await createFileFromTestFile('chr7_coordinates1.csv');
    const coordInput = getByLabelText('Click to select file or drag and drop') as HTMLInputElement;
    await fireEvent.change(coordInput, { target: { files: [coordFile] } });

    // Upload multiple matrix files
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

    // Submit upload
    const submitButton = getByText('Upload');
    await fireEvent.click(submitButton);

    // Verify API call
    expect(fetch).toHaveBeenCalledWith(
      `${API_BASE_URL}/generate_graph`,
      expect.objectContaining({
        method: 'POST',
        body: expect.any(FormData)
      })
    );
  });

  it('handles loading existing group data', async () => {
    // Mock successful API response
    const mockGroupData = {
      graphs: [{
        nodes: [
          { id: '1', genome_name: 'genome1', protein_name: 'protein1', direction: 'plus', rel_position: 0, is_present: true }
        ],
        links: [],
        genomes: ['genome1']
      }],
      num_genes: 1,
      num_domains: 1,
      title: 'Test Group',
      description: 'Test Description',
      matrix_files: [{ url: 'test.csv', original_name: 'test.csv' }],
      coordinate_file: { url: 'test.csv', original_name: 'test.csv' }
    };

    vi.mocked(fetch).mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockGroupData)
    } as any);

    // Mock URL parameters
    const mockUrl = new URL('http://localhost/diagram?groupId=123');
    Object.defineProperty(window, 'location', {
      value: mockUrl,
      writable: true
    });

    const { getByText } = render(Page);

    // Verify API call
    expect(fetch).toHaveBeenCalledWith(
      `${API_BASE_URL}/get_group_graph?groupId=123`,
      expect.any(Object)
    );

    // Verify group data is displayed
    expect(getByText('Test Group')).toBeTruthy();
    expect(getByText('Test Description')).toBeTruthy();
  });

  it('handles authentication errors', async () => {
    // Mock authentication error
    vi.mocked(oidcClient.getUser).mockRejectedValue(new Error('Auth error'));

    render(Page);

    // Verify redirect to invalid login page
    expect(goto).toHaveBeenCalledWith('/invalid-login');
  });
}); 