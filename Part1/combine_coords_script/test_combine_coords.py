import sys

def test():
    correct_file = open("./OUTPUT_example_domain_coordinates_parser.xlsx-Sheet1.csv", "r")
    output_file = open("combined_coords.csv", "r")
    correct_lines = correct_file.readlines()
    output_lines = output_file.readlines()
    for i in range(len(correct_lines) - 1):
        assert correct_lines[i] == output_lines[i]

test()