import pandas as pd

# File paths
fasta_file = "Dandie_helixer_Rprotein.fasta"
xlsx_file = "Dandie_conversion_list.xlsx"
output_fasta = "Simplified_Dandie_helixer_Rprotein.fasta"

# Read the conversion table from the Excel file
df = pd.read_excel(xlsx_file, header=None)
name_map = dict(zip(df[1], df[0]))  # column 1 has original names and column 0 has simplified names

# Process the FASTA file and replace names
with open(fasta_file, "r", encoding="utf-8", errors="replace") as infile, open(output_fasta, "w", encoding="utf-8") as outfile:
    for line in infile:
        if line.startswith(">"):
            original_name = line[1:].strip().split()[0]
            simplified_name = name_map.get(original_name, original_name)
            outfile.write(f">{simplified_name}\n")
        else:
            outfile.write(line)

print(f"Simplified FASTA file has been generated: {output_fasta}")