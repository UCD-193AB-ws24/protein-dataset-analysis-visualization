<script>
    let numFiles = 2;
    let uploads = Array(numFiles).fill(null);
    let username = localStorage.getItem("username") || ""; // Retrieve username
    let uploadedFileUrl = "";
    let errorMessage = "";
    let isUploading = false;
    let file_names = ["matrix", "coordinate"]

    async function uploadFile() {
        if (uploads.some(file => file === null) || !username) {
            errorMessage = "Please select a file and log in first.";
            return;
        }

        isUploading = true;
        errorMessage = "";
        uploadedFileUrl = "";

        const formData = new FormData();
        uploads.forEach((file, i) => {
            formData.append(`file_${file_names[i]}`, file);
        })
        formData.append("username", username);  // Automatically send stored username

        try {
            const response = await fetch("http://127.0.0.1:5000/upload", { // https://h47f781wh1.execute-api.us-east-1.amazonaws.com/dev/upload
                method: "POST",
                body: formData
            });

            if (!response.ok) {
                throw new Error(`Upload failed: ${response.statusText}`);
            }

            const data = await response.json();
            uploadedFileUrl = data.url;
            console.log(data)
        } catch (error) {
            errorMessage = error.message || "An error occurred.";
            console.error('Detailed error:', {
                status: error.response?.status,
                data: await error.response?.text()
            });
        } finally {
            isUploading = false;
        }
    }

    function addFile(i) {
        if (!uploads[i]) {
            alert(`Please select a ${file_names[i]} file  to upload`)
            return
        }
    }

    function handleFileChange(event, i) {
        const file = event.target.files[0];
        if (file) {
            uploads[i] = file;
        }
    }

    $: if (uploads.every(file => file !== null)) {
        uploadFile();
    }
</script>

<div class="container">
    <h2>📤 Upload a File</h2>

    <div class="upload">
        <p class="description">Please upload the matrix file</p>
        <input type="file" class="file-input" on:change={(e) => handleFileChange(e, 0)} />
        <button class="btn upload-btn" on:click={() => addFile(0)} disabled={isUploading}>
            {#if isUploading} Uploading... {:else} Upload {/if}
        </button>
    </div>

    <div class="upload">
        <p class="description">Please upload the coordinates file</p>
        <input type="file" class="file-input" on:change={(e) => handleFileChange(e, 1)} />
        <button class="btn upload-btn" on:click={() => addFile(1)} disabled={isUploading}>
            {#if isUploading} Uploading... {:else} Upload {/if}
        </button>
    </div>

    {#if errorMessage}
        <p class="error">{errorMessage}</p>
    {/if}

    {#if uploadedFileUrl}
        <p class="success">✅ File Uploaded:</p>
        <a class="file-link" href={uploadedFileUrl} target="_blank">{uploadedFileUrl}</a>
    {/if}
</div>
