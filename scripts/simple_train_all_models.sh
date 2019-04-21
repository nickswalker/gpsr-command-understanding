if [[ $# < 1 ]]; then
    echo "Please indicate which category to train on"
    exit 1
fi

category=$1
vocab_dir="vocabulary"
if [[ $# > 1]]; then
    vocab_dir=$2
fi

echo "Cleaning all training data..."
if [ -d "experiments/results_${category}" ]; then
    rm -rf experiments/results_${category}
fi
echo "Done."

config="{\"train_data_path\":\"data/${category}/train.txt\",\"validation_data_path\":\"data/${category}/val.txt\",\"vocabulary\":{\"directory_path\":\"${vocab_dir}\"},\"trainer\":{\"cuda_device\":0}}"

bash scripts/train_all_models ${category} experiments -- -o $config
