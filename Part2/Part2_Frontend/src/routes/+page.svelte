<script>
	import { oidcClient } from '$lib/auth';

	function startLogin() {
		oidcClient.signinRedirect();
	}
</script>

<div class="landing">
	<div class="overlay"></div>
	<div class="content">
		<h1>GeneLCGVT</h1>
		<p>
			The Locus Comparitive Genomics Visulization Tool, the only tool that creates visualizations of
			gene and domain comparisons across organisms
		</p>
		<div class="buttons">
			<button on:click={startLogin}>Sign in with AWS</button>
		</div>
	</div>
</div>

<style>
	@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

	.landing {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		min-height: 100vh;
		padding: 2rem;
		text-align: center;
		background: url('https://images.unsplash.com/photo-1612178993494-1c2d1f1c9376?auto=format&fit=crop&w=1950&q=80')
			center/cover no-repeat;
		position: relative;
		overflow: hidden;
	}

	.overlay {
		position: absolute;
		inset: 0;
		background-color: rgba(255, 255, 255, 0.6);
		backdrop-filter: blur(6px);
		z-index: 1;
	}

	.content {
		position: relative;
		z-index: 2;
		max-width: 600px;
		padding: 2.5rem;
		background-color: rgba(255, 255, 255, 0.95);
		border-radius: 24px;
		box-shadow: 0 20px 40px rgba(0, 0, 0, 0.15);
		animation: fadeIn 0.8s ease-out;
	}

	@keyframes fadeIn {
		from {
			opacity: 0;
			transform: scale(0.95);
		}
		to {
			opacity: 1;
			transform: scale(1);
		}
	}

	h1 {
		font-size: 3rem;
		margin-bottom: 1rem;
		color: #00b894;
		background: linear-gradient(to right, #00cec9, #0984e3);
		-webkit-background-clip: text;
		-webkit-text-fill-color: transparent;
	}

	p {
		font-size: 1.25rem;
		color: #555;
		margin-bottom: 1.5rem;
	}

	.buttons {
		display: flex;
		justify-content: center;
		gap: 1rem;
	}

	button {
		padding: 0.9rem 1.7rem;
		font-size: 1rem;
		font-weight: 600;
		border: none;
		border-radius: 9999px;
		background: linear-gradient(to right, #00cec9, #0984e3);
		color: white;
		cursor: pointer;
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
		transition:
			transform 0.2s ease,
			box-shadow 0.2s ease;
	}

	button:hover {
		transform: translateY(-3px);
		box-shadow: 0 8px 20px rgba(0, 0, 0, 0.25);
	}
</style>
