#!/usr/bin/perl
use strict;
use warnings;

# Function to extract portions based on coordinates
sub extract_portions {
my ($fasta_file, $coordinates_file, $output_file) = @_;

# Read the FASTA file into a hash
my %sequences;
my $current_id = '';
my $current_seq = '';

open my $fasta_fh, '<', $fasta_file or die "Could not open '$fasta_file': $!";
while (my $line = <$fasta_fh>) {
chomp $line;
if ($line =~ /^>(.+)/) {
if ($current_id) {
$sequences{$current_id} = $current_seq;
}
$current_id = $1; # New sequence ID
$current_seq = ''; # Reset the sequence
} else {
$current_seq .= $line; # Append to the current sequence
}
}
$sequences{$current_id} = $current_seq if $current_id; # Save the last sequence
close $fasta_fh;

# Read coordinates and extract portions
open my $coord_fh, '<', $coordinates_file or die "Could not open '$coordinates_file': $!";
open my $output_fh, '>', $output_file or die "Could not open '$output_file': $!";

while (my $line = <$coord_fh>) {
chomp $line;
my ($seq_id, $start, $end) = split ',', $line;

if (exists $sequences{$seq_id}) {
# Adjust for 1-based indexing
if ($start < 1 || $end < $start || $end > length($sequences{$seq_id})) {
warn "Warning: Invalid coordinates for '$seq_id': start=$start, end=$end\n";
next;
}

my $portion_seq = substr($sequences{$seq_id}, $start - 1, $end - $start + 1);
my $portion_key = "$seq_id\_$start\_$end"; # Create a unique identifier
print $output_fh ">$portion_key\n$portion_seq\n";
} else {
warn "Warning: Sequence ID '$seq_id' not found in FASTA file.\n";
}
}

close $coord_fh;
close $output_fh;
}

# Main script
if (@ARGV != 3) {
die "Usage: $0 <fasta_file> <coordinates_file> <output_file>\n";
}

my ($fasta_file, $coordinates_file, $output_file) = @ARGV;

extract_portions($fasta_file, $coordinates_file, $output_file);