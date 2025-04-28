<script>
    let manualPublicId = "";
    let retrievedFileUrl = "";
    let errorMessage = "";

    async function fetchFile() {
        if (!manualPublicId) {
            errorMessage = "Please enter a file name!";
            return;
        }

        try {
            const response = await fetch(`https://4aorvlzrd1.execute-api.us-east-1.amazonaws.com/dev/retrieve/${manualPublicId}`);
            if (!response.ok) {
                throw new Error("Failed to retrieve file.");
            }

            const data = await response.json();
            retrievedFileUrl = data.file_url;
        } catch (error) {
            errorMessage = error.message;
        }
    }
</script>

<div class="container">
    <h2>🔍 Retrieve a File</h2>
    <input type="text" class="text-input" bind:value={manualPublicId} placeholder="Enter file name" />
    <button class="btn retrieve-btn" on:click={fetchFile}>Retrieve</button>

    {#if errorMessage}
        <p class="error">{errorMessage}</p>
    {/if}

    {#if retrievedFileUrl}
        <p class="success">✅ File Retrieved:</p>
        {#if retrievedFileUrl.match(/\.(jpg|jpeg|png|gif)$/)}
            <img class="retrieved-img" src={retrievedFileUrl} alt="Retrieved Image" />
        {:else if retrievedFileUrl.match(/\.(mp4|mov|avi)$/)}
            <video controls class="retrieved-video">
                <source src={retrievedFileUrl} type="video/mp4">
                Your browser does not support the video tag.
            </video>
        {:else}
            <a class="file-link" href={retrievedFileUrl} target="_blank">{retrievedFileUrl}</a>
        {/if}
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

    .text-input {
        width: 100%;
        padding: 10px;
        margin-bottom: 10px;
        border: 2px solid #60a5fa;
        border-radius: 8px;
    }

    .retrieved-img, .retrieved-video {
        max-width: 100%;
        margin-top: 10px;
        border-radius: 5px;
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
