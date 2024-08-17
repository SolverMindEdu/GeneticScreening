#!/bin/bash

# Initialize variables with default values
outdir=""
ref=""
bed_dir=""

# Function to display help
show_help() {
  cat <<EOF
Usage: ${0##*/} [-h] -o OUTPUT_DIR -r REFERENCE_FA -b BED_DIR
Extract sequences based on BED files to generate FASTA files.

    -h          display this help and exit
    -o DIR      specify the output directory
    -r FILE     specify the reference .fa file
    -b DIR      specify the directory containing .bed files
EOF
}

# Parse command line options
while getopts "ho:r:b:" opt; do
  case "$opt" in
  h)
    show_help
    exit 0
    ;;
  o)
    outdir=$OPTARG
    ;;
  r)
    ref=$OPTARG
    ;;
  b)
    bed_dir=$OPTARG
    ;;
  '?')
    show_help >&2
    exit 1
    ;;
  esac
done

# Check if all options were provided
if [ -z "$outdir" ] || [ -z "$ref" ] || [ -z "$bed_dir" ]; then
  echo "All options must be provided."
  show_help >&2
  exit 1
fi

# Create output directory if it doesn't exist
mkdir -p "$outdir"

export ref outdir

cleanup() {
  echo "Received signal, terminating..."
  kill -- -$$ # Send SIGTERM to the entire process group
}
trap cleanup SIGINT SIGTERM

process_bed() {
  bed=$1
  fb=$(basename "$bed")

  id="${fb%%.*}"
  fullfa=$outdir/"${id}.fa"
  if [ ! -f "$fullfa" ]; then
    echo "Extracting sequences from $fb"
    gunzip -c "$bed" | bedtools getfasta -fi "$ref" -bed - -fo "$fullfa"
  else
    echo "$fb already exists, skipping."
  fi
}

export -f process_bed

find "$bed_dir" -name '*.tsv.bgz' -print0 | xargs -0 -P 8 -I {} bash -c 'process_bed "$@"' _ {}
