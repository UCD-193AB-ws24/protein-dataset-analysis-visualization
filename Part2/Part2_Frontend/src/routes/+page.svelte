<script>
	import { oidcClient } from '$lib/auth';

	function startLogin() {
		oidcClient.signinRedirect();
	}
</script>

<div class="w-full bg-white">
	<!-- Hero Section -->
	<section class="w-full py-24 relative overflow-hidden">
		<div class="absolute inset-0 bg-green-50/80"></div>
		<div class="absolute inset-0 bg-gradient-to-br from-green-50/0 via-green-100/40 to-green-50/0 animate-gradient"></div>
		<div class="absolute inset-0 bg-gradient-to-tr from-green-50/0 via-green-100/30 to-green-50/0 animate-gradient-reverse"></div>
		<div class="max-w-5xl mx-auto px-8 relative">
			<div class="max-w-3xl mx-auto text-center">
				<h1 class="text-4xl md:text-5xl font-bold text-green-800 mb-6">
					Visualize lettuce protein similarity like never before.
				</h1>
				<p class="text-lg md:text-xl text-slate-600 mb-10">
					Upload, analyze, and compare genomic datasets across multiple
					genotypes. Gain insights through interactive, domain-specific
					visualizations.
				</p>
				<a href="/diagram" class="inline-flex items-center px-8 py-4 text-base font-medium text-white bg-green-600 rounded-lg hover:bg-green-700 transition-colors duration-200 shadow-md hover:shadow-lg">
					Start Visualizing
					<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="ml-2"><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></svg>
				</a>
			</div>
		</div>
	</section>

	<!-- Content Sections -->
	<section class="py-24 bg-white">
		<div class="max-w-6xl mx-auto px-8">
			<!-- Section 1 -->
			<div class="flex flex-col md:flex-row items-center gap-16 mb-24">
				<div class="md:w-1/2">
					<h2 class="text-2xl md:text-3xl font-bold text-green-800 mb-6">
						Why Protein Comparison?
					</h2>
					<p class="text-slate-600 mb-4">
						Traditional DNA tools fall short when studying
						resistance-related proteins in lettuce. Our tool fills that gap
						by providing specialized visualizations for protein sequence
						analysis.
					</p>
					<p class="text-slate-600">
						LocusCGVT enables researchers to identify patterns and
						relationships that may not be apparent through conventional
						genomic analysis methods.
					</p>
				</div>
				<div class="md:w-1/2">
					<div class="bg-green-50 rounded-xl p-10 flex items-center justify-center aspect-square max-w-[400px] mx-auto">
						<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-green-600"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/></svg>
					</div>
				</div>
			</div>

			<!-- Section 2 -->
			<div class="flex flex-col md:flex-row-reverse items-center gap-16 mb-24">
				<div class="md:w-1/2">
					<h2 class="text-2xl md:text-3xl font-bold text-green-800 mb-6">
						Multiple Comparison Modes
					</h2>
					<p class="text-slate-600 mb-4">
						Use general or domain-specific analysis to uncover consistent or
						conflicting connections between protein sequences across
						different lettuce genotypes.
					</p>
					<p class="text-slate-600">
						Our visualization engine highlights relationships and
						inconsistencies, making it easier to identify patterns relevant
						to your research.
					</p>
				</div>
				<div class="md:w-1/2">
					<div class="bg-green-50 rounded-xl p-10 flex items-center justify-center aspect-square max-w-[400px] mx-auto">
						<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-green-600">
							<path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/>
							<circle cx="12" cy="12" r="3"/>
						</svg>
					</div>
				</div>
			</div>

			<!-- Section 3 -->
			<div class="flex flex-col md:flex-row items-center gap-16">
				<div class="md:w-1/2">
					<h2 class="text-2xl md:text-3xl font-bold text-green-800 mb-6">
						No Account Required
					</h2>
					<p class="text-slate-600 mb-4">
						Use the visualization tool freely. Save data only when you're
						ready. Get started immediately without registration barriers.
					</p>
					<p class="text-slate-600">
						When you're ready to save your work, create an account to store
						and manage your analyses.
					</p>
				</div>
				<div class="md:w-1/2">
					<div class="bg-green-50 rounded-xl p-10 flex items-center justify-center aspect-square max-w-[400px] mx-auto">
						<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-green-600"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
					</div>
				</div>
			</div>
		</div>
	</section>
</div>

<style>
	@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

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

	@keyframes gradient {
		0% {
			background-position: 0% 50%;
		}
		50% {
			background-position: 100% 50%;
		}
		100% {
			background-position: 0% 50%;
		}
	}

	@keyframes gradient-reverse {
		0% {
			background-position: 100% 50%;
		}
		50% {
			background-position: 0% 50%;
		}
		100% {
			background-position: 100% 50%;
		}
	}

	.animate-gradient {
		background-size: 300% 300%;
		animation: gradient 8s ease infinite;
	}

	.animate-gradient-reverse {
		background-size: 300% 300%;
		animation: gradient-reverse 12s ease infinite;
	}

	p {
		font-size: 1.25rem;
		color: #555;
		margin-bottom: 1.5rem;
	}
</style>
