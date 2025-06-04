import '@testing-library/jest-dom';
import { vi, afterEach } from 'vitest';
import { cleanup } from '@testing-library/svelte';

// Clean up after each test
afterEach(() => {
  cleanup();
});

declare global {
  interface Window {
    FileReader: typeof FileReader;
    fetch: typeof fetch;
  }
}

// Mock the FileReader API
const mockFileReader = {
  EMPTY: 0,
  LOADING: 1,
  DONE: 2,
  prototype: {
    readAsText: vi.fn(),
    readAsArrayBuffer: vi.fn(),
    readAsDataURL: vi.fn(),
    readAsBinaryString: vi.fn(),
    abort: vi.fn()
  }
};

// Add FileReader to the global window object
window.FileReader = mockFileReader as any;

// Mock fetch
window.fetch = vi.fn();

// Mock document.querySelector and scrollIntoView
document.querySelector = vi.fn().mockReturnValue({
  scrollIntoView: vi.fn()
});

// Mock ResizeObserver
window.ResizeObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}));

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

// Mock window.requestAnimationFrame
let rafId = 0;
window.requestAnimationFrame = vi.fn(callback => {
  setTimeout(callback, 0);
  return ++rafId;
});
window.cancelAnimationFrame = vi.fn();

// Mock window.URL.createObjectURL
window.URL.createObjectURL = vi.fn();
window.URL.revokeObjectURL = vi.fn(); 