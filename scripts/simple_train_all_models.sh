echo "Cleaning all training data..."
if [ -d "experiments/results_cat1" ]; then
    rm -rf experiments/results_cat1
fi
echo "Done."

config="{\"train_data_path\":\"data/cat1/train.txt\",\"validation_data_path\":\"data/cat1/val.txt\",\"vocabulary\":{\"directory_path\":\"vocabulary\"}}"

bash scripts/train_all_models cat1 experiments -- -o $config
