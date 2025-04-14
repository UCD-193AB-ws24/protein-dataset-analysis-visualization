<script>
    let file;
    let username = localStorage.getItem("username") || ""; // Retrieve username
    let uploadedFileUrl = "";
    let errorMessage = "";
    let isUploading = false;

    async function uploadFile() {
        if (!file || !username) {
            errorMessage = "Please select a file and log in first.";
            return;
        }

        isUploading = true;
        errorMessage = "";
        uploadedFileUrl = "";

        const formData = new FormData();
        formData.append("file", file);
        formData.append("username", username);  // Automatically send stored username

        try {
            const response = await fetch("https://h47f781wh1.execute-api.us-east-1.amazonaws.com/dev/upload", {
                method: "POST",
                body: formData
            });

            if (!response.ok) {
                throw new Error(`Upload failed: ${response.statusText}`);
            }

            const data = await response.json();
            uploadedFileUrl = data.url;
        } catch (error) {
            errorMessage = error.message || "An error occurred.";
        } finally {
            isUploading = false;
        }
    }

    function handleFileChange(event) {
        file = event.target.files[0];
    }
</script>

<div class="container">
    <h2>📤 Upload a File</h2>

    <input type="file" class="file-input" on:change={handleFileChange} />
    <button class="btn upload-btn" on:click={uploadFile} disabled={isUploading}>
        {#if isUploading} Uploading... {:else} Upload {/if}
    </button>

    {#if errorMessage}
        <p class="error">{errorMessage}</p>
    {/if}

    {#if uploadedFileUrl}
        <p class="success">✅ File Uploaded:</p>
        <a class="file-link" href={uploadedFileUrl} target="_blank">{uploadedFileUrl}</a>
    {/if}
</div>
