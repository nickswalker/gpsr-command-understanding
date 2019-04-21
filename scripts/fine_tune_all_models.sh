if [[ $# < 2 ]]; then
  echo "Usage: bash scripts/fine_tune_all_models.sh category model_dir"
  exit 1
fi

category=$1
model_dir=$2

if [ -d "fine_tune_results_${category}" ]; then
  rm -rf fine_tune_results_${category}
fi
mkdir fine_tune_results_${category}

# Models to be trained
models=("bert_base_seq2seq" "bert_large_seq2seq" "elmo_seq2seq" "openai_seq2seq" "glove_seq2seq" "seq2seq")

for model in ${models[*]}
do
  config="{\"train_data_path\":\"data/${category}/train.txt\",\"validation_data_path\":\"data/${category}/val.txt\",\"trainer\":{\"cuda_device\":0}}"
  allennlp fine-tune -m ${model_dir}/$model/model.tar.gz -c experiments/${model}.json -s fine_tune_results_${category}/${model} -o $config --include-package gpsr_semantic_parser
  echo "${model} is done" >> fine_tune_progress_${category}.txt
done
