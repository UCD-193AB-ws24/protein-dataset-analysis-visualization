import sys

def test():
    correct_file = open("./Dandie_file_to_test_on.fasta", "r")
    output_file = open("simplified.fasta", "r")
    correct_lines = correct_file.readlines()
    output_lines = output_file.readlines()
    for i in range(len(output_lines) - 1):
        assert correct_lines[i] == output_lines[i]

test()

