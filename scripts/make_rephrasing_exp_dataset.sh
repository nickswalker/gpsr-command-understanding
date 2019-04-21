python -m gpsr_semantic_parser.data.make_dataset --name rephrasing_only -s 0.4 0.1 0.5 -t data/all_rephrasings_txt.txt -na
python -m gpsr_semantic_parser.data.make_dataset --name rephrasing_all -s 0.32 0.08 0.6 -t data/all_rephrasings_txt.txt
python -m gpsr_semantic_parser.data.make_dataset --name rephrasing_vocab -s 0.8 0.2 0.0 -t data/all_rephrasings_txt.txt
