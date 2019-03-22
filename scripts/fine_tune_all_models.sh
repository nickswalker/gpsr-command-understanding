# Models to be trained
models=("bert_base_seq2seq_freezed" "bert_large_seq2seq_freezed" "elmo_seq2seq_freezed" "openai_seq2seq_freezed" "seq2seq")

for model in ${models[*]}
do
  for i in {1..10} "Full"
  do
    allennlp fine-tune -m results/$model/model.tar.gz -c experiments/${model}_$i.json -s fine_tune_results/${model}_$i --include-package gpsr_semantic_parser
  done
done
