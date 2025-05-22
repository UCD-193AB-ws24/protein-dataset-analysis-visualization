<script lang="ts">
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
      const newFiles = Array.from(target.files);
      const totalFiles = matrixFiles.length + newFiles.length;
      
      if (totalFiles > 3) {
        errorMessage = 'You can only upload a maximum of 3 matrix files.';
        return;
      }
      
      matrixFiles = [...matrixFiles, ...newFiles];
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
      const newFiles = Array.from(e.dataTransfer.files);
      const totalFiles = matrixFiles.length + newFiles.length;
      
      if (totalFiles > 3) {
        errorMessage = 'You can only upload a maximum of 3 matrix files.';
        return;
      }
      
      matrixFiles = [...matrixFiles, ...newFiles];
    }
    errorMessage = '';
  }

  function validateFiles(): boolean {
    if (!coordinateFile || matrixFiles.length === 0) {
      errorMessage = 'Please select both coordinate and matrix files.';
      return false;
    }
    if (!isDomainSpecific && matrixFiles.length !== 1) {
      errorMessage = 'For non-domain-specific graphs, please select exactly one matrix file. \n For domain-specific graphs, select the "Domain-Specific?" checkbox.';
      return false;
    }
    if (isDomainSpecific && matrixFiles.length > 3) {
      errorMessage = 'For domain-specific graphs, you can select up to three matrix files.';
      return false;
    }
    errorMessage = '';
    return true;
  }

  async function handleSubmit() {
    if (!validateFiles()) return;
    
    isUploading = true;
    errorMessage = '';
    try {
      await onUpload(coordinateFile, matrixFiles, isDomainSpecific);
    } catch (error) {
      errorMessage = error instanceof Error ? error.message : 'An error occurred during upload';
      isUploading = false;
      // Scroll to error message
      const errorElement = document.querySelector('.error-message');
      if (errorElement) {
        errorElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    }
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
      errorMessage = 'For non-domain-specific graphs, please select exactly one matrix file. For domain-specific graphs, select the "Domain-Specific?" checkbox.';
    } else {
      errorMessage = '';
    }
  }
</script>

{#if isOpen}
  <div class="fixed inset-0 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center z-50 p-4 overflow-y-auto">
    <div class="bg-white rounded-lg shadow-xl w-full max-w-4xl my-4">
      <div class="flex justify-between items-center p-4 sm:p-6 border-b border-slate-200">
        <h2 class="text-xl sm:text-2xl font-bold">Upload Files</h2>
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
      <div class="p-4 sm:p-6">
        {#if errorMessage}
          <div class="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg error-message">
            <p class="text-red-600">{errorMessage}</p>
          </div>
        {/if}
        <div class="grid md:grid-cols-2 gap-4 sm:gap-6">
          <!-- Coordinate File Upload -->
          <div 
            class="border-2 border-dashed border-slate-300 rounded-lg p-4 sm:p-6 flex flex-col items-center justify-center transition-colors duration-200 {isDragging ? 'border-blue-500 bg-blue-50' : ''}"
            on:dragover={handleDragOver}
            on:dragleave={handleDragLeave}
            on:drop={(e) => handleDrop(e, 'coordinate')}
            role="button"
            tabindex="0"
          >
            <h3 class="text-lg sm:text-xl font-bold mb-4 text-center">
              Upload Coordinate File
            </h3>
            <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-slate-400 mb-4">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
              <polyline points="17 8 12 3 7 8"></polyline>
              <line x1="12" y1="3" x2="12" y2="15"></line>
            </svg>
            <div class="w-full">
              <label class="flex flex-col items-center px-2 sm:px-4 py-4 sm:py-6 bg-white rounded-lg shadow-sm border border-slate-300 cursor-pointer hover:bg-slate-50">
                <span class="text-sm sm:text-base font-medium text-center">
                  Click to select file or drag and drop
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
              <div class="w-full mt-4 max-h-[200px] overflow-y-auto pr-1">
                <div class="space-y-2">
                  <div class="flex items-center justify-between p-2 sm:p-3 bg-white border border-slate-200 rounded-lg">
                    <div class="flex items-center text-green-600 min-w-0 flex-1 mr-2">
                      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="flex-shrink-0">
                        <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
                        <polyline points="22 4 12 14.01 9 11.01"></polyline>
                      </svg>
                      <span class="text-slate-700 truncate text-sm sm:text-base ml-2" title={coordinateFile.name}>{coordinateFile.name}</span>
                    </div>
                    <button
                      class="text-slate-400 hover:text-red-500 flex-shrink-0"
                      on:click={() => coordinateFile = null}
                      aria-label="Remove file"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <line x1="18" y1="6" x2="6" y2="18"></line>
                        <line x1="6" y1="6" x2="18" y2="18"></line>
                      </svg>
                    </button>
                  </div>
                </div>
              </div>
            {/if}
          </div>
          <!-- Matrix Files Upload -->
          <div 
            class="border-2 border-dashed border-slate-300 rounded-lg p-4 sm:p-6 flex flex-col items-center justify-center transition-colors duration-200 {isDragging ? 'border-blue-500 bg-blue-50' : ''}"
            on:dragover={handleDragOver}
            on:dragleave={handleDragLeave}
            on:drop={(e) => handleDrop(e, 'matrix')}
            role="button"
            tabindex="0"
          >
            <h3 class="text-lg sm:text-xl font-bold mb-4 text-center">Upload Matrix Files</h3>
            <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-slate-400 mb-4">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
              <polyline points="17 8 12 3 7 8"></polyline>
              <line x1="12" y1="3" x2="12" y2="15"></line>
            </svg>
            <div class="w-full">
              <label class="flex flex-col items-center px-2 sm:px-4 py-4 sm:py-6 bg-white rounded-lg shadow-sm border border-slate-300 cursor-pointer hover:bg-slate-50">
                <span class="text-sm sm:text-base font-medium text-center">
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
              <div class="w-full mt-4 max-h-[200px] overflow-y-auto pr-1">
                <div class="space-y-2">
                  {#each matrixFiles as file}
                    <div class="flex items-center justify-between p-2 sm:p-3 bg-white border border-slate-200 rounded-lg">
                      <div class="flex items-center text-green-600 min-w-0 flex-1 mr-2">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="flex-shrink-0">
                          <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
                          <polyline points="22 4 12 14.01 9 11.01"></polyline>
                        </svg>
                        <span class="text-slate-700 truncate text-sm sm:text-base ml-2" title={file.name}>{file.name}</span>
                      </div>
                      <button
                        class="text-slate-400 hover:text-red-500 flex-shrink-0"
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
              </div>
            {/if}
            <div class="mt-4 sm:mt-6 flex items-center">
              <input
                type="checkbox"
                id="domainSpecific"
                bind:checked={isDomainSpecific}
                class="h-4 w-4 text-blue-600 rounded border-slate-300 focus:ring-blue-500"
              />
              <label
                for="domainSpecific"
                class="ml-2 text-sm sm:text-base text-slate-700"
              >
                Domain-Specific?
              </label>
            </div>
          </div>
        </div>
      </div>
      <div class="flex justify-end p-4 sm:p-6 border-t border-slate-200 bg-slate-50 rounded-b-lg">
        {#if !uploadComplete}
          <button
            on:click={handleClose}
            class="px-4 sm:px-6 py-2 border border-slate-300 rounded-md hover:bg-slate-100 mr-3 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-white text-sm sm:text-base"
            disabled={isUploading}
          >
            Cancel
          </button>
          <button
            on:click={handleSubmit}
            class="px-4 sm:px-6 py-2 bg-green-600 hover:bg-green-700 text-white rounded-md disabled:bg-green-300 disabled:cursor-not-allowed text-sm sm:text-base"
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
            class="px-4 sm:px-6 py-2 bg-green-600 hover:bg-green-700 text-white rounded-md text-sm sm:text-base"
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