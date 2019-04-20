echo "Cleaning old data..."
if [ -d "data/cat1" ]; then
    rm -rf data/cat1
fi

if [ -d "data/cat2" ]; then
    rm -rf data/cat2
fi

if [ -d "data/cat3" ]; then
    rm -rf data/cat3
fi

if [ -d "data/all" ]; then
    rm -rf data/all
fi
echo "Done."

echo "Generate data..."
python -m gpsr_semantic_parser.data.make_dataset --name cat1 -s 0.8 0.2 0.0 -trc 1 -tc 1
python -m gpsr_semantic_parser.data.make_dataset --name cat2 -s 0.4 0.1 0.5 -trc 2 -tc 2 -i
python -m gpsr_semantic_parser.data.make_dataset --name cat3 -s 0.4 0.1 0.5 -trc 3 -tc 3 -i
python -m gpsr_semantic_parser.data.make_dataset --name all -s 0.9 0.1 0.0
echo "Done."

