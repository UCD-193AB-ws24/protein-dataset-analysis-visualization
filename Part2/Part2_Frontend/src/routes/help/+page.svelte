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

   <h2 class="text-2xl font-bold text-slate-800 mb-6">Input File Requirements: General Visualization</h2>
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
    <div class="bg-blue-50 p-6 rounded-lg mb-6">
                <h2 class="text-xl font-semibold text-slate-800 mb-3">The coordinates file will have the following columns, in the following order: name, protein_name, genome, Chromosome, position, and orientation.</h2>
                <ol class="list-decimal list-inside space-y-2 text-slate-600">
                    <li>The “name” column will contain the name of each gene, optionally including the species name. This column must match the column and row headers of the matrix file.</li>
                    <li>The protein_name” column will contain the name of the protein.</li>
                    <li>The “Chromosome” column contains what chromosome the gene is located in.</li>
                    <li>The “position” column contains the position of the gene within its chromosome. This column should only contain numeric values.</li>
                    <li>The “orientation” column contains the direction of the gene. Only the words “plus” or “minus” should be entered into this column. This will determine if a gene is facing left or right on the visualization.</li>
                </ol>
            </div>
  </ul>

  <p>
    In the matrix file, the top row and leftmost column must be identical. Each entry will contain the name of a gene, with the same name as in the coordinates file. All other entries will be a numerical percentage score (omit the “%” sign) between the gene in a row and the gene in the corresponding column.
  </p>

  <h2 class="text-2xl font-bold text-slate-800 mb-6">Input File Requirements: Domain-Specific Visualization</h2>

   <p>
    The domain-specific visualization mode allows for seeing similarities and differences between specific domains. It requires a single coordinates file and two to three matrix files (one for each domain being compared).
  </p>

  <p>
    The coordinates file may have two formats. In format 1, the file will indicate whether or not domains are present within genes. The following fields have the same requirements as in the general case: name, protein_name, genome, gene_type, position, and orientation.
  </p>

  <h2 class="text-xl font-bold text-slate-800 mb-6">Format 1</h2>
  <p>
    Indicates domain presence with "yes" or blank. Columns include: <strong>name</strong>,
    <strong>protein_name</strong>, <strong>genome</strong>, <strong>gene_type</strong>,
    <strong>position</strong>, <strong>orientation</strong>, and domain presence columns.
  </p>
  <div class="image-placeholder">(image of Format 1 headers)</div>

  <h2 class="text-xl font-bold text-slate-800 mb-6">Format 2</h2>
  <p>
    Indicates domain start and end coordinates using columns like domain1_start and domain1_end. Values must
    be numeric.
  </p>
  <div class="image-placeholder">(image of Format 2 headers)</div>

  <h2 class="text-2xl font-bold text-slate-800 mb-6">Types of Connections</h2>
  <ul>
    <p>
    <li><strong>Solid colored lines</strong> (except red) indicate a connection that is reciprocal between two genes. This means that when two genomes are compared, the strongest connection is the same for the forward comparison as for the reverse comparison.</li>
    <li><strong>Grey dashed lines</strong> indicate a connection that is not reciprocal between two genes. This means that when two genomes are compared, the connection between the two genes is only the strongest in either the forward or backwards direction, but not both.</li>
    <li> Domain-specific visualizations feature two more types of connections: colored dashed lines and solid red lines.</li>
    <li><strong>Colored dashed lines</strong> indicate a connection that exists in all domains, is reciprocal in at least one domain, and is nonreciprocal (grey dashed) in the other domains.</li>
    <li><strong>Solid red lines</strong> indicate a connection that is inconsistent between domains. This means that a reciprocal connection exists in at least one domain, but the connection between the same genes is absent in at least one domain.</li>  
</p>
</ul>

  <h2 class="text-2xl font-bold text-slate-800 mb-6">How Gene Groups (of the Same Color) Are Formed</h2>
  <ul>
    <p>
    Genes and connections are colored according to reciprocal similarity. Red is reserved for showing inconsistencies in the domain comparison feature. If a gene is colored dark grey, that indicates that there are no reciprocal connections between it and the genes of the genomes it is being compared with.
    <li>(insert example of dark grey node)</li>
</p>  
<p>
    If a gene is colored light grey, that means the domain being visualized is not present in that gene. For example, this is the comparison for the TIR domain of these genes. ViAE’s third gene is light grey in this diagram, which means that gene does not have a TIR domain.
<li>(insert example of light grey node)</li>
</p>
<p>
    In order for a gene to be absent: it must not appear in the corresponding matrix file (it’s not enough if only the coordinates file indicates its absence).
</p>
</ul>

  <p>
    For a gene to be considered absent, it must be missing from the corresponding matrix file, not just the
    coordinates file.
  </p>

   </div>
    </div>
</div>

<style>
    /* Add any additional styles here if needed */
</style>