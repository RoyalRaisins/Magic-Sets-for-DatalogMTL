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
import gc

datapath = f"./lubm_data/lubm_10^6.txt"
program_path = f"./lubm_programs/p.txt"
dataset = load_dataset(datapath)
coalescing_d(dataset)

with open(program_path, "r") as f:
    rules = f.readlines()
    original_program = load_program(rules)

# entailed
query_list = [
"AssistantProfessorCandidate(ID0)@18",
"AssistantProfessorCandidate(ID1)@14",
"AssociateProfessor(ID0)@34",
"AssociateProfessor(ID1)@19",
"AssociateProfessorCandidate(ID0)@19",
"AssociateProfessorCandidate(ID1)@18",
"Chair(ID2002)@8",
"Chair(ID3738)@36",
"Employee(ID0)@36",
"Employee(ID1)@13",
"Faculty(ID0)@40",
"Faculty(ID1)@18",
"FullProfessor(ID11)@67",
"FullProfessor(ID11)@78",
"FullProfessor(ID24)@45",
"FullProfessor(ID24)@57",
"FullProfessorCandidate(ID4)@24",
"FullProfessorCandidate(ID7)@12",
"GoodDepartment(ID16)@40",
"GoodDepartment(ID1971)@19",
"Lecturer(ID0)@12",
"Lecturer(ID1)@12",
"LecturerCandidate(ID0)@35",
"LecturerCandidate(ID1)@15",
"Organization(ID12)@44",
"Organization(ID16)@29",
"Publication(ID6)@21",
"ResearchAssistant(ID0)@32",
"ResearchAssistant(ID1)@18",
"ResearchAssistantCandidate(ID0)@12",
"ResearchAssistantCandidate(ID1)@19",
"Scientist(ID11)@61",
"Scientist(ID11)@88",
"Scientist(ID24)@34",
"Scientist(ID24)@53",
"ScientistCandidate(ID11)@46",
"ScientistCandidate(ID24)@22",
"SmartStudent(ID0)@25",
"SmartStudent(ID1)@36",
"Student(ID0)@29",
"Student(ID1)@11",
"TeachingAssistant(ID4)@5",
"TeachingAssistant(ID7)@23",
"Work(ID18)@26",
"Work(ID2)@38",
"Employee(ID24)@149",
"Employee(ID26)@149",
"Employee(ID50)@149",
"Faculty(ID24)@149",
"Faculty(ID26)@149",
"Faculty(ID50)@149",
"FullProfessor(ID50)@149",
"FullProfessor(ID26)@149",
"FullProfessor(ID24)@149",
"Scientist(ID50)@149",
"Scientist(ID26)@149",
"Scientist(ID24)@149",
]

fact_list = []

for query in query_list:
    fact = parse_str_fact(query)
    F = Atom(fact[0], fact[1], fact[2])
    fact_list.append(F)
    print(F)

parsed_queries = []

for query in query_list:
    match = re.match(r'^([a-zA-Z]+)\((ID\d+)\)@(\d+)$', query)
    if match:
        predicate = match.group(1)
        ID = match.group(2)
        score = match.group(3)
        parsed_queries.append({
            'predicate': predicate,
            'ID': ID,
            'score': score
        })

for parsed_query in parsed_queries:
    print(f"Predicate: {parsed_query['predicate']}, ID: {parsed_query['ID']}, Score: {parsed_query['score']}")

cnt = 0

for parsed_query in parsed_queries:
    
    gc.collect()

    # Ideally, this copy should be lazy
    D = copy.deepcopy(dataset)

    fact = parse_str_fact(query_list[cnt])

    F = Atom(fact[0], fact[1], fact[2])
    print(F)

    program, D, magic_time = produce_magic_pair(original_program, D, F)
    print("Magic Time:", magic_time)

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
        D1, common, varrho_left, left_period, left_len, varrho_right, right_period, right_len = find_periods_with_query(CR,F,datasetname="lubm",is_entailed="entailed")
    except Exception as e:
        print("entailed!")
        print(f"total_time is(without CR):{float(str(e)) + init_time + float(magic_time)}")
        with open(f"./lubm_new_program_results_entailed/{query_list[cnt]}_magic_new_inside.txt", 'w') as f:
            f.write(f"total_time is(without CR):{float(str(e)) + init_time + float(magic_time)}")
            f.write(f"\nmagic_and_reasoning_time:{float(magic_time) + float(str(e))}")
            f.write(f"\ninitial time:{init_time}")
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
    with open(f"./lubm_new_program_results_entailed/{query_list[cnt]}_magic_new_outside.txt", 'w') as f:
        f.write(f"Final Entailment from canonical representation:{entailment_result}\ntotal_time is(with CR):{end_canonical_build_time - start_canonical_build_time + init_time + float(magic_time)}")
        f.write(f"\nmagic_and_reasoning_time:{float(magic_time) + end_canonical_build_time - start_canonical_build_time}")
        f.write(f"\ninitial time:{init_time}")
    cnt += 1
    del CR
    del D
    gc.collect()