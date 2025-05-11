<script>
  
</script>

<nav>
    <ul>
        <li><a href="/dashboard/upload">📤 Upload File</a></li>
        <li><a href="/dashboard/files">📂Files</a></li>
        <li><a href="/dashboard/diagram">📊diagram</a></li>
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
</style>

<slot />
