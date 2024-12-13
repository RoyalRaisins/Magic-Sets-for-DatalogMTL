from meteor_reasoner.materialization.coalesce import *
from meteor_reasoner.materialization.index_build import *
from meteor_reasoner.utils.loader import *
from meteor_reasoner.canonical.magic_utils import find_periods_with_query
from meteor_reasoner.canonical.canonical_representation import CanonicalRepresentation
from meteor_reasoner.utils.parser import parse_str_fact
from meteor_reasoner.classes.atom import Atom
from meteor_reasoner.canonical.utils import fact_entailment
from produce_magic_pair import produce_magic_pair
import time
import re
import copy

datapath = f"./weather_data/weather_dataset.txt"
program_path = f"./weather_programs/w.txt"
dataset = load_dataset(datapath)
coalescing_d(dataset)

with open(program_path, "r") as f:
    rules = f.readlines()
    original_program = load_program(rules)

# entailed facts
query_list = [
"ExcessiveHeat(station533)@1295",
"HeatAffectedState(color)@1310",
"HeavyWind(station4863)@1901",
"HeavyWindAffectedState(glakes)@417"
]

pattern = re.compile(r'(\w+)\((\w+)\)@(\d+)')

for query in query_list:

    match = pattern.match(query)
    if match:
        predicate, entity, intervalnum = match.groups()
        print(f"Predicate: {predicate}, Entity: {entity}, Intervalnum: {intervalnum}")

    D = copy.deepcopy(dataset)

    fact = parse_str_fact(query)
    F = Atom(fact[0], fact[1], fact[2])
    print(F)

    program, D, magic_time = produce_magic_pair(original_program, D, F)

    # start init time
    start_init_time = time.time()

    # Find the Canonical Representation
    CR = CanonicalRepresentation(D, program)
    CR.initilization()

    #initial time
    end_init_time = time.time()
    init_time = end_init_time - start_init_time

    # Start the canonical timer
    start_canonical_build_time = time.time()

    try:
        D1, common, varrho_left, left_period, left_len, varrho_right, right_period, right_len = find_periods_with_query(CR,F,datasetname="weather",is_entailed="entailed")
    except Exception as e:
        print("entailed!")
        print(f"total_time is(without CR):{float(str(e)) + init_time + float(magic_time)}")
        print(f"initial time is:{init_time}")
        with open(f"./weather_new_program_results_entailed/{str(F)}_magic_new_inside.txt", 'w') as f:
            f.write(f"total_time is(without CR):{float(str(e)) + init_time + float(magic_time)}\n")
            f.write(f"initial time is:{init_time}")
        continue

    # Stop the canonical timer
    end_canonical_build_time = time.time()
    print("end_canonical_build_time is:", end_canonical_build_time, "seconds")

    # Test the entailment
    entailment_result = fact_entailment(D1, F, common, left_period, left_len, right_period, right_len)
    print("Final Entailment from canonical representation:", entailment_result)
    print("total_time is(with CR):", end_canonical_build_time - start_canonical_build_time + init_time + float(magic_time), "seconds")
    print("end with cr!")
    with open(f"./weather_new_program_results_entailed/{str(F)}_magic_new_outside.txt", 'w') as f:
        f.write(f"Final Entailment from canonical representation:{entailment_result}\ntotal_time is(with CR):{end_canonical_build_time - start_canonical_build_time + init_time + float(magic_time)}")
        f.write(f"\nmagic_and_reasoning_time:{float(magic_time) + end_canonical_build_time - start_canonical_build_time}")
        f.write(f"\ninitial time is:{init_time}")