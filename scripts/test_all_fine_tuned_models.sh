# Models to be trained
models=("all_data_all_cats" "bert_base_seq2seq_freezed" "bert_large_seq2seq_freezed" "elmo_seq2seq_freezed" "openai_seq2seq_freezed" "seq2seq")

for model in ${models[*]}
do
  for i in {1..10} "Full"
  do
    allennlp evaluate "fine_tune_results/${model}_$i/model.tar.gz" data/test.txt --output-file "fine_tune_evaluation/${model}_$i.json" --include-package gpsr_semantic_parser
  done
done
