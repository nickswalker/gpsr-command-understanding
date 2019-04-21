if [[ $# < 2 ]]; then
    echo "Please indicate the training and validation path"
    exit 1
fi

echo "Cleaning vocabulary_rephrasing..."
if [ -d "vocabulary_rephrasing" ]; then
    rm -rf vocabulary_rephrasing
fi
echo "Done."

training_path=$1
validation_path=$2
override_config="{\"train_data_path\":\"${training_path}\",\"validation_data_path\":\"${validation_path}\"}"


mkdir tmp
echo $override_config
allennlp dry-run experiments/seq2seq.json -s tmp -o ${override_config} --include-package gpsr_semantic_parser
mv tmp/vocabulary ./vocabulary_rephrasing
rm -rf tmp
