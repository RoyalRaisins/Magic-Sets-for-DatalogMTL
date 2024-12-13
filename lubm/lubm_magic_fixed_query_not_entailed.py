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
import os
import re
import copy
import gc

datapath = f"./lubm_data/lubm_10^6.txt"
program_path = f"./lubm_programs/p.txt"
datapath_filename = os.path.basename(datapath).split('.')[0]
dataset = load_dataset(datapath)
coalescing_d(dataset)

with open(program_path, "r") as f:
    rules = f.readlines()
    original_program = load_program(rules)

# not entailed
query_list = [
"AssistantProfessorCandidate(ID0)@56",
"AssistantProfessorCandidate(ID1)@94",
"AssociateProfessor(ID0)@70",
"AssociateProfessor(ID1)@88",
"AssociateProfessorCandidate(ID0)@94",
"AssociateProfessorCandidate(ID1)@93",
"Chair(ID2002)@92",
"Chair(ID3738)@93",
"Course(ID18)@55",
"Course(ID2)@69",
"Employee(ID0)@68",
"Employee(ID1)@84",
"Faculty(ID0)@90",
"Faculty(ID1)@78",
"FullProfessorCandidate(ID4)@85",
"FullProfessorCandidate(ID7)@51",
"GoodDepartment(ID16)@87",
"GoodDepartment(ID1971)@78",
"Lecturer(ID0)@87",
"Lecturer(ID1)@90",
"LecturerCandidate(ID0)@61",
"LecturerCandidate(ID1)@67",
"Organization(ID12)@54",
"Organization(ID16)@80",
"Publication(ID3)@56",
"Publication(ID6)@74",
"ResearchAssistant(ID0)@76",
"ResearchAssistant(ID1)@74",
"ResearchAssistantCandidate(ID0)@100",
"ResearchAssistantCandidate(ID1)@82",
"ScientistCandidate(ID11)@98",
"ScientistCandidate(ID24)@53",
"SmartStudent(ID0)@78",
"SmartStudent(ID1)@96",
"Student(ID0)@84",
"Student(ID1)@51",
"TeachingAssistant(ID4)@71",
"TeachingAssistant(ID7)@85",
"University(ID12)@65",
"University(ID31)@59",
"Work(ID18)@69",
"Work(ID2)@51",
"AssistantProfessorCandidate(ID-0)@2",
"AssociateProfessor(ID-0)@20",
"AssociateProfessorCandidate(ID-0)@42",
"Chair(ID-2002)@30",
"Course(ID-2)@37",
"Employee(ID-0)@1",
"Faculty(ID-0)@36",
"FullProfessor(ID-11)@40",
"FullProfessorCandidate(ID-4)@0",
"GoodDepartment(ID-16)@28",
"Lecturer(ID-0)@44",
"LecturerCandidate(ID-0)@19",
"Organization(ID-12)@49",
"Publication(ID-3)@29",
"ResearchAssistant(ID-0)@35",
"ResearchAssistantCandidate(ID-0)@31",
"Scientist(ID-11)@36",
"ScientistCandidate(ID-11)@11",
"SmartStudent(ID-0)@6",
"Student(ID-0)@10",
"TeachingAssistant(ID-4)@6",
"University(ID-12)@29",
"Work(ID-2)@30"
]

pattern = re.compile(r'(\w+)\(([\w-]+)\)@(\d+)')

cnt = 0
for query in query_list:
    
    match = pattern.match(query)
    if match:
        predicate, entity, intervalnum = match.groups()

    D = copy.deepcopy(dataset)

    fact = parse_str_fact(query)
    F = Atom(fact[0], fact[1], fact[2])
    print(F)
    
    program, D, magic_time = produce_magic_pair(original_program, D, F)
    print("Magic Time:", magic_time)

    #start init time
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
        D1, common, varrho_left, left_period, left_len, varrho_right, right_period, right_len = find_periods_with_query(CR,F,datasetname="lubm",is_entailed="not_entailed")
    except Exception as e:
        print("entailed!")
        print(f"total_time is(without CR):{float(str(e)) + init_time + float(magic_time)}")
        with open(f"./lubm_new_program_results_not_entailed/{query}_magic_new_inside.txt", 'w') as f:
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
    with open(f"./lubm_new_program_results_not_entailed/{query}_magic_new_outside.txt", 'w') as f:
        f.write(f"Final Entailment from canonical representation:{entailment_result}\ntotal_time is(with CR):{end_canonical_build_time - start_canonical_build_time + init_time + float(magic_time)}")
        f.write(f"\nmagic_and_reasoning_time:{float(magic_time) + end_canonical_build_time - start_canonical_build_time}")
        f.write(f"\ninitial time:{init_time}")
    cnt += 1
    del CR
    del D
    gc.collect()