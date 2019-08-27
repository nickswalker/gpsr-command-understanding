import importlib_resources

from gpsr_command_understanding.generator import Generator
from gpsr_command_understanding.knowledge import KnowledgeBase


def load_all_2018_by_cat(grammar_dir):
    common_path = importlib_resources.open_text(grammar_dir, "common_rules.txt")

    cat1_gen = Generator(grammar_format_version=2018)
    cat2_gen = Generator(grammar_format_version=2018)
    cat3_gen = Generator(grammar_format_version=2018)
    cat1_gen.load_rules(
        [common_path, importlib_resources.open_text(grammar_dir, "gpsr_category_1_grammar.txt")])
    cat2_gen.load_rules(
        [common_path, importlib_resources.open_text(grammar_dir, "gpsr_category_2_grammar.txt")])
    cat3_gen.load_rules(
        [common_path, importlib_resources.open_text(grammar_dir, "gpsr_category_3_grammar.txt")])

    cat1_gen.load_semantics_rules(
        importlib_resources.open_text(grammar_dir, "gpsr_category_1_semantics.txt"))
    cat2_gen.load_semantics_rules(
        [importlib_resources.open_text(grammar_dir, "gpsr_category_1_semantics.txt"),
         importlib_resources.open_text(grammar_dir, "gpsr_category_2_semantics.txt")])
    cat3_gen.load_semantics_rules(
        importlib_resources.open_text(grammar_dir, "gpsr_category_3_semantics.txt"))

    return [cat1_gen, cat2_gen, cat3_gen]


def load_all_2018(grammar_dir):
    common_path = importlib_resources.open_text(grammar_dir, "common_rules.txt")

    generator = Generator(grammar_format_version=2018)
    generator.knowledge_base = KnowledgeBase()
    generator.knowledge_base.load_from_xml(grammar_dir)
    grammar_files = [common_path, importlib_resources.open_text(grammar_dir, "gpsr_category_1_grammar.txt"),
                     importlib_resources.open_text(grammar_dir, "gpsr_category_2_grammar.txt"),
                     importlib_resources.open_text(grammar_dir, "gpsr_category_3_grammar.txt")]
    generator.load_rules(grammar_files)

    generator.load_semantics_rules(
        [importlib_resources.open_text(grammar_dir, "gpsr_category_1_semantics.txt"),
         importlib_resources.open_text(grammar_dir, "gpsr_category_2_semantics.txt"),
         importlib_resources.open_text(grammar_dir, "gpsr_category_3_semantics.txt")])

    return generator


def load_all(generator, task, grammar_dir, expand_shorthand=True):
    common_path = importlib_resources.open_text(grammar_dir, "common_rules.txt")
    generator.knowledge_base = KnowledgeBase()
    generator.knowledge_base.load_from_xml_dir(grammar_dir)
    generator.load_rules([common_path, importlib_resources.open_text(grammar_dir, task + ".txt")],
                         expand_shorthand=expand_shorthand)

    generator.load_semantics_rules(importlib_resources.open_text(grammar_dir, "gpsr_semantics.txt"))
