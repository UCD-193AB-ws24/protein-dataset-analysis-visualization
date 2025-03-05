<script>
</script>

<nav>
    <ul>
        <li><a href="/">🏠 Home</a></li>
        <li><a href="/diagram">📈 Diagram</a></li>
        <li><a href="/upload">📤 Upload File</a></li>
        <li><a href="/retrieve">🔍 Retrieve File</a></li>
    </ul>
</nav>

<style>
    nav {
        background: #1e293b;
        padding: 15px;
        text-align: center;
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
