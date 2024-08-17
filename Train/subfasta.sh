#!/bin/bash

# Initialize variables
indir=""
outdir=""
n=10000

# Function to show help
show_help() {
  echo "Usage: ${0##*/} -i INPUT_DIR -o OUTPUT_DIR -n NUM_READS [-f] [-h]"
  echo "  -i  Set the input directory containing FASTA files."
  echo "  -o  Set the output directory for subsampled FASTA files."
  echo "  -n  Set the number of reads to subsample."
  echo "  -f  Force overwrite of existing output files."
  echo "  -h  Display this help and exit."
}

force_overwrite=0 # Initialize as false
while getopts 'i:o:n:fh' option; do
  case "$option" in
  i) indir=$OPTARG ;;
  o) outdir=$OPTARG ;;
  n) n=$OPTARG ;;
  f) force_overwrite=1 ;;
  h)
    show_help
    exit 0
    ;;
  *)
    show_help
    exit 1
    ;;
  esac
done

# Shift off the options and optional --
shift "$((OPTIND - 1))"


# Check if all required arguments are provided and valid
if [ -z "$indir" ] || [ -z "$outdir" ] || [ -z "$n" ]; then
  echo "All arguments -i, -o, and -n must be provided."
  show_help
  exit 1
fi

# Ensure that the number of samples is a number
if ! [ "$n" -eq "$n" ] 2>/dev/null; then
  echo "The number of samples (-n) must be an integer."
  exit 1
fi
mkdir -p "$outdir"

for fn in "$indir"/*.fa; do
  fb=$(basename "$fn")
  subfa=$outdir/"$fb"
  if [ -f "$subfa" ] && [ "$force_overwrite" -eq 0 ]; then
    printf "Skipping ..%s.. \n" "$fb"
  else
    printf "Subsampling ..%s.. \n" "$fb"
    seqtk sample -s 60 "$fn" "$n" >"$subfa"
  fi
done
