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
    if len(sys.argv) < 2:
        print("Usage: python simplify_headers.py <input_file_name> <output_file_name>")
        sys.exit(1)

    input_file = sys.argv[1]
    if (len(sys.argv)) == 3:
        output_file = sys.argv[2]
    else:
        output_file = sys.argv[1].split(".")[0] + "_simplified.fasta"
        
    process_fasta(input_file, output_file)
    print(f"Simplified FASTA file saved as: {output_file}")
