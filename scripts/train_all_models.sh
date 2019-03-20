# Remove all models in results directory
rm -rf results/*

# Models to be trained
bert_base_seq2seq_freezed="bert_base_seq2seq_freezed"
bert_base_seq2seq_unfreezed="bert_base_seq2seq_unfreezed"
bert_large_seq2seq_freezed="bert_large_seq2seq_freezed"
bert_large_seq2seq_unfreezed="bert_large_seq2seq_unfreezed"
elmo_seq2seq_freezed="elmo_seq2seq_freezed"
elmo_seq2seq_unfreezed="elmo_seq2seq_unfreezed"
openai_seq2seq_freezed="openai_seq2seq_freezed"
openai_seq2seq_unfreezed="openai_seq2seq_unfreezed"
seq2seq="seq2seq"

# Training all models
allennlp train "experiments/$bert_base_seq2seq_freezed.json" -s "results/$bert_base_seq2seq_freezed" --include-package gpsr_semantic_parser
allennlp train "experiments/$bert_base_seq2seq_unfreezed.json" -s "results/$bert_base_seq2seq_unfreezed" --include-package gpsr_semantic_parser
allennlp train "experiments/$bert_large_seq2seq_freezed.json" -s "results/$bert_large_seq2seq_freezed" --include-package gpsr_semantic_parser
allennlp train "experiments/$bert_large_seq2seq_unfreezed.json" -s "results/$bert_large_seq2seq_unfreezed" --include-package gpsr_semantic_parser
allennlp train "experiments/$elmo_seq2seq_freezed.json" -s "results/$elmo_seq2seq_freezed" --include-package gpsr_semantic_parser
allennlp train "experiments/$elmo_seq2seq_unfreezed.json" -s "results/$elmo_seq2seq_unfreezed" --include-package gpsr_semantic_parser
allennlp train "experiments/$openai_seq2seq_freezed.json" -s "results/$openai_seq2seq_freezed" --include-package gpsr_semantic_parser
allennlp train "experiments/$openai_seq2seq_unfreezed.json" -s "results/$openai_seq2seq_unfreezed" --include-package gpsr_semantic_parser
allennlp train "experiments/$seq2seq.json" -s "results/$seq2seq" --include-package gpsr_semantic_parser
