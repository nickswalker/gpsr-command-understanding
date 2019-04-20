echo "Cleaning all training data..."
if [ -d "results" ]; then
    rm -rf results
    mkdir results
fi
echo "Done."

config="{\"train_data_path\":\"data/cat1/train.txt\",\"validation_data_path\":\"data/cat1/val.txt\",\"vocabulary\":{\"directory_path\":\"vocabulary\"}}"

bash scripts/train_all_models results experiments -- -o $config
