SHELL_SCRIPT=$(readlink -f "$0")
RUN_PATH=$(dirname "$SHELL_SCRIPT")

SRC_PATH=/path/to/Mercury_bam_model/src/model_run

python -u ${SRC_PATH}/predict.py \
  --model-path ${RUN_PATH}/train_output_Cristiano \
  --data-path ${RUN_PATH}/data_Cristiano/tokenized_data \
  --batch-size 48 \
  --max-tokens 30 \
  --dataset-name test \
  -o ${RUN_PATH}/prediction_test_Cristiano.csv