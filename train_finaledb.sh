#!/bin/bash

SHELL_SCRIPT=$(readlink -f "$0")
RUN_PATH=$(dirname "$SHELL_SCRIPT")
SRC_PATH="/mnt/c/Users/RyanDesktop/Downloads/finaledb_bam_model/mercury_opt_model/model_run"

echo "RUN_PATH: ${RUN_PATH}"
echo "SRC_PATH: ${SRC_PATH}"

torchrun --nproc_per_node=1 ${SRC_PATH}/train.py \
  --model_name_or_path "facebook/opt-125m" \
  --tokenizer_name_or_path ${SRC_PATH}/opt-seq-pubmed-tokenizer \
  --data_path ${RUN_PATH}/data_Cristiano/tokenized_data \
  --output_dir ${RUN_PATH}/train_output_Cristiano \
  --num_train_epochs 83.32 \
  --per_device_train_batch_size 10 \
  --per_device_eval_batch_size 10 \
  --gradient_accumulation_steps 10 \
  --evaluation_strategy "no" \
  --save_strategy "steps" \
  --save_steps 1000 \
  --save_total_limit 1 \
  --learning_rate 1e-4 \
  --weight_decay 0.01 \
  --warmup_ratio 0.03 \
  --lr_scheduler_type "cosine" \
  --logging_steps 32 \
  --full_determinism \
  --fp16 False \
  --dataloader_num_workers 8 \
  --fsdp "full_shard auto_wrap" \
  --fsdp_config ${SRC_PATH}/fsdp_config_opt.json
