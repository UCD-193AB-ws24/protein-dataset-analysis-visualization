<script lang="ts">
  import { onMount } from 'svelte';

  export let isOpen = false;
  export let onClose: () => void;
  export let onUpload: (coordinateFile: File | null, matrixFiles: File[], isDomainSpecific: boolean) => void;

  let isDomainSpecific = false;
  let coordinateFile: File | null = null;
  let matrixFiles: File[] = [];
  let isUploading = false;
  let uploadComplete = false;
  let errorMessage = '';
  let isDragging = false;

  // Reset state when modal is closed
  $: if (!isOpen) {
    coordinateFile = null;
    matrixFiles = [];
    isDomainSpecific = false;
    isUploading = false;
    uploadComplete = false;
    errorMessage = '';
  }

  function handleCoordinateUpload(e: Event) {
    const target = e.target as HTMLInputElement;
    if (target.files && target.files.length > 0) {
      coordinateFile = target.files[0];
    }
  }

  function handleMatrixUpload(e: Event) {
    const target = e.target as HTMLInputElement;
    if (target.files) {
      matrixFiles = Array.from(target.files);
      errorMessage = '';
    }
  }

  function handleDragOver(e: DragEvent) {
    e.preventDefault();
    isDragging = true;
  }

  function handleDragLeave() {
    isDragging = false;
  }

  function handleDrop(e: DragEvent, type: 'coordinate' | 'matrix') {
    e.preventDefault();
    isDragging = false;
    
    if (!e.dataTransfer?.files) return;
    
    if (type === 'coordinate') {
      if (e.dataTransfer.files.length > 1) {
        errorMessage = 'Please drop only one coordinate file.';
        return;
      }
      coordinateFile = e.dataTransfer.files[0];
    } else {
      const files = Array.from(e.dataTransfer.files);
      if (!isDomainSpecific && files.length > 1) {
        errorMessage = 'For non-domain-specific graphs, please select exactly one matrix file.';
        return;
      }
      matrixFiles = files;
    }
    errorMessage = '';
  }

  function validateFiles(): boolean {
    if (!coordinateFile || matrixFiles.length === 0) {
      errorMessage = 'Please select both coordinate and matrix files.';
      return false;
    }
    if (!isDomainSpecific && matrixFiles.length !== 1) {
      errorMessage = 'For non-domain-specific graphs, please select exactly one matrix file. For domain-specific graphs, select the "Domain-Specific?" checkbox.';
      return false;
    }
    if (isDomainSpecific && matrixFiles.length > 3) {
      errorMessage = 'For domain-specific graphs, you can select up to three matrix files.';
      return false;
    }
    errorMessage = '';
    return true;
  }

  function handleSubmit() {
    if (!validateFiles()) return;
    
    isUploading = true;
    onUpload(coordinateFile, matrixFiles, isDomainSpecific);
    // Simulate upload completion after a short delay
    setTimeout(() => {
      isUploading = false;
      uploadComplete = true;
    }, 1500);
  }

  function handleClose() {
    onClose();
  }

  function handleDone() {
    onClose();
  }

  // Add a reactive statement to validate when domain-specific changes
  $: if (isDomainSpecific !== undefined) {
    if (!isDomainSpecific && matrixFiles.length > 1) {
      errorMessage = 'For non-domain-specific graphs, please select exactly one matrix file.';
    } else {
      errorMessage = '';
    }
  }
</script>

{#if isOpen}
  <div class="fixed inset-0 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
    <div class="bg-white rounded-lg shadow-xl w-full max-w-4xl">
      <div class="flex justify-between items-center p-6 border-b border-slate-200">
        <h2 class="text-2xl font-bold">Upload Files</h2>
        <button
          on:click={handleClose}
          class="text-slate-500 hover:text-slate-700"
          aria-label="Close modal"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="18" y1="6" x2="6" y2="18"></line>
            <line x1="6" y1="6" x2="18" y2="18"></line>
          </svg>
        </button>
      </div>
      <div class="p-6">
        {#if errorMessage}
          <div class="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p class="text-red-600">{errorMessage}</p>
          </div>
        {/if}
        <div class="grid md:grid-cols-2 gap-6">
          <!-- Coordinate File Upload -->
          <div 
            class="border-2 border-dashed border-slate-300 rounded-lg p-6 flex flex-col items-center justify-center transition-colors duration-200 {isDragging ? 'border-blue-500 bg-blue-50' : ''}"
            on:dragover={handleDragOver}
            on:dragleave={handleDragLeave}
            on:drop={(e) => handleDrop(e, 'coordinate')}
            role="button"
            tabindex="0"
          >
            <h3 class="text-xl font-bold mb-4">
              Upload Coordinate File
            </h3>
            <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-slate-400 mb-4">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
              <polyline points="17 8 12 3 7 8"></polyline>
              <line x1="12" y1="3" x2="12" y2="15"></line>
            </svg>
            <div class="w-full">
              <label class="flex flex-col items-center px-4 py-6 bg-white rounded-lg shadow-sm border border-slate-300 cursor-pointer hover:bg-slate-50">
                <span class="text-base font-medium">
                  {coordinateFile
                    ? coordinateFile.name
                    : 'Click to select file or drag and drop'}
                </span>
                <input
                  type="file"
                  class="hidden"
                  on:change={handleCoordinateUpload}
                  accept=".xlsx,.csv,.txt"
                />
              </label>
            </div>
            {#if coordinateFile}
              <div class="mt-4 flex items-center text-green-600">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="mr-2">
                  <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
                  <polyline points="22 4 12 14.01 9 11.01"></polyline>
                </svg>
                <span>File ready to upload</span>
              </div>
            {/if}
          </div>
          <!-- Matrix Files Upload -->
          <div 
            class="border-2 border-dashed border-slate-300 rounded-lg p-6 flex flex-col items-center justify-center transition-colors duration-200 {isDragging ? 'border-blue-500 bg-blue-50' : ''}"
            on:dragover={handleDragOver}
            on:dragleave={handleDragLeave}
            on:drop={(e) => handleDrop(e, 'matrix')}
            role="button"
            tabindex="0"
          >
            <h3 class="text-xl font-bold mb-4">Upload Matrix Files</h3>
            <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-slate-400 mb-4">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
              <polyline points="17 8 12 3 7 8"></polyline>
              <line x1="12" y1="3" x2="12" y2="15"></line>
            </svg>
            <div class="w-full">
              <label class="flex flex-col items-center px-4 py-6 bg-white rounded-lg shadow-sm border border-slate-300 cursor-pointer hover:bg-slate-50">
                <span class="text-base font-medium">
                  Click to select files or drag and drop
                </span>
                <input
                  type="file"
                  class="hidden"
                  on:change={handleMatrixUpload}
                  multiple
                  accept=".xlsx,.csv,.txt"
                />
              </label>
            </div>
            {#if matrixFiles.length > 0}
              <div class="w-full mt-4 space-y-2">
                {#each matrixFiles as file}
                  <div class="flex items-center justify-between p-3 bg-white border border-slate-200 rounded-lg">
                    <div class="flex items-center text-green-600">
                      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="mr-2">
                        <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
                        <polyline points="22 4 12 14.01 9 11.01"></polyline>
                      </svg>
                      <span class="text-slate-700">{file.name}</span>
                    </div>
                    <button
                      class="text-slate-400 hover:text-red-500"
                      on:click={() => matrixFiles = matrixFiles.filter(f => f !== file)}
                      aria-label="Remove file"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <line x1="18" y1="6" x2="6" y2="18"></line>
                        <line x1="6" y1="6" x2="18" y2="18"></line>
                      </svg>
                    </button>
                  </div>
                {/each}
              </div>
            {/if}
            <div class="mt-6 flex items-center">
              <input
                type="checkbox"
                id="domainSpecific"
                bind:checked={isDomainSpecific}
                class="h-4 w-4 text-blue-600 rounded border-slate-300 focus:ring-blue-500"
              />
              <label
                for="domainSpecific"
                class="ml-2 text-slate-700"
              >
                Domain-Specific?
              </label>
            </div>
          </div>
        </div>
      </div>
      <div class="flex justify-end p-6 border-t border-slate-200 bg-slate-50 rounded-b-lg">
        {#if !uploadComplete}
          <button
            on:click={handleClose}
            class="px-6 py-2 border border-slate-300 rounded-md hover:bg-slate-100 mr-3"
            disabled={isUploading}
          >
            Cancel
          </button>
          <button
            on:click={handleSubmit}
            class="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md disabled:bg-blue-300 disabled:cursor-not-allowed"
            disabled={!coordinateFile || matrixFiles.length === 0 || isUploading}
          >
            {#if isUploading}
              <div class="flex items-center">
                <svg class="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Uploading...
              </div>
            {:else}
              Upload
            {/if}
          </button>
        {:else}
          <button
            on:click={handleDone}
            class="px-6 py-2 bg-green-600 hover:bg-green-700 text-white rounded-md"
          >
            Done
          </button>
        {/if}
      </div>
    </div>
  </div>
{/if}

<style>
  /* Empty style tag required for Tailwind processing */
</style> 