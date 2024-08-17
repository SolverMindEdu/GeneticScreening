import argparse
from pathlib import Path

import yaml
from datasets import load_dataset
from transformers import AutoTokenizer


def parse_yaml(path: Path):
    with open(path, "r") as f:
        data_files = yaml.safe_load(f)

    for k in data_files.keys():
        data_files[k][0] = data_files[k][0].replace("${CONFIGPATH}", str(path.parent))
    return data_files


def arg_parser():
    parser = argparse.ArgumentParser(description="tokenize data")

    parser.add_argument(
        "--pretrained-model",
        type=str,
        help="name or Path to the pretrained model.",
        default=str(Path(__file__).parent / "opt-seq-pubmed-tokenizer"),
    )
    parser.add_argument(
        "--data",
        type=str,
        help="Path to the data YAML configuration file or data file.",
        required=True,
    )
    parser.add_argument(
        "--max-length",
        type=int,
        default=None,
        help="Maximum sequence length for tokenization.",
    )
    parser.add_argument(
        "-j",
        "--n-cores",
        type=int,
        default=32,
        help="Number of workers for preprocessing.",
    )
    parser.add_argument(
        "--overwrite-cache", action="store_true", help="Overwrite the cache or not."
    )
    parser.add_argument(
        "-o",
        "--output-path",
        type=str,
        help="Path to save tokenized data.",
        default=None,
    )
    return parser.parse_args()


args = arg_parser()

data_path = Path(args.data)

if args.output_path is None and data_path.parent.is_dir():
    outpath = data_path.parent
else:
    outpath = Path(args.output_path)


if outpath.is_dir():
    outfile = outpath / "tokenized_data"
elif outpath.parent.is_dir():
    outfile = outpath
    outpath = outfile.parent
else:
    raise ValueError("Output path does not exist.")
if not data_path.exists():
    raise ValueError("Data path does not exist.")

if data_path.suffix == ".yml" or data_path.suffix == ".yaml":
    data_files = parse_yaml(data_path)
else:
    data_files = {
        "data": [args.data],
    }

# load tokenizer
tokenizer = AutoTokenizer.from_pretrained(args.pretrained_model)
max_length = args.max_length


def tokenize_function(examples):
    return tokenizer(examples["text"], truncation=True, max_length=max_length)


cache_dir = outpath / "tmp"  # Cache directory

extension = "csv"
raw_datasets = load_dataset(extension, data_files=data_files, cache_dir=cache_dir)

preprocessing_num_workers = args.n_cores
overwrite_cache = args.overwrite_cache
removed_columns = ["text"]

tokenized_datasets = raw_datasets.map(
    tokenize_function,
    num_proc=preprocessing_num_workers,
    remove_columns=removed_columns,
    load_from_cache_file=not overwrite_cache,
    desc="Running tokenizer on dataset",
)

tokenized_datasets.save_to_disk(outfile)
