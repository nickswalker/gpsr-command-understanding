local common_parameters = import 'common_seq2seq.libjsonnet';
local transformer_model = std.extVar('TRANSFORMER_NAME');
local glove_embedding = import 'glove_embedding.libjsonnet';
local transformer_sizes = {
  'albert-base-v2': 768,
  'bert-base-uncased': 768,
  'bert-large-uncased': 1024,
  'distilroberta-base': 768,
  gpt2: 768,
  'roberta-base': 768,
  'xlnet-base-cased': 768,
};
std.mergePatch(common_parameters,
{
 dataset_reader: {
   source_token_indexers: {
     source_tokens: {
       type: 'single_id',
       namespace: 'source_tokens',
     },
     bert: {
       type: 'pretrained_transformer',
       model_name: transformer_model,
     },
   },
   source_tokenizer: {
     type: 'pretrained_transformer',
     model_name: transformer_model,
   },
 },
 model: {
   type: 'seq2seq',
   source_embedder: {
     token_embedders: {
       source_tokens: glove_embedding,
       bert: {
         type: 'pretrained_transformer',
         model_name: transformer_model,
       },
     },
   },
   encoder: {
     type: 'lstm',
     input_size: 100 + transformer_sizes[transformer_model],
     hidden_size: 200,
   },
 },
 trainer: {
   no_grad: ['.*transformer_model*'],
 },
})