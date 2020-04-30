local common_parameters = import 'common_seq2seq.libjsonnet';
local transformer_model = std.extVar('TRANSFORMER_NAME');
local glove_embedding = import 'glove_embedding.libjsonnet';
local transformer_sizes = {
  gpt2: 768,
  distilgpt2: 768
};
local get_transformer_size(name) =
    if std.length(std.findSubstr("base", name)) == 1 then
        768
    else if std.length(std.findSubstr("large", name)) == 1 then
        1024
    else if std.objectHas(transformer_sizes, name) then
        transformer_sizes[name]
    else
        error "Unknown size";

std.mergePatch(common_parameters,
{
 dataset_reader: {
   source_add_start_token: false,
   source_add_end_token: false,
   source_token_indexers: {
     source_tokens: {
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
       source_tokens: {
         type: 'pretrained_transformer',
         model_name: transformer_model,
       },
     },
   },
   encoder: {
     type: 'lstm',
     input_size: get_transformer_size(transformer_model),
     hidden_size: 200,
   },
 },
 trainer: {
   no_grad: ['.*transformer_model*'],
 },
})