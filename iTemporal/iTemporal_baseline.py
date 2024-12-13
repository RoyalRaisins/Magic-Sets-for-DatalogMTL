from meteor_reasoner.materialization.coalesce import *
from meteor_reasoner.materialization.index_build import *
from meteor_reasoner.utils.loader import *
from meteor_reasoner.canonical.magic_utils import find_periods_with_query_list
from meteor_reasoner.canonical.canonical_representation import CanonicalRepresentation
from meteor_reasoner.utils.parser import parse_str_fact
from meteor_reasoner.classes.atom import Atom
from meteor_reasoner.canonical.utils import fact_entailment
import time
import os

datapath = f"./iTemporal_data/10^5"

rulepath = f"./iTemporal_programs/iTemporal_program.txt"

datapath_filename = os.path.basename(datapath).split('.')[0]
program_filename = os.path.basename(rulepath).split('.')[0]

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

# Load the program
with open(rulepath) as file:
    rules = file.readlines()
    program = load_program(rules)

D = load_dataset(datapath)

# start inital time
start_inital_time = time.time()

# Find the Canonical Representation
CR = CanonicalRepresentation(D, program)
CR.initilization()

#initial time
end_inital_time = time.time()
inital_time = end_inital_time - start_inital_time

# Start the canonical timer
start_canonical_build_time = time.time()

D1, common, varrho_left, left_period, left_len, varrho_right, right_period, right_len = find_periods_with_query_list(CR,fact_list,inital_time,datasetname="iTemporal")

# Stop the canonical timer
end_canonical_build_time = time.time()

for F in fact_list:
    # Test the entailment
    entailment_result = fact_entailment(D1, F, common, left_period, left_len, right_period, right_len)
    print("Final Entailment from canonical representation:", entailment_result)
    print("total_time is(with CR):", end_canonical_build_time - start_canonical_build_time, "seconds")
    print("end with cr!")
    with open(f"./iTemporal_baseline_results/"+str(F)+"_outside.txt", 'w') as f:
        f.write(f"Final Entailment from canonical representation:{entailment_result}\ntotal_time is(with CR):{end_canonical_build_time - start_canonical_build_time}")
        f.write(f"\nreasoning_time:{end_canonical_build_time - start_canonical_build_time}")
        f.write(f"\ninitial time is:{inital_time}")