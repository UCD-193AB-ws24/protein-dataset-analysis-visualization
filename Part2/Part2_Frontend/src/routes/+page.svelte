<script>
    import { goto } from "$app/navigation";

    function goToLogin() {
        goto("/login");
    }
</script>

<div class="container">
    <h1>👋 Welcome</h1>

    <button class="btn login-btn" on:click={goToLogin}>Login</button>
</div>

<style>
    .container {
        max-width: 500px;
        margin: 100px auto;
        padding: 40px;
        background: white;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        border-radius: 15px;
        text-align: center;
        animation: fadeIn 0.6s ease-in-out;
    }

    h1 {
        font-size: 2rem;
        color: #333;
        margin-bottom: 10px;
    }

    .subtitle {
        color: #555;
        font-size: 1.2rem;
        margin-bottom: 20px;
    }

    .btn {
        font-size: 1.2rem;
        padding: 12px 20px;
        border-radius: 8px;
        border: none;
        cursor: pointer;
        transition: background 0.3s;
    }

    .login-btn {
        background-color: #3b82f6;
        color: white;
    }

    .login-btn:hover {
        background-color: #2563eb;
    }

    @keyframes fadeIn {
        from {
            opacity: 0;
            transform: translateY(-10px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
</style>
