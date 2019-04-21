if [[ $# < 1 ]]; then
    echo "Usage: bash scripts/simple_train_all_models.sh category (vocabulary)"
    exit 1
fi

category=$1
vocab_dir="vocabulary"
config="{\"train_data_path\":\"data/${category}/train.txt\",\"validation_data_path\":\"data/${category}/val.txt\",\"trainer\":{\"cuda_device\":0}}"

if [[ $# > 1 ]]; then
    vocab_dir=$2
    config="{\"train_data_path\":\"data/${category}/train.txt\",\"validation_data_path\":\"data/${category}/val.txt\",\"vocabulary\":{\"directory_path\":\"${vocab_dir}\"},\"trainer\":{\"cuda_device\":0}}"
fi

echo "Cleaning all training data..."
if [ -d "experiments/results_${category}" ]; then
    rm -rf experiments/results_${category}
fi
echo "Done."

bash scripts/train_all_models ${category} experiments -- -o $config
