import sys


def parse_line(line, coord_mapping):
    if line.strip():
        # print(line)
        protein_id, start, end, domain = line.split(',')
        unique_domain = protein_id + ',' + domain

        # New Coordinate + domain
        if unique_domain not in coord_mapping:
            coord_mapping[protein_id + ',' + domain] = [start, end]
        # Old Coordinate, need to see if replacement necessary
        else:
            if start < coord_mapping[unique_domain][0]:
                coord_mapping[unique_domain][0] = start
            if end > coord_mapping[unique_domain][1]:
                coord_mapping[unique_domain][1] = end


def combine_coords(coordinates, output_file):

    coord_mapping = {}

    # Read coordinates file
    with open(coordinates, 'r') as mapping:
        coord_lines = mapping.readlines()
        for line in coord_lines:
            parse_line(line, coord_mapping)

    output_lines = []
    # print(coord_mapping)
    for key, value in coord_mapping.items():
        protein_id, domain = key.split(',')
        output_lines.append(protein_id + ',' + value[0] + ',' + value[1] + ',' + domain)

    with open(output_file, 'w') as output:
        output.writelines(output_lines)


combine_coords(sys.argv[1], sys.argv[2])

    
