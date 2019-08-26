import importlib_resources

from gpsr_command_understanding.knowledge import KnowledgeBase


def load_all_2018_by_cat(generator, grammar_dir):
    common_path = importlib_resources.open_text(grammar_dir, "common_rules.txt")

    cat1_rules = generator.load_rules(
        [common_path, importlib_resources.open_text(grammar_dir, "gpsr_category_1_grammar.txt")])
    cat2_rules = generator.load_rules(
        [common_path, importlib_resources.open_text(grammar_dir, "gpsr_category_2_grammar.txt")])
    cat3_rules = generator.load_rules(
        [common_path, importlib_resources.open_text(grammar_dir, "gpsr_category_3_grammar.txt")])

    cat1_semantics = generator.load_semantics_rules(
        importlib_resources.open_text(grammar_dir, "gpsr_category_1_semantics.txt"))
    cat2_semantics = generator.load_semantics_rules(
        [importlib_resources.open_text(grammar_dir, "gpsr_category_1_semantics.txt"),
         importlib_resources.open_text(grammar_dir, "gpsr_category_2_semantics.txt")])
    cat3_semantics = generator.load_semantics_rules(
        importlib_resources.open_text(grammar_dir, "gpsr_category_3_semantics.txt"))

    return [(cat1_rules, cat1_semantics), (cat2_rules, cat2_semantics), (cat3_rules, cat3_semantics)]


def load_all_2018(generator, grammar_dir):
    common_path = importlib_resources.open_text(grammar_dir, "common_rules.txt")

    generator.knowledge_base = KnowledgeBase()
    generator.knowledge_base.load_from_xml(grammar_dir)
    grammar_files = [common_path, importlib_resources.open_text(grammar_dir, "gpsr_category_1_grammar.txt"),
                     importlib_resources.open_text(grammar_dir, "gpsr_category_2_grammar.txt"),
                     importlib_resources.open_text(grammar_dir, "gpsr_category_3_grammar.txt")]
    rules = generator.load_rules(grammar_files)


    semantics = generator.load_semantics_rules(
        [importlib_resources.open_text(grammar_dir, "gpsr_category_1_semantics.txt"),
         importlib_resources.open_text(grammar_dir, "gpsr_category_2_semantics.txt"),
         importlib_resources.open_text(grammar_dir, "gpsr_category_3_semantics.txt")])

    return rules, semantics


def load_all(generator, task, grammar_dir, expand_shorthand=True):
    common_path = importlib_resources.open_text(grammar_dir, "common_rules.txt")
    generator.knowledge_base = KnowledgeBase()
    generator.knowledge_base.load_from_xml_dir(grammar_dir)
    rules = generator.load_rules([common_path, importlib_resources.open_text(grammar_dir, task + ".txt")],
                                 expand_shorthand=expand_shorthand)


    semantics = generator.load_semantics_rules(importlib_resources.open_text(grammar_dir, "gpsr_semantics.txt"))

    return rules, semantics,
