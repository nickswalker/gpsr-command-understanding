local common_parameters = import 'common_seq2seq.libjsonnet';
local glove_embedding = import 'glove_embedding.libjsonnet';
std.mergePatch(common_parameters, {
  dataset_reader: {
    source_token_indexers: {
      source_tokens: {
        type: 'single_id',
        namespace: 'source_tokens',
      },
    },
  },
  model: {
    type: 'seq2seq',
    source_embedder: {
      token_embedders: {
        source_tokens: glove_embedding,
      },
    },
  },
  trainer: {
    num_epochs: 150,
  },
})