local common_parameters = import 'common_seq2seq.libjsonnet';
local glove_embedding = import 'glove_embedding.libjsonnet';
std.mergePatch(common_parameters, {
  dataset_reader: {
    source_token_indexers: {
      source_tokens: {
        type: 'single_id',
        namespace: 'source_tokens',
      },
      elmo: {
        type: 'elmo_characters',
      },
    },
  },
  model: {
    source_embedder: {
      token_embedders: {
        source_tokens: glove_embedding,
        elmo: {
          type: 'elmo_token_embedder',
          options_file: 'https://s3-us-west-2.amazonaws.com/allennlp/models/elmo/2x4096_512_2048cnn_2xhighway/elmo_2x4096_512_2048cnn_2xhighway_options.json',
          weight_file: 'https://s3-us-west-2.amazonaws.com/allennlp/models/elmo/2x4096_512_2048cnn_2xhighway/elmo_2x4096_512_2048cnn_2xhighway_weights.hdf5',
          do_layer_norm: false,
          dropout: 0.0,
        },
      },
    },
    encoder: {
      type: 'lstm',
      input_size: 100 + 1024,
    },
  },
  trainer: {
    num_epochs: 150,
    patience: 30,
  },
})