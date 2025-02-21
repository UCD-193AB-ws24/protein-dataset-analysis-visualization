import sys

def simplify_header(header):
    """
    Simplifies the header by keeping only the first four tokens separated by underscores.
    """
    parts = header.split("_")
    return "_".join(parts[:4])

def process_fasta(input_file, output_file):
    """
    Reads an input FASTA file, modifies the headers, and writes to an output FASTA file.
    """
    with open(input_file, 'r') as infile, open(output_file, 'w') as outfile:
        for line in infile:
            if line.startswith('>'):
                simplified_header = simplify_header(line.strip().lstrip('>'))
                outfile.write(f'>{simplified_header}\n')
            else:
                outfile.write(line)

if __name__ == "__main__":
    input_path = "./Dandie_helixer_Rprotein.fasta"
    output_path = "./Dandie_helixer_Rprotein_simplified.fasta"
    process_fasta(input_path, output_path)
    print(f"Simplified FASTA file saved as: {output_path}")
