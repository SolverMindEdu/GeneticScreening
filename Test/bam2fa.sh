#!/bin/bash

# $1: bam dir
# $2: output dir

bam_dir=$1
fasta_dir=$2
mkdir -p $fasta_dir

for bam in $bam_dir/*.sort.dedup.bam; do

  fb=$(basename "$bam")
  fullfa=$fasta_dir/$(echo "$fb" | sed 's/\.sort\.dedup\.bam$/.fa/')

  if [ ! -f "$fullfa" ]; then
    echo "Subsampling $fb "
    samtools fasta -@ 60 "$bam" >$fullfa
  else
    echo "Skipping $fb "
  fi
done
