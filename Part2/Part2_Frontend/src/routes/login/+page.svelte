<script>
	import { goto } from '$app/navigation';
	import { API_BASE_URL } from '$lib/api';

	let username = '';
	let password = '';
	let message = '';
	let loading = false;

	async function handleLogin() {
		message = '';

		try {
			const response = await fetch(
				`${API_BASE_URL}/login`,
				{
					method: 'POST',
					headers: {
						'Content-Type': 'application/json'
					},
					body: JSON.stringify({ username, password })
				}
			);

			if (!response.ok) {
				throw new Error('Login failed');
			}

			const result = await response.json();

			// Store username in localStorage
			localStorage.setItem('username', username);

			message = '✅ Login successful!';
			setTimeout(() => goto('/dashboard/files'), 1000); // Redirect after 1s
		} catch (error) {
			message = `${error.message}`;
		}
	}
</script>

<main class="container">
	<h2>Login</h2>
	<p class="subtitle">Welcome back! Please enter your credentials.</p>
	<p>Backend API URL: {API_BASE_URL}</p>

	<form on:submit|preventDefault={handleLogin}>
		<div class="input-group">
			<label for="username">👤 Username</label>
			<input type="text" id="username" bind:value={username} required />
		</div>

		<div class="input-group">
			<label for="password">🔒 Password</label>
			<input type="password" id="password" bind:value={password} required />
		</div>

		<button type="submit" class="btn" disabled={loading}> Login </button>
	</form>

	{#if message}
		<p class={message.includes('✅') ? 'success' : 'error'}>{message}</p>
	{/if}
</main>

<style>
	/* Container */
	.container {
		max-width: 400px;
		margin: 50px auto;
		padding: 30px;
		background: white;
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
		border-radius: 12px;
		text-align: center;
		animation: fadeIn 0.6s ease-in-out;
	}

	/* Title */
	h2 {
		font-size: 2rem;
		color: #333;
		margin-bottom: 5px;
	}

	.subtitle {
		color: #555;
		font-size: 1rem;
		margin-bottom: 20px;
	}

	/* Input fields */
	.input-group {
		text-align: left;
		margin-bottom: 15px;
	}

	label {
		display: block;
		font-size: 1rem;
		margin-bottom: 5px;
		color: #444;
	}

	input {
		width: 100%;
		padding: 10px;
		border: 2px solid #ddd;
		border-radius: 8px;
		font-size: 1rem;
		transition: border 0.3s;
	}

	input:focus {
		border-color: #3b82f6;
		outline: none;
	}

	/* Button */
	.btn {
		width: 100%;
		padding: 12px;
		font-size: 1.1rem;
		border-radius: 8px;
		border: none;
		cursor: pointer;
		background-color: #3b82f6;
		color: white;
		transition: background 0.3s;
	}

	.btn:hover {
		background-color: #2563eb;
	}

	.btn:disabled {
		background-color: #aaa;
		cursor: not-allowed;
	}

	/* Messages */
	.success {
		color: green;
		font-size: 1rem;
		margin-top: 10px;
	}

	.error {
		color: red;
		font-size: 1rem;
		margin-top: 10px;
	}

	/* Animation */
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
