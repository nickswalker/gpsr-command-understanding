# Models to be trained
models=("bert_base_seq2seq" "bert_large_seq2seq" "elmo_seq2seq" "openai_seq2seq" "seq2seq")

for model in ${models[*]}
do
  for i in {1..17} "Full"
  do
    allennlp fine-tune -m results/$model/model.tar.gz -c experiments/${model}_$i.json -s fine_tune_results/${model}_$i --include-package gpsr_semantic_parser
    echo "$model is done" >> progress.txt
  done
done
