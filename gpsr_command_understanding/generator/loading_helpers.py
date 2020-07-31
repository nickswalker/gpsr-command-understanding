import importlib_resources

from gpsr_command_understanding.generator.generator import Generator
from gpsr_command_understanding.generator.knowledge import KnowledgeBase
from gpsr_command_understanding.generator.paired_generator import PairedGenerator

GRAMMAR_DIR_2018 = "gpsr_command_understanding.resources.generator2018"
GRAMMAR_DIR_2019 = "gpsr_command_understanding.resources.generator2019"
GRAMMAR_DIR_2021 = "gpsr_command_understanding.resources.generator2021"

GRAMMAR_YEAR_TO_MODULE = {2018: GRAMMAR_DIR_2018, 2019: GRAMMAR_DIR_2019, 2021: GRAMMAR_DIR_2021}

def load_2018_by_cat(grammar_dir):
    kb = KnowledgeBase.from_xml_dir(grammar_dir)
    with importlib_resources.open_text(grammar_dir, "common_rules.txt") as common_file:
        common = common_file.readlines()

    cat1_gen = Generator(kb, grammar_format_version=2018)
    cat2_gen = Generator(kb, grammar_format_version=2018)
    cat3_gen = Generator(kb, grammar_format_version=2018)
    with importlib_resources.open_text(grammar_dir, "gpsr_category_1_grammar.txt") as cat1:
        cat1_gen.load_rules([common, cat1])
    with importlib_resources.open_text(grammar_dir, "gpsr_category_2_grammar.txt") as cat2:
        cat2_gen.load_rules([common, cat2])
    with importlib_resources.open_text(grammar_dir, "gpsr_category_3_grammar.txt") as cat3:
        cat3_gen.load_rules([common, cat3])

    return [cat1_gen, cat2_gen, cat3_gen]


def load_paired_2018_by_cat(grammar_dir):
    cat1_gen, cat2_gen, cat3_gen = map(PairedGenerator.from_generator, load_2018_by_cat(grammar_dir))

    with importlib_resources.open_text(grammar_dir, "gpsr_category_1_semantics.txt") as cat1:
        cat1_gen.load_semantics_rules(cat1)
    with importlib_resources.open_text(grammar_dir,
                                       "gpsr_category_1_semantics.txt") as cat1, importlib_resources.open_text(
            grammar_dir, "gpsr_category_2_semantics.txt") as cat2:
        cat2_gen.load_semantics_rules([cat1, cat2])
    with importlib_resources.open_text(grammar_dir, "gpsr_category_3_semantics.txt") as cat3:
        cat3_gen.load_semantics_rules([cat3])

    return [cat1_gen, cat2_gen, cat3_gen]


def load_2018(grammar_dir):
    kb = KnowledgeBase.from_xml_dir(grammar_dir)
    generator = Generator(kb, grammar_format_version=2018)

    common_path = importlib_resources.open_text(grammar_dir, "common_rules.txt")
    grammar_files = [common_path, importlib_resources.open_text(grammar_dir, "gpsr_category_1_grammar.txt"),
                     importlib_resources.open_text(grammar_dir, "gpsr_category_2_grammar.txt"),
                     importlib_resources.open_text(grammar_dir, "gpsr_category_3_grammar.txt")]
    generator.load_rules(grammar_files)

    for file in grammar_files:
        file.close()
    return generator


def load_paired_2018(grammar_dir):
    generator = load_2018(grammar_dir)
    generator = PairedGenerator.from_generator(generator)
    semantics = [importlib_resources.open_text(grammar_dir, "gpsr_category_1_semantics.txt"),
                 importlib_resources.open_text(grammar_dir, "gpsr_category_2_semantics.txt"),
                 importlib_resources.open_text(grammar_dir, "gpsr_category_3_semantics.txt")]
    generator.load_semantics_rules(semantics)
    for file in semantics:
        file.close()
    return generator


def load(generator, task, grammar_dir, expand_shorthand=True):
    generator.knowledge_base = KnowledgeBase.from_xml_dir(grammar_dir)
    with importlib_resources.open_text(grammar_dir, task + ".txt") as task_rules_file:
        task_rules = task_rules_file.readlines()
    # Only load common rules if they're imported in this task's grammar
    if any(map(lambda rule: "common.txt" in rule, task_rules)):
        with importlib_resources.open_text(grammar_dir, "common_rules.txt") as common_rules_file:
            task_rules += common_rules_file.readlines()
    generator.load_rules([task_rules],
                         expand_shorthand=expand_shorthand)


def load_paired(generator, task, grammar_dir, expand_shorthand=True):
    load(generator, task, grammar_dir, expand_shorthand=expand_shorthand)
    generator = PairedGenerator.from_generator(generator)
    with importlib_resources.open_text(grammar_dir, task + "_semantics.txt") as semantics:
        generator.load_semantics_rules(semantics)
