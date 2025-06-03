<script>
	import { oidcClient } from '$lib/auth';

	function startLogin() {
		oidcClient.signinRedirect();
	}
</script>

<svelte:head>
	<title>LocusCGVT - Locus Comparative Genomics Visualization Tool</title>
	<meta name="description" content="Combine phylogenetic and syntenic information to visualize genes/proteins in genomic regions and their relationships across genotypes or species." />
</svelte:head>

<div class="w-full bg-white">
	<!-- Hero Section -->
	<section class="w-full py-20 relative overflow-hidden">
		<div class="absolute inset-0 bg-gradient-to-br from-green-50 via-white to-green-50"></div>
		<div class="max-w-6xl mx-auto px-8 relative">
			<div class="max-w-4xl mx-auto text-center">
				<h1 class="text-5xl md:text-6xl font-bold text-green-800 mb-6">
					LocusCGVT
				</h1>
				<p class="text-xl md:text-2xl text-green-700 font-medium mb-4">
					Locus Comparative Genomics Visualization Tool
				</p>
				<p class="text-lg md:text-xl text-slate-600 mb-10 max-w-3xl mx-auto">
					Visualize genes/proteins in genomic regions and their relationships across genotypes or species,
					enabling identification of homologs/orthologs and gene diversification events.
				</p>
				<div class="flex flex-col sm:flex-row gap-4 justify-center items-center">
					<a href="/diagram" class="inline-flex items-center px-8 py-4 text-base font-medium text-white bg-green-600 rounded-lg hover:bg-green-700 transition-colors duration-200 shadow-md hover:shadow-lg cursor-pointer">
						Start Analyzing
						<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="ml-2">
							<path d="M5 12h14"/>
							<path d="m12 5 7 7-7 7"/>
						</svg>
					</a>
					<button
						on:click={startLogin}
						class="inline-flex items-center px-8 py-4 text-base font-medium text-green-600 bg-white border-2 border-green-600 rounded-lg hover:bg-green-50 transition-colors duration-200 cursor-pointer"
					>
						<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="mr-2">
							<path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/>
							<circle cx="12" cy="7" r="4"/>
						</svg>
						Sign Up to Save Projects
					</button>
				</div>
			</div>
		</div>
	</section>

	<!-- Visualization Showcase -->
	<section class="py-16 bg-slate-50">
		<div class="max-w-6xl mx-auto px-8">
			<div class="text-center mb-12">
				<h2 class="text-3xl md:text-4xl font-bold text-slate-800 mb-4">
					See Your Data Come to Life
				</h2>
				<p class="text-lg text-slate-600 max-w-3xl mx-auto">
					LocusCGVT transforms complex genomic similarity matrices into intuitive visualizations
					that reveal patterns and relationships across genomes.
				</p>
			</div>

			<!-- Actual screenshot of the tool -->
			<div class="max-w-5xl mx-auto">
				<div class="bg-white rounded-lg shadow-md p-4">
					<img
						src="/images/locuscgvt-diagram.png"
						alt="LocusCGVT genomic visualization showing gene relationships across multiple genomes"
						class="w-full h-auto rounded-md"
					/>
				</div>
				<p class="text-center text-sm text-slate-500 mt-4">
					Interactive visualization showing gene relationships across multiple genomes with customizable filtering and analysis options
				</p>
			</div>
		</div>
	</section>

	<!-- Main Features -->
	<section class="py-20 bg-white">
		<div class="max-w-6xl mx-auto px-8">
			<div class="text-center mb-16">
				<h2 class="text-3xl md:text-4xl font-bold text-slate-800 mb-4">
					Powerful Analysis Modes
				</h2>
			</div>

			<div class="grid md:grid-cols-2 gap-12 items-start">
				<!-- General Analysis -->
				<div class="space-y-6">
					<div class="flex items-center gap-4 mb-6">
						<div class="w-16 h-16 bg-green-100 rounded-xl flex items-center justify-center">
							<!-- Single document icon -->
							<svg fill="none" height="32" viewBox="0 0 66 86" width="25" xmlns="http://www.w3.org/2000/svg" class="text-green-600">
								<rect height="80" rx="2" stroke="currentColor" stroke-width="6" width="60" x="3" y="3"/>
								<path d="M15 27H50" stroke="currentColor" stroke-linecap="round" stroke-width="4"/>
								<path d="M15 55H37" stroke="currentColor" stroke-linecap="round" stroke-width="4"/>
								<path d="M15 41H50" stroke="currentColor" stroke-linecap="round" stroke-width="4"/>
							</svg>
						</div>
						<h3 class="text-2xl font-bold text-slate-800">General Analysis</h3>
					</div>
					<p class="text-slate-600 text-lg leading-relaxed">
						LocusCGVT displays the similarity between the genes/proteins from one locus
						and the genes from the same region in other organisms (accession/genotype/species).
						Homologs or orthologs between different genomes are displayed as reciprocal connections.
					</p>
					<p class="text-slate-600 text-lg leading-relaxed">
						LocusCGVT enables researchers to identify patterns and relationships that may not be
						apparent through conventional comparative genomic analysis, and allows the fast
						identification of gene duplications, deletions, and rearrangements.
					</p>
				</div>

				<!-- Domain-Specific Analysis -->
				<div class="space-y-6">
					<div class="flex items-center gap-4 mb-6">
						<div class="w-16 h-16 bg-blue-100 rounded-xl flex items-center justify-center">
							<!-- Stacked documents icon -->
							<svg fill="none" height="32" viewBox="0 0 85 106" width="25" xmlns="http://www.w3.org/2000/svg" class="text-blue-600">
								<rect height="80" rx="2" stroke="currentColor" stroke-width="6" width="60" x="3" y="23"/>
								<path d="M15 47H50" stroke="currentColor" stroke-linecap="round" stroke-width="4"/>
								<path d="M15 75H37" stroke="currentColor" stroke-linecap="round" stroke-width="4"/>
								<path d="M15 61H50" stroke="currentColor" stroke-linecap="round" stroke-width="4"/>
								<path d="M12 23V13" stroke="currentColor" stroke-linecap="round" stroke-width="6"/>
								<path d="M72 93H64" stroke="currentColor" stroke-linecap="round" stroke-width="6"/>
								<path d="M12 13H72" stroke="currentColor" stroke-linecap="round" stroke-width="6"/>
								<path d="M72.9219 92.9946L72 12.9999" stroke="currentColor" stroke-linecap="round" stroke-width="6"/>
								<path d="M21 13V3" stroke="currentColor" stroke-linecap="round" stroke-width="6"/>
								<path d="M81 83H73" stroke="currentColor" stroke-linecap="round" stroke-width="6"/>
								<path d="M21 3H81" stroke="currentColor" stroke-linecap="round" stroke-width="6"/>
								<path d="M81.9219 82.9946L81 2.99994" stroke="currentColor" stroke-linecap="round" stroke-width="6"/>
							</svg>
						</div>
						<h3 class="text-2xl font-bold text-slate-800">Domain-Specific Analysis</h3>
					</div>
					<p class="text-slate-600 text-lg leading-relaxed">
						The domain-specific analysis mode is an innovative tool for visualizing regions
						containing genes with canonical domains, such as NLRs and RLKs. By combining
						domain-specific inputs, LocusCGVT can quickly display domain fusion and duplications.
					</p>
					<p class="text-slate-600 text-lg leading-relaxed">
						This mode highlights domain shuffling events (inconsistencies between domain
						relationships from a protein), making it easier to identify complex evolutionary
						patterns in multi-domain proteins.
					</p>
				</div>
			</div>
		</div>
	</section>

	<!-- Call to Action -->
	<section class="py-20 bg-green-600">
		<div class="max-w-4xl mx-auto px-8 text-center">
			<h2 class="text-3xl md:text-4xl font-bold text-white mb-6">
				Ready to Visualize Your Genomic Data?
			</h2>
			<p class="text-xl text-green-100 mb-8 max-w-2xl mx-auto">
				Start analyzing immediately with no account required. Create an account when you're ready to save and manage your analyses.
			</p>
			<div class="flex flex-col sm:flex-row gap-4 justify-center items-center">
				<a href="/diagram" class="inline-flex items-center px-8 py-4 text-lg font-medium text-green-600 bg-white rounded-lg hover:bg-slate-50 transition-colors duration-200 shadow-lg cursor-pointer">
					Start Analysis
					<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="ml-2">
						<path d="M5 12h14"/>
						<path d="m12 5 7 7-7 7"/>
					</svg>
				</a>
				<button
					on:click={startLogin}
					class="inline-flex items-center px-8 py-4 text-lg font-medium text-white border-2 border-white rounded-lg hover:bg-green-700 transition-colors duration-200 cursor-pointer"
				>
					<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="mr-2">
						<path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/>
						<circle cx="12" cy="7" r="4"/>
					</svg>
					Create Account
				</button>
			</div>
		</div>
	</section>
</div>

<style>
	@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
</style>
