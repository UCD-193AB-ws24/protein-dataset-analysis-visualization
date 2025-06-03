<svelte:head>
	<title>About LocusCGVT - Locus Comparative Genomics Visualization Tool</title>
	<meta name="description" content="Learn about LocusCGVT, The Michelmore Lab, and our development team." />
</svelte:head>

<div class="w-full bg-white">
	<!-- Header Section -->
	<section class="w-full py-12 bg-gradient-to-r from-green-50 to-green-100">
		<div class="max-w-6xl mx-auto px-8">
			<div class="text-center">
				<h1 class="text-4xl md:text-5xl font-bold text-green-800 mb-4">
					About LocusCGVT
				</h1>
				<p class="text-lg text-green-700">
					Discover the tool, the lab behind it, and the team that brought it to life
				</p>
			</div>
		</div>
	</section>

	<!-- About the Tool Section -->
	<section class="py-16 bg-white">
		<div class="max-w-6xl mx-auto px-8">
			<div class="grid lg:grid-cols-2 gap-8 items-center">
				<!-- Text Content - Left Side -->
				<div class="space-y-6">
					<h2 class="text-3xl md:text-4xl font-bold text-slate-800 mb-6">
						About the Tool
					</h2>
					<p class="text-lg text-slate-600 leading-relaxed">
						LocusCGVT combines phylogenetic and syntenic information to visualize
						genes/proteins in genomic regions and their relationships between different
						genotypes or species, enabling identification of homologs/orthologs and
						gene diversification events.
					</p>

					<p class="text-slate-600 leading-relaxed">
						The tool displays similarity between genes/proteins from one locus and genes
						from the same region in other organisms, with homologs or orthologs shown
						as reciprocal connections. This enables researchers to quickly identify
						gene duplications, deletions, and rearrangements that may not be apparent
						through conventional analysis.
					</p>

					<div class="bg-green-50 p-6 rounded-lg">
						<h4 class="text-lg font-semibold text-green-800 mb-2">File Format Support</h4>
						<p class="text-green-700">
							We accept CSV, TSV, and Excel files containing gene distance matrices and
							gene information including chromosome position, gene type, and orientation.
						</p>
					</div>
				</div>

				<!-- Image - Right Side -->
				<div class="flex justify-center">
					<div class="bg-white rounded-lg shadow-lg overflow-hidden max-w-lg w-full">
						<img
							src="/images/locuscgvt-diagram.png"
							alt="LocusCGVT genomic visualization"
							class="w-full h-auto"
						/>
					</div>
				</div>
			</div>
		</div>
	</section>

	<!-- About the Lab Section -->
	<section class="py-16 bg-green-50">
		<div class="max-w-6xl mx-auto px-8">
			<div class="grid lg:grid-cols-2 gap-8 items-center">
				<!-- Image - Left Side -->
				<div class="flex justify-center">
					<div class="bg-white rounded-lg shadow-lg overflow-hidden max-w-lg w-full">
						<img
							src="/images/michelmore_lab.jpg"
							alt="The Michelmore Lab"
							class="w-full h-auto"
						/>
					</div>
				</div>

				<!-- Text Content - Right Side -->
				<div class="space-y-6">
					<h2 class="text-3xl md:text-4xl font-bold text-slate-800 mb-6">
						About The Michelmore Lab
					</h2>
					<p class="text-lg text-slate-600 leading-relaxed">
						Located within the UC Davis Genome Center, The Michelmore Lab is at the
						forefront of plant genomics research with access to cutting-edge sequencing
						and analysis technologies.
					</p>

					<div class="space-y-4">
						<h3 class="text-xl font-semibold text-slate-800">Key Research Areas</h3>
						<ul class="space-y-2 text-slate-600">
							<li class="flex items-start">
								<span class="text-green-600 mr-2">•</span>
								Comparative and functional genomics of disease resistance genes in plants
							</li>
							<li class="flex items-start">
								<span class="text-green-600 mr-2">•</span>
								Classical and molecular genetics of lettuce and its pathogens
							</li>
							<li class="flex items-start">
								<span class="text-green-600 mr-2">•</span>
								Development of novel technologies for crop improvement
							</li>
							<li class="flex items-start">
								<span class="text-green-600 mr-2">•</span>
								Genomics of oomycete pathogens causing downy mildews
							</li>
						</ul>
					</div>

					<div class="bg-green-100 p-6 rounded-lg">
						<h4 class="text-lg font-semibold text-green-800 mb-2">Notable Achievements</h4>
						<p class="text-green-700 mb-3">
							The lab has sequenced and assembled multiple high-quality plant genomes,
							including a telomere-to-telomere assembly of lettuce, and is currently
							developing pan-genomic resources.
						</p>
						<p class="text-green-700">
							The lab is highly collaborative and welcomes partnerships with academic
							and private sector organizations focused on increasing global food security.
						</p>
					</div>
				</div>
			</div>
		</div>
	</section>

	<!-- About Us Section -->
	<section class="py-16 bg-white">
		<div class="max-w-6xl mx-auto px-8">
			<div class="grid lg:grid-cols-2 gap-8 items-center">
				<!-- Text Content - Left Side -->
				<div class="space-y-6">
					<h2 class="text-3xl md:text-4xl font-bold text-slate-800 mb-6">
						About Our Development Team
					</h2>
					<p class="text-lg text-slate-600 leading-relaxed">
						As part of the Capstone Project Class (ECS 193) at UC Davis, our team
						developed LocusCGVT to bridge the gap between complex matrix comparison
						outputs from existing bioinformatics programs and researchers seeking
						intuitive ways to understand their genomic data.
					</p>

					<div class="space-y-4">
						<h3 class="text-xl font-semibold text-slate-800">Our Mission</h3>
						<p class="text-slate-600 leading-relaxed">
							We're passionate about the intersection of computer science, software
							engineering, and biology. Our goal was to build a tool that's both
							easy for researchers to use and genuinely valuable for advancing
							genomic research.
						</p>
					</div>

					<div class="bg-green-50 p-6 rounded-lg">
						<h4 class="text-lg font-semibold text-green-800 mb-3">Join Us at the Showcase!</h4>
						<p class="text-green-700">
							We're presenting LocusCGVT at the <strong>Engineering Design Showcase</strong> on June 5th, 2025 - come check us out!
						</p>
					</div>
				</div>

				<!-- Team Photos Grid - Right Side -->
				<div class="flex justify-center">
					<div class="bg-green-50 rounded-lg p-8 max-w-lg w-full">
						<h4 class="text-xl font-semibold text-slate-800 mb-6 text-center">Meet Our Team</h4>
						<div class="grid grid-cols-2 gap-6">
							<!-- KB K. -->
							<div class="text-center">
								<div class="bg-white rounded-lg shadow-md overflow-hidden">
									<img
										src="/images/AggieCard_Profile_Pic.jpg"
										alt="KB K. - Team Member"
										class="w-full h-48 object-cover"
									/>
								</div>
								<p class="mt-2 text-sm font-medium text-slate-700">KB K.</p>
							</div>

							<!-- Vishal K. -->
							<div class="text-center">
								<div class="bg-white rounded-lg shadow-md overflow-hidden">
									<img
										src="/images/Vishal_Koppuru_Resized.jpg"
										alt="Vishal K. - Team Member"
										class="w-full h-48 object-cover"
									/>
								</div>
								<p class="mt-2 text-sm font-medium text-slate-700">Vishal K.</p>
							</div>

							<!-- Gurpreet S. -->
							<div class="text-center">
								<div class="bg-white rounded-lg shadow-md overflow-hidden">
									<img
										src="/images/business_casual_photo_1.jpeg"
										alt="Gurpreet S. - Team Member"
										class="w-full h-48 object-cover object-[center_30%]"
									/>
								</div>
								<p class="mt-2 text-sm font-medium text-slate-700">Gurpreet S.</p>
							</div>

							<!-- Balint S. -->
							<div class="text-center">
								<div class="bg-white rounded-lg shadow-md overflow-hidden">
									<img
										src="/images/Balint_Szigeti_Csucs_Personal_Photo.jpeg"
										alt="Balint S. - Team Member"
										class="w-full h-48 object-cover object-top"
									/>
								</div>
								<p class="mt-2 text-sm font-medium text-slate-700">Balint S.</p>
							</div>
						</div>
					</div>
				</div>
			</div>
		</div>
	</section>

	<!-- Call to Action -->
	<section class="py-16 bg-green-600">
		<div class="max-w-4xl mx-auto px-8 text-center">
			<h2 class="text-3xl font-bold text-white mb-4">
				Ready to Explore LocusCGVT?
			</h2>
			<p class="text-xl text-green-100 mb-8">
				Start analyzing your genomic data with our intuitive visualization tools
			</p>
			<a href="/diagram" class="inline-flex items-center px-8 py-4 text-lg font-medium text-green-600 bg-white rounded-lg hover:bg-slate-50 transition-colors duration-200 shadow-lg cursor-pointer">
				Start Analysis
				<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="ml-2">
					<path d="M5 12h14"/>
					<path d="m12 5 7 7-7 7"/>
				</svg>
			</a>
		</div>
	</section>
</div>

<style>
	@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=svg');
</style>