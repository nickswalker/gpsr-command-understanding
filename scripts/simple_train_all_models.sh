config="{\"train_data_path\":\"data/cat1/train.txt\",\"validation_data_path\":\"data/cat1/val.txt\",\"vocabulary\":{\"directory_path\":\"vocabulary\"}}"

bash scripts/train_all_models results experiments -- -o $config
