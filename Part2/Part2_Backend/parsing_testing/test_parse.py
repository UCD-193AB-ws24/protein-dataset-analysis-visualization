import sys

def test():
    correct_file = open("./expected_output.json", "r")
    output_file = open("actual_output", "r")
    correct_lines = correct_file.readlines()
    output_lines = output_file.readlines()
    for i in range(len(correct_lines) - 1):
        assert correct_lines[i] == output_lines[i]

test()