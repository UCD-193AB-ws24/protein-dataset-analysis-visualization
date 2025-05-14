<script>
    import { oidcClient, signOutRedirect } from "$lib/auth";

    async function handleSignOut() {
        await signOutRedirect();
	}
    let isAuthenticated = false;
    const userPromise = oidcClient.getUser();

    userPromise.then(user => {
      if (user && !user.expired) {
        isAuthenticated = true;
      }
    });
</script>

<nav>
    <ul>
        <li><a href="/dashboard/files">📂 Files</a></li>
        <li><a href="/dashboard/diagram">📊 Diagram</a></li>
        {#if isAuthenticated}
            <button on:click={handleSignOut}>Log out</button>
        {/if}
    </ul>
</nav>

<style>
    nav {
        background: #1e293b;
        padding: 15px;
        text-align: center;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    ul {
        list-style: none;
        display: flex;
        justify-content: center;
        gap: 25px;
        padding: 0;
    }

    li {
        display: inline;
    }

    a {
        color: white;
        text-decoration: none;
        font-size: 18px;
        font-weight: bold;
        transition: color 0.3s ease;
    }

    a:hover {
        color: #60a5fa;
    }

    button {
        background-color: #3b82f6;
        color: white;
        border: none;
        padding: 10px 15px;
        border-radius: 5px;
        cursor: pointer;
        transition: background 0.3s;
    }
</style>

<slot />