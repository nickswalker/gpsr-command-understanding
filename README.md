# gpsr_semantic_parser

A semantic parser for the [RoboCup@Home](http://www.robocupathome.org/) _General Purpose Service Robot_ task.

* [X] Utterance to λ-calculus representation parser
* [ ] Utterance intention recognition model
* [X] Lexer/parser for loading the released command generation CFG
* [X] Tools for generating commands along with a λ-calculus representation

## Usage

### Generation

The latest grammar and knowledgebase files (pulled from [the generator](https://github.com/kyordhel/GPSRCmdGen)) are provided in the resources directory. The grammar [format specification](https://github.com/kyordhel/GPSRCmdGen/wiki/Grammar-Format-Specification) will clarify how to interpret the files.

See the scripts directory for examples.

### Training

We base our training on [previous work](https://github.com/jbkjr/allennlp_sempar) using [AllenNLP](https://allennlp.org) for seq2seq semantic parser training. All of our experiments are
declaratively specified  in the `experiments` directory.

You can run them with

    allennlp train \
    experiments/seq2seq.json \
    -s results/seq2seq \
    --include-package gpsr_semantic_parser

You can monitor training with Tensorboard:

    #TODO

### Testing

You can poke at a trained model through the browser using AllenNLP as well

    python -m allennlp.service.server_simple \
        --archive-path results/seq2seq/model.tar.gz \
        --predictor  my_seq2seq\
        --include-package gpsr_semantic_parser \
        --title "GPSR Semantic Parser" \
        --field-name command