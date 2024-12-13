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

datapath = f"./weather_data/weather_small_dataset.txt"

rulepath = f"./weather_programs/w.txt"

datapath_filename = os.path.basename(datapath).split('.')[0]
program_filename = os.path.basename(rulepath).split('.')[0]

# entailed facts
query_list = [
"ExcessiveHeat(station533)@1295",
"HeatAffectedState(color)@1310",
"HeavyWind(station4863)@1901",
"HeavyWindAffectedState(glakes)@417"
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

# initial time
start_inital_time = time.time()

# Find the Canonical Representation
CR = CanonicalRepresentation(D, program)
CR.initilization()

#initial time
end_inital_time = time.time()
inital_time = end_inital_time - start_inital_time

# Start the canonical timer
start_canonical_build_time = time.time()

D1, common, varrho_left, left_period, left_len, varrho_right, right_period, right_len = find_periods_with_query_list(CR,fact_list,inital_time,datasetname="weather")

# Stop the canonical timer
end_canonical_build_time = time.time()

for F in fact_list:
    # Test the entailment
    entailment_result = fact_entailment(D1, F, common, left_period, left_len, right_period, right_len)
    print("Final Entailment from canonical representation:", entailment_result)
    print("total_time is(with CR):", end_canonical_build_time - start_canonical_build_time + inital_time, "seconds")
    print("end with cr!")
    with open(f"./weather_baseline_results/"+str(F)+"_outside.txt", 'w') as f:
        f.write(f"Final Entailment from canonical representation:{entailment_result}\ntotal_time is(with CR):{end_canonical_build_time - start_canonical_build_time + inital_time}")
        f.write(f"reasoning_time:{end_canonical_build_time - start_canonical_build_time}")
        f.write(f"initial time is:{inital_time}")