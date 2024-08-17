import argparse
import csv
import random
from multiprocessing import Pool
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd
import yaml


def parse_args():
    parser = argparse.ArgumentParser(description="Process FASTA files in parallel.")
    parser.add_argument(
        "--info",
        type=str,
        help="Path to sample info file, should contains SampleID and Response",
        required=True,
    )
    parser.add_argument(
        "--fasta-dir", type=str, help="Path to directory containing FASTA files"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=40,
        help="Number of sequences to process in a batch",
    )
    parser.add_argument(
        "--truncation",
        type=int,
        default=0,
        help="Number of sequences to process in a batch",
    )
    parser.add_argument(
        "-j",
        "--n_cores",
        type=int,
        default=60,
        help="Number of cores for parallel processing",
    )
    parser.add_argument(
        "--with-response",
        nargs=2,
        type=str,
        action="append",
        help="ids file and output csv name for samples with response",
    )
    parser.add_argument(
        "--no-response",
        nargs=2,
        type=str,
        action="append",
        help="ids file and output csv name for samples without response",
    )
    parser.add_argument(
        "-o",
        "--outdir",
        type=str,
        required=True,
        help="Output file dir",
    )

    return parser.parse_args()


def read_info_file(filepath):
    """Reads an info file based on its extension and returns a pandas DataFrame."""
    file_extension = Path(filepath).suffix.lower()

    if file_extension in [".csv", ".tsv"]:
        sep = "," if file_extension == ".csv" else "\t"
        return pd.read_csv(filepath, sep=sep)
    elif file_extension in [".xlsx", ".xls"]:
        return pd.read_excel(filepath)
    else:
        raise ValueError(f"Unsupported file extension: {file_extension}")


# Define the function to be executed in parallel
def process_fasta_file(
    info: pd.DataFrame, fa: Path, truncation: int, batch_size: int, with_response=True
):
    sampleID = fa.stem.split(".")[0]
    try:
        response = info.loc[info["SampleID"] == sampleID, "Response"].values[0]
    except IndexError:
        print(f"No response for {sampleID}...")
        return None

    with open(fa, "r") as f:
        sequences = [s.strip() for s in f.readlines() if not s.startswith(">")]
        if len(sequences) == 0:
            print(f"No sequences found for {sampleID}...")
            return

        if truncation > 0:
            sequences = [sequence[:truncation] for sequence in sequences]

    # shuffle the sequences
    random.shuffle(sequences)

    batch_size = min(batch_size, len(sequences))
    for batch_start in range(0, len(sequences), batch_size):
        if batch_start+batch_size > len(sequences):
            break
        
        batch = sorted(sequences[batch_start : batch_start + batch_size])
        if with_response is True:
            text = f"### Instruction:\nAnnotate the following sequence.\n### Input:\n{' '.join(sorted(batch))}\n### Response:\n{response}."
            yield text, response, sampleID
        else:
            text = f"### Instruction:\nAnnotate the following sequence.\n### Input:\n{' '.join(sorted(batch))}.\n### Response:"
            yield text, response, sampleID
    print(f"Completed processing of {sampleID}.")


def process_fasta_worker(
    info, fa_path, truncation, batch_size, temp_dir_path, with_response
):
    results = list(
        process_fasta_file(
            info=info,
            fa=fa_path,
            truncation=truncation,
            batch_size=batch_size,
            with_response=with_response,
        )
    )

    if results:
        temp_file_path = temp_dir_path / f"{fa_path.stem}_results.csv"
        with temp_file_path.open("w", newline="", encoding="utf-8") as temp_file:
            writer = csv.writer(
                temp_file, delimiter=",", quotechar='"', quoting=csv.QUOTE_MINIMAL
            )
            writer.writerow(["text", "output", "patient"])
            writer.writerows(results)
        return temp_file_path
    return None


def main():
    args = parse_args()

    info_path = Path(args.info)
    fasta_dir = Path(args.fasta_dir)
    n_cores = args.n_cores
    batch_size = args.batch_size
    outdir = Path(args.outdir)

    outdir.mkdir(
        exist_ok=True,
        parents=True,
    )
    info = read_info_file(info_path)

    input_with_response = [ls + [True] for ls in args.with_response]
    input_no_response = [ls + [False] for ls in args.no_response]
    inputs = input_with_response + input_no_response

    data_config = {}

    with TemporaryDirectory(dir=outdir) as temp_dir_path:
        temp_dir_path = Path(temp_dir_path)
        for ids_file, outname, with_response in inputs:
            outfile = outdir / f"{outname}_data.csv"

            specific_ids = set(open(ids_file, "r").read().splitlines())

            with Pool(n_cores) as pool:
                temp_files = pool.starmap(
                    process_fasta_worker,
                    [
                        (
                            info,
                            fa,
                            args.truncation,
                            batch_size,
                            temp_dir_path,
                            with_response,
                        )
                        for fa in fasta_dir.iterdir()
                        if fa.is_file()
                        and (not specific_ids or fa.stem.split(".")[0] in specific_ids)
                    ],
                )

            # Stream temporary files directly into the final output, reducing memory usage.
            with open(outfile, "w", newline="", encoding="utf-8") as f_out:
                writer = None
                for temp_file in filter(None, temp_files):
                    with open(temp_file, "r", newline="", encoding="utf-8") as f_in:
                        reader = csv.reader(f_in)
                        if writer is None:
                            writer = csv.writer(f_out)
                            writer.writerow(next(reader))
                        else:
                            next(reader)
                        writer.writerows(reader)
                        temp_file.unlink()

            print(f"All processes completed. Output written to {outfile}.")

            data_config[outname] = [f"${{CONFIGPATH}}/{outfile.name}"]

    # create a yaml config for data
    with open(outdir / "data_config.yaml", "w") as f:
        yaml.dump(data_config, f)

    with open(outdir / "args.yaml", "w") as f:
        yaml.dump(args.__dict__, f)


if __name__ == "__main__":
    main()
