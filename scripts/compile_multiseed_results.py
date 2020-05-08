#!/usr/bin/env python
import argparse
import pandas as pd
import os
import re


def get_immediate_subdirectories(a_dir):
    return [name for name in os.listdir(a_dir)
            if os.path.isdir(os.path.join(a_dir, name))]


def get_files_with_prefix(dir, prefix):
    return [name for name in os.listdir(dir)
            if os.path.isfile(os.path.join(dir, name)) and name.startswith(prefix)]


def load_results_data_for_experiment(path):
    results = []
    eval_files = get_files_with_prefix(path, "evaluation")
    for file in eval_files:
        eval_path = os.path.join(path, file)
        eval_name = re.match("evaluation_(.*)\.", file)[1]
        eval_data = pd.read_json(eval_path, typ="series")
        eval_data["test_name"] = eval_name
        results.append(eval_data)
    return results


def print_full(x):
    pd.set_option('display.max_rows', len(x))
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 2000)
    pd.set_option('display.float_format', '{:20,.3f}'.format)
    pd.set_option('display.max_colwidth', -1)
    print(x)
    pd.reset_option('display.max_rows')
    pd.reset_option('display.max_columns')
    pd.reset_option('display.width')
    pd.reset_option('display.float_format')
    pd.reset_option('display.max_colwidth')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("results_folders", nargs="+")
    args = parser.parse_args()

    results_data = []
    for seed_path in args.results_folders:
        seed_num = int(seed_path[-1])
        experiment_names = get_immediate_subdirectories(seed_path)
        for exp in experiment_names:
            exp_path = os.path.join(seed_path, exp)
            model_dirs = get_immediate_subdirectories(exp_path)
            for model in model_dirs:
                model_res_path = os.path.join(exp_path, model)
                results_data.append((seed_num, exp, model, model_res_path))

    results_data_by_test_set = []
    for exp in results_data:
        test_results = load_results_data_for_experiment(exp[3])
        for result in test_results:
            results_data_by_test_set.append(exp + tuple(result))

    frame = pd.DataFrame(results_data_by_test_set,
                         columns=["seed", "exp", "model", "results_path", "seq_acc", "parse_validity", "loss",
                                  "test_name"])
    settings = frame.groupby(["exp", "model", "test_name"])
    summary_stats = settings.agg({"seq_acc": ["mean", "std", "count"]})
    print_full(summary_stats)


if __name__ == "__main__":
    main()
