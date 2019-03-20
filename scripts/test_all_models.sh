# Models to be evaluated
bert_base_seq2seq_freezed="bert_base_seq2seq_freezed"
bert_base_seq2seq_unfreezed="bert_base_seq2seq_unfreezed"
bert_large_seq2seq_freezed="bert_large_seq2seq_freezed"
bert_large_seq2seq_unfreezed="bert_large_seq2seq_unfreezed"
elmo_seq2seq_freezed="elmo_seq2seq_freezed"
elmo_seq2seq_unfreezed="elmo_seq2seq_unfreezed"
openai_seq2seq_freezed="openai_seq2seq_freezed"
openai_seq2seq_unfreezed="openai_seq2seq_unfreezed"
seq2seq="seq2seq"

# Test all models
allennlp evaluate "results/$bert_base_seq2seq_freezed/model.tar.gz" data/test.txt --output-file "evaluation/$bert_base_seq2seq_freezed.json" --include-package gpsr_semantic_parser
allennlp evaluate "results/$bert_base_seq2seq_unfreezed/model.tar.gz" data/test.txt --output-file "evaluation/$bert_base_seq2seq_unfreezed.json" --include-package gpsr_semantic_parser
allennlp evaluate "results/$bert_large_seq2seq_freezed/model.tar.gz" data/test.txt --output-file "evaluation/$bert_large_seq2seq_freezed.json" --include-package gpsr_semantic_parser
allennlp evaluate "results/$bert_large_seq2seq_unfreezed/model.tar.gz" data/test.txt --output-file "evaluation/$bert_large_seq2seq_unfreezed.json" --include-package gpsr_semantic_parser
allennlp evaluate "results/$elmo_seq2seq_freezed/model.tar.gz" data/test.txt --output-file "evaluation/$elmo_seq2seq_freezed.json" --include-package gpsr_semantic_parser
allennlp evaluate "results/$elmo_seq2seq_unfreezed/model.tar.gz" data/test.txt --output-file "evaluation/$elmo_seq2seq_unfreezed.json" --include-package gpsr_semantic_parser
allennlp evaluate "results/$openai_seq2seq_freezed/model.tar.gz" data/test.txt --output-file "evaluation/$openai_seq2seq_freezed.json" --include-package gpsr_semantic_parser
allennlp evaluate "results/$openai_seq2seq_unfreezed/model.tar.gz" data/test.txt --output-file "evaluation/$openai_seq2seq_unfreezed.json" --include-package gpsr_semantic_parser
allennlp evaluate "results/$seq2seq/model.tar.gz" data/test.txt --output-file "evaluation/$seq2seq.json" --include-package gpsr_semantic_parser
