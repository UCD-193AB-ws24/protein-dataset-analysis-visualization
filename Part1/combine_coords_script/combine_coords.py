import sys
import csv

def parse_data(data, coord_mapping):
    current_unique_domain = "a"
    for row in data:
        protein_id, start, end, domain = row
        start, end = int(start), int(end)  # Convert to integers
        unique_domain = "{},{}".format(protein_id, domain)

        if ((unique_domain + current_unique_domain[-1]) == current_unique_domain):
            unique_domain = current_unique_domain

        if unique_domain not in coord_mapping:
            coord_mapping[unique_domain] = [start, end]
            current_unique_domain = unique_domain
        else:
            if current_unique_domain != unique_domain:
                last_char = unique_domain[-1]
                try:
                    last_char = int(last_char)
                    unique_domain.append(str(int(last_char) + 1))
                except:
                     unique_domain += "2"
                current_unique_domain = unique_domain
                coord_mapping[unique_domain] = [start, end]
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
        writer = csv.writer(outfile, lineterminator = "\n")
        for key, value in coord_mapping.items():
            protein_id, domain = key.split(',')
            writer.writerow([protein_id, value[0], value[1], domain])

# Usage
if len(sys.argv) != 3:
    print("Usage: python combine_coords.py <input_file> <output_file>")
    sys.exit(1)

input_file = sys.argv[1]
output_file = sys.argv[2]
combine_coords(input_file, output_file)