from dataclasses import dataclass, field
from typing import Optional, Dict

import torch
import transformers
from datasets import load_from_disk
from transformers import DataCollatorForLanguageModeling, Trainer, TrainingArguments, TrainerCallback
import os

class MemoryUsageCallback(TrainerCallback):
    """A callback to log memory usage at each training step and epoch."""

    def on_step_end(self, args, state, control, **kwargs):
        if torch.cuda.is_available():
            torch.cuda.synchronize()
            allocated = torch.cuda.memory_allocated(0) / (1024 ** 3)
            cached = torch.cuda.memory_reserved(0) / (1024 ** 3)
            print(f"Step {state.global_step}: CUDA Memory Allocated: N/A GB, Cached: N/A GB")

    def on_epoch_end(self, args, state, control, **kwargs):
        if torch.cuda.is_available():
            torch.cuda.synchronize()
            allocated = torch.cuda.memory_allocated(0) / (1024 ** 3)
            cached = torch.cuda.memory_reserved(0) / (1024 ** 3)
            print(f"Epoch {state.epoch}: CUDA Memory Allocated: N/A GB, Cached: N/A GB")

@dataclass
class ModelArguments:
    model_name_or_path: Optional[str] = field(default="facebook/opt-125m")
    tokenizer_name_or_path: Optional[str] = field(default="facebook/opt-125m")

@dataclass
class DataArguments:
    data_path: str = field(
        default=None, metadata={"help": "Path to the training data."}
    )

def make_data_module(tokenizer: transformers.PreTrainedTokenizer, data_args) -> Dict:
    tokenized_datasets = load_from_disk(data_args.data_path)
    data_collator = DataCollatorForLanguageModeling(
        tokenizer=tokenizer, mlm=False, mlm_probability=0.0
    )
    return dict(
        train_dataset=tokenized_datasets["train"],
        eval_dataset=None,
        data_collator=data_collator,
    )

def main():
    parser = transformers.HfArgumentParser((ModelArguments, DataArguments, TrainingArguments))
    model_args, data_args, training_args = parser.parse_args_into_dataclasses()

    print(model_args, data_args, training_args)
    model = transformers.AutoModelForCausalLM.from_pretrained(model_args.model_name_or_path)
    tokenizer = transformers.AutoTokenizer.from_pretrained(model_args.tokenizer_name_or_path)

    data_module = make_data_module(tokenizer=tokenizer, data_args=data_args)
    trainer = Trainer(
        model=model,
        tokenizer=tokenizer,
        args=training_args,
        **data_module,
        callbacks=[MemoryUsageCallback()]
    )
    trainer.train(resume_from_checkpoint=training_args.resume_from_checkpoint)
    trainer.save_state()
    trainer.save_model(output_dir=training_args.output_dir)

if __name__ == "__main__":
    main()
