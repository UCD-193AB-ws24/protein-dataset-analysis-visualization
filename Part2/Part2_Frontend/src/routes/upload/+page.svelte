<script>
    let file;
    let uploadedFileUrl = "";
    let errorMessage = "";
    let isUploading = false;

    async function uploadFile() {
        if (!file) {
            errorMessage = "Please select a file.";
            return;
        }

        isUploading = true;
        errorMessage = "";
        uploadedFileUrl = "";

        const formData = new FormData();
        formData.append("file", file);

        try {
            const response = await fetch("http://127.0.0.1:5000/upload", {
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
        {isUploading ? "Uploading..." : "Upload"}
    </button>

    {#if errorMessage}
        <p class="error">{errorMessage}</p>
    {/if}

    {#if uploadedFileUrl}
        <p class="success">✅ File Uploaded:</p>
        <a class="file-link" href={uploadedFileUrl} target="_blank">{uploadedFileUrl}</a>
    {/if}
</div>

<style>
    .container {
        max-width: 400px;
        margin: 50px auto;
        padding: 20px;
        background: white;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
        border-radius: 10px;
        text-align: center;
    }

    h2 {
        color: #333;
        margin-bottom: 15px;
    }

    .file-input {
        width: 100%;
        padding: 10px;
        margin-bottom: 10px;
        border: 2px dashed #60a5fa;
        border-radius: 8px;
        text-align: center;
    }

    .btn {
        background-color: #3b82f6;
        color: white;
        border: none;
        padding: 10px 15px;
        border-radius: 5px;
        cursor: pointer;
        transition: background 0.3s;
    }

    .btn:hover {
        background: #2563eb;
    }

    .error {
        color: red;
        font-size: 14px;
    }

    .success {
        color: green;
        font-weight: bold;
    }

    .file-link {
        color: #1d4ed8;
        text-decoration: none;
    }
</style>
