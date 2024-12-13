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
import copy
import re
import gc

datapath = f"./iTemporal_data/10^5"
program_path = f"./iTemporal_programs/iTemporal_program.txt"
dataset = load_dataset(datapath)
coalescing_d(dataset)

with open(program_path, "r") as f:
    rules = f.readlines()
    original_program = load_program(rules)

# entailed
query_list = [
"g4862(94.0,36.0)@13412",
"g4862(94.0,36.0)@11372",
"g4863(302.0,68.0)@9211",
"g4863(337.0,83.0)@7993",
"g4864(1.0,0.0)@13633",
"g4864(1.0,1.0)@12736",
"g4866(302.0,68.0)@2009",
"g4866(337.0,83.0)@12965",
"g4867(130.0,1.0)@13008",
"g4867(302.0,68.0)@19180",
"g4869(36.0,94.0)@13464",
"g4869(302.0,68.0)@14694",
"g4901(130.0,1.0)@10613",
"g4901(136.0,97.0)@6882"
]

fact_list = []

for query in query_list:
    fact = parse_str_fact(query)
    F = Atom(fact[0], fact[1], fact[2])
    fact_list.append(F)
    print(F)

parsed_queries = []

for query in query_list:
    match = re.match(r'^([a-zA-Z]+\d+)\(([\d.]+),([\d.]+)\)@(\d+)$', query)
    if match:
        predicate = match.group(1)
        entity1 = match.group(2), match.group(3)
        entity2 = match.group(4)
        parsed_queries.append({
            'predicate': predicate,
            'entity1': entity1,
            'entity2': entity2
        })

cnt = 0
for parsed_query in parsed_queries:
    
    rulepath = f"./iTemporal_programs/iTemporal_{parsed_query['predicate']}.txt"

    D = copy.deepcopy(dataset)

    fact = parse_str_fact(query_list[cnt])
    F = Atom(fact[0], fact[1], fact[2])
    print(F)

    program, D, magic_time = produce_magic_pair(original_program, D, F)

    # start initial time
    start_inital_time = time.time()

    # Find the Canonical Representation
    CR = CanonicalRepresentation(D, program)
    CR.initilization()

    #initial time
    end_init_time = time.time()
    init_time = end_init_time - start_inital_time

    # Start the canonical timer
    start_canonical_build_time = time.time()

    try:
        D1, common, varrho_left, left_period, left_len, varrho_right, right_period, right_len = find_periods_with_query(CR,F,datasetname="iTemporal",is_entailed="not_entailed")
    except Exception as e:
        print("entailed!")
        print(f"total_time is(without CR):{float(str(e)) + init_time  + float(magic_time)}")
        with open(f"./iTemporal_new_program_results_entailed/{query_list[cnt]}_magic_new_inside.txt", 'w') as f:
            f.write(f"total_time is(without CR):{float(str(e)) + init_time  + float(magic_time)}")
            f.write(f"\nmagic_and_reasoning_time:{float(magic_time) + float(str(e))}")
            f.write(f"\ninitial time is:{init_time}")
        cnt += 1
        del CR
        del D
        gc.collect()
        continue

    # Stop the canonical timer
    end_canonical_build_time = time.time()

    # Test the entailment
    entailment_result = fact_entailment(D1, F, common, left_period, left_len, right_period, right_len)
    print("Final Entailment from canonical representation:", entailment_result)
    print("total_time is(with CR):", end_canonical_build_time - start_canonical_build_time + init_time + float(magic_time), "seconds")
    print("end with cr!")
    with open(f"./iTemporal_new_program_results_entailed/{query_list[cnt]}_magic_new_outside.txt", 'w') as f:
        f.write(f"Final Entailment from canonical representation:{entailment_result}\ntotal_time is(with CR):{end_canonical_build_time - start_canonical_build_time + init_time + float(magic_time)}")
        f.write(f"\nmagic_and_reasoning_time:{float(magic_time) + end_canonical_build_time - start_canonical_build_time}")
        f.write(f"\ninitial time is:{init_time}")
    cnt += 1
    del CR
    del D
    gc.collect()