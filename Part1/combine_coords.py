import sys
import csv

def parse_data(data, coord_mapping):
    for row in data:
        protein_id, start, end, domain = row
        start, end = int(start), int(end)  # Convert to integers
        unique_domain = "{},{}".format(protein_id, domain)

        if unique_domain not in coord_mapping:
            coord_mapping[unique_domain] = [start, end]
        else:
            if start < coord_mapping[unique_domain][0]:
                coord_mapping[unique_domain][0] = start
            if end > coord_mapping[unique_domain][1]:
                coord_mapping[unique_domain][1] = end

def combine_coords(inputfile, outputfile):
    # Determine file type and read accordingly
    if inputfile.endswith('.csv'):
        delimiter = ','
    elif inputfile.endswith('.tsv'):
        delimiter = '\t'
    else:
        raise ValueError("Unsupported file format. Please use CSV or TSV.")

    coord_mapping = {}
    
    with open(inputfile, 'r') as infile:
        reader = csv.reader(infile, delimiter=delimiter)
        parse_data(reader, coord_mapping)

    with open(outputfile, 'w') as outfile:
        writer = csv.writer(outfile)
        for key, value in coord_mapping.items():
            protein_id, domain = key.split(',')
            writer.writerow([protein_id, value[0], value[1], domain])

# Usage
if len(sys.argv) != 3:
    print("Usage: python script.py <input_file> <output_file>")
    sys.exit(1)

input_file = sys.argv[1]
output_file = sys.argv[2]
combine_coords(input_file, output_file)
