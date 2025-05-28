<div class="w-[95%] max-w-[1600px] mx-auto py-8">
    <div class="max-w-3xl mx-auto">
        <h1 class="text-4xl font-bold text-slate-800 mb-6">Help & Documentation</h1>
        <div class="prose prose-lg">
            <p class="text-slate-600 mb-4">
                Welcome to the LocusCGVT help center. This section is currently under development and will soon contain comprehensive documentation and guides for using our platform.
            </p>
            <div class="bg-blue-50 p-6 rounded-lg mb-6">
                <h2 class="text-xl font-semibold text-slate-800 mb-3">Quick Start Guide</h2>
                <ol class="list-decimal list-inside space-y-2 text-slate-600">
                    <li>Upload your protein sequence data through the Dashboard.</li>
                    <li>Navigate to the Visualize page to create your first comparison.</li>
                    <li>Use the interactive tools to explore relationships between sequences.</li>
                    <li>Save your work when you're ready (requires an account).</li>
                </ol>
            </div>
            <p>
    Thank you for using the Locus Comparative Genomics Visualization Tool! This tool can be used to
    graphically compare the genes of two or three genomes at a time based on percentage similarity. Two
    types of visualizations can be generated: general (gene-level) and domain-specific.
  </p>
  <p>
    In both the general and domain-specific cases, two types of files are required as input: coordinates files
    and matrix files. Both types of files must be Excel or csv or tsv files and they must be in a specific format
    in order for the tool to work.
  </p>

   <h2>Input File Requirements: General Visualization</h2>
  <p>
    The general visualization requires a single coordinates file and a single matrix file as input. These files
    must contain at least two genomes to compare and must have matching gene names.
  </p>

   <p>
    The coordinates file will have the following columns, in the following order: <strong>name</strong>,
    <strong>protein_name</strong>, <strong>genome</strong>, <strong>Chromosome</strong>,
    <strong>position</strong>, and <strong>orientation</strong>.
  </p>

  <ul>
    <li>The “name” column will contain the name of each gene, optionally including the species name. This column must match the column and row headers of the matrix file.</li>
    <li>The protein_name” column will contain the name of the protein.</li>
    <li>The “Chromosome” column contains what chromosome the gene is located in.</li>
    <li>The “position” column contains the position of the gene within its chromosome. This column should only contain numeric values.</li>
    <li>The “orientation” column contains the direction of the gene. Only the words “plus” or “minus” should be entered into this column. This will determine if a gene is facing left or right on the visualization.</li>
  </ul>

  <p>
    In the matrix file, the top row and leftmost column must be identical. Each entry will contain the name of a gene, with the same name as in the coordinates file. All other entries will be a numerical percentage score (omit the “%” sign) between the gene in a row and the gene in the corresponding column.
  </p>

  <h2>Input File Requirements: Domain-Specific Visualization</h2>
        </div>
    </div>
</div>

<style>
    /* Add any additional styles here if needed */
</style>