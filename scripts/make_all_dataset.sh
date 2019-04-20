echo "Cleaning old data..."
if [ -d "data/1_1" ]; then
    rm -rf data/1_1
fi

if [ -d "data/2_2" ]; then
    rm -rf data/2_2
fi

if [ -d "data/3_3" ]; then
    rm -rf data/3_3
fi

if [ -d "data/123_123" ]; then
    rm -rf data/123_123
fi
echo "Done."

echo "Generate data..."
python -m gpsr_semantic_parser/data/make_dataset -s 0.8 0.2 0.0 -trc 1 -tc 1
python -m gpsr_semantic_parser/data/make_dataset -s 0.4 0.1 0.5 -trc 2 -tc 2 -i
python -m gpsr_semantic_parser/data/make_dataset -s 0.4 0.1 0.5 -trc 3 -tc 3 -i
python -m gpsr_semantic_parser/data/make_dataset -s 0.8 0.2 0.0
echo "Done."

