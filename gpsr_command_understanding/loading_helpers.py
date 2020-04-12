import importlib_resources

from gpsr_command_understanding.generator import Generator
from gpsr_command_understanding.knowledge import KnowledgeBase

GRAMMAR_DIR_2018 = "gpsr_command_understanding.resources.generator2018"
GRAMMAR_DIR_2019 = "gpsr_command_understanding.resources.generator2019"

def load_all_2018_by_cat(grammar_dir):
    with importlib_resources.open_text(grammar_dir, "common_rules.txt") as common_file:
        common = common_file.readlines()

    cat1_gen = Generator(grammar_format_version=2018)
    cat2_gen = Generator(grammar_format_version=2018)
    cat3_gen = Generator(grammar_format_version=2018)
    with importlib_resources.open_text(grammar_dir, "gpsr_category_1_grammar.txt") as cat1:
        cat1_gen.load_rules([common, cat1])
    with importlib_resources.open_text(grammar_dir, "gpsr_category_2_grammar.txt") as cat2:
        cat2_gen.load_rules([common, cat2])
    with importlib_resources.open_text(grammar_dir, "gpsr_category_3_grammar.txt") as cat3:
        cat3_gen.load_rules([common, cat3])

    with importlib_resources.open_text(grammar_dir, "gpsr_category_1_semantics.txt") as cat1:
        cat1_gen.load_semantics_rules(cat1)
    with importlib_resources.open_text(grammar_dir, "gpsr_category_1_semantics.txt") as cat1, importlib_resources.open_text(grammar_dir, "gpsr_category_2_semantics.txt") as cat2:
        cat2_gen.load_semantics_rules([cat1, cat2])
    with importlib_resources.open_text(grammar_dir, "gpsr_category_1_semantics.txt") as cat1, importlib_resources.open_text(grammar_dir, "gpsr_category_2_semantics.txt") as cat2, importlib_resources.open_text(grammar_dir, "gpsr_category_3_semantics.txt") as cat3:
        cat3_gen.load_semantics_rules([cat1, cat2, cat3])

    return [cat1_gen, cat2_gen, cat3_gen]


def load_all_2018(grammar_dir):
    generator = Generator(grammar_format_version=2018)
    generator.knowledge_base = KnowledgeBase()
    generator.knowledge_base.load_from_xml_dir(grammar_dir)
    common_path = importlib_resources.open_text(grammar_dir, "common_rules.txt")
    grammar_files = [common_path, importlib_resources.open_text(grammar_dir, "gpsr_category_1_grammar.txt"),
                     importlib_resources.open_text(grammar_dir, "gpsr_category_2_grammar.txt"),
                     importlib_resources.open_text(grammar_dir, "gpsr_category_3_grammar.txt")]
    generator.load_rules(grammar_files)

    semantics = [importlib_resources.open_text(grammar_dir, "gpsr_category_1_semantics.txt"),
                 importlib_resources.open_text(grammar_dir, "gpsr_category_2_semantics.txt"),
                 importlib_resources.open_text(grammar_dir, "gpsr_category_3_semantics.txt")]
    generator.load_semantics_rules(semantics)
    for file in semantics + grammar_files:
        file.close()
    return generator


def load_all(generator, task, grammar_dir, expand_shorthand=True):

    generator.knowledge_base = KnowledgeBase()
    generator.knowledge_base.load_from_xml_dir(grammar_dir)
    with importlib_resources.open_text(grammar_dir, "common_rules.txt") as common_rules_file, importlib_resources.open_text(grammar_dir, task + ".txt") as task_rules:
        generator.load_rules([common_rules_file, task_rules],
                         expand_shorthand=expand_shorthand)

    with importlib_resources.open_text(grammar_dir, "gpsr_semantics.txt") as semantics:
        generator.load_semantics_rules(semantics)
