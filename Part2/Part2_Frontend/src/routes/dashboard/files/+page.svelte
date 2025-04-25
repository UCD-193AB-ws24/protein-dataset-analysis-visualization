<script>
    import { onMount } from "svelte";
    import { goto } from "$app/navigation";

    let username = "";
    let userFiles = [];
    let userFileGroups = [];
    let errorMessage = "";
    let loading = false;
    let retrievedFileUrl = "";
    let retrievingFile = false;

    // Ensure `localStorage` is accessed only in the client
    onMount(async () => {
        if (typeof window !== "undefined") {
            username = localStorage.getItem("username") || "";
            if (username) {
                try {
                    // Fetch user files and file groups
                    await fetchUserFiles();
                    await fetchUserFileGroups();
                } catch (error) {
                    errorMessage = error.message || "Failed to load data";
                }
            } else {
                errorMessage = "No username found. Please log in.";
            }
        }
    });

    async function fetchUserFileGroups() {
        loading = true;
        errorMessage = "";

        try {
            const response = await fetch("http://127.0.0.1:5000/get_user_file_groups", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ username }),
            });

            if (!response.ok) {
                throw new Error(`Error fetching file groups: ${response.statusText}`);
            }

            const data = await response.json();
            userFileGroups = data.file_groups;
        } catch (error) {
            errorMessage = error.message || "An error occurred.";
        } finally {
            loading = false;
        }
    }

    async function fetchUserFiles() {
        loading = true;
        errorMessage = "";

        try {
            const response = await fetch("http://127.0.0.1:5000/get_user_files", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ username }),
            });

            if (!response.ok) {
                throw new Error(`Error fetching files: ${response.statusText}`);
            }

            const data = await response.json();
            userFiles = data.files; // Store the retrieved files
        } catch (error) {
            errorMessage = error.message || "An error occurred.";
        } finally {
            loading = false;
        }
    }

    // Function to retrieve a file when clicking the "Retrieve" button
    async function fetchFile(fileName) {
        if (!fileName) {
            errorMessage = "File name is missing!";
            return;
        }

        retrievingFile = true;
        errorMessage = "";
        retrievedFileUrl = "";

        try {
            const response = await fetch(`http://127.0.0.1:5000/retrieve/${fileName}`);
            if (!response.ok) {
                throw new Error("Failed to retrieve file.");
            }

            const data = await response.json();
            retrievedFileUrl = data.file_url;
        } catch (error) {
            errorMessage = error.message;
        } finally {
            retrievingFile = false;
        }
    }
</script>

<div class="file-groups">
    <h2>📁 Your File Groups</h2>

    {#if loading}
        <p>Loading file groups...</p>
    {/if}

    {#if errorMessage}
        <p class="error">{errorMessage}</p>
    {/if}

    {#if userFileGroups.length > 0}
        <div class="card-container">
            {#each userFileGroups as group}
                <div class="card">
                    <h3>{group.title}</h3>
                    <p>Description: {group.description}</p>
                    <p>Genomes: {group.genomes.join(", ")}</p>
                    <p>Num Genes: {group.num_genes}</p>
                    <p>Num Domains: {group.num_domains}</p>
                    <p>Domain Specific: {group.is_domain_specific ? "Yes" : "No"}</p>
                    <p>Files:</p>
                    {#if group.files.length > 0}
                        <ul class="group-file-list">
                            {#each group.files as file}
                                <li style="word-wrap: break-word; overflow-wrap: break-word;">
                                    <strong>{`${file.file_type}`}</strong>{`: ${file.file_name}`}
                                </li>
                            {/each}
                        </ul>
                        <button on:click={() => goto(`/dashboard/diagram?groupId=${group.id}`)}>
                            View Diagram
                        </button>
                    {:else}
                        <p class="no-files">No files included</p>
                    {/if}
                </div>
            {/each}
        </div>
    {:else if !loading}
        <p>No file groups found.</p>
    {/if}
</div>

<div class="container">
    <h2>📂 Your Uploaded Files</h2>

    {#if loading}
        <p>Loading files...</p>
    {/if}

    {#if errorMessage}
        <p class="error">{errorMessage}</p>
    {/if}

    {#if userFiles.length > 0}
        <ul class="file-list">
            {#each userFiles as file}
                <li>
                    {file.file_name} - Uploaded at: {file.uploaded_at}
                    <button class="retrieve-btn" on:click={() => fetchFile(file.file_name)}>
                        {retrievingFile ? "Retrieving..." : "Retrieve"}
                    </button>
                </li>
            {/each}
        </ul>
    {:else if !loading}
        <p>No files found.</p>
    {/if}

    {#if retrievedFileUrl}
        <div class="retrieved-file">
            <h3>📄 Retrieved File</h3>
            <a href={retrievedFileUrl} target="_blank">{retrievedFileUrl}</a>
            <br />
            <iframe src={retrievedFileUrl} class="preview"></iframe>
        </div>
    {/if}
</div>

<style>
    .file-groups {
        margin-top: 30px;
    }


    .card-container {
        display: grid;
        grid-template-columns: repeat(3, minmax(200px, 1fr));
        gap: 15px;
        margin-top: 15px;
    }

    .card {
        padding: 15px;
        background: #f9f9f9;
        border: 1px solid #ddd;
        border-radius: 8px;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
        text-align: left;
    }

    .card h3 {
        margin: 0 0 10px;
        font-size: 18px;
        color: #333;
    }

    .card p {
        margin: 5px 0;
        font-size: 14px;
        color: #555;
    }

    .group-file-list {
        list-style-type: none;
        padding: 0;
        margin-top: 0px;
        font-size: 14px;
        color: #555;
        max-width: 100%;
    }

    .no-files {
        font-style: italic;
        color: #999;
    }

    .container {
        max-width: 500px;
        margin: 50px auto;
        padding: 20px;
        background: white;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
        border-radius: 10px;
        text-align: center;
    }

    .file-list {
        list-style-type: none;
        padding: 0;
        margin-top: 15px;
    }

    .file-list li {
        padding: 8px;
        border-bottom: 1px solid #ddd;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .retrieve-btn {
        background-color: #f59e0b;
        color: white;
        border: none;
        padding: 5px 10px;
        border-radius: 5px;
        cursor: pointer;
    }

    .retrieve-btn:hover {
        background: #d97706;
    }

    .retrieved-file {
        margin-top: 20px;
        padding: 10px;
        border: 2px solid #4caf50;
        background-color: #e8f5e9;
        border-radius: 5px;
    }

    .preview {
        width: 100%;
        height: 400px;
        margin-top: 10px;
        border: none;
    }

    .error {
        color: red;
        font-size: 14px;
    }
</style>
