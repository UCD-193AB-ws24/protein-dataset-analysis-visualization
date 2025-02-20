import sys
import pandas as pd

def parse_dataframe(df, coord_mapping):
    for _, row in df.iterrows():
        protein_id, start, end, domain = row
        unique_domain = f"{protein_id},{domain}"

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
        df = pd.read_csv(inputfile, header=None, names=['protein_id', 'start', 'end', 'domain'])
    elif inputfile.endswith('.xlsx'):
        df = pd.read_excel(inputfile, header=None, names=['protein_id', 'start', 'end', 'domain'])
    else:
        raise ValueError("Unsupported file format. Please use CSV or XLSX.")

    coord_mapping = {}
    parse_dataframe(df, coord_mapping)

    output_lines = []
    for key, value in coord_mapping.items():
        protein_id, domain = key.split(',')
        output_lines.append(f"{protein_id},{value[0]},{value[1]},{domain}\n")

    with open(outputfile, 'w') as output:
        output.writelines(output_lines)

# Usage
input_file = sys.argv[1]  # or 'your_input_file.csv'
output_file = sys.argv[2]
combine_coords(input_file, output_file)

