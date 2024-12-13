from meteor_reasoner.materialization.coalesce import *
from meteor_reasoner.materialization.index_build import *
from meteor_reasoner.utils.loader import *
from meteor_reasoner.canonical.magic_utils import find_periods_with_query
from meteor_reasoner.canonical.canonical_representation import CanonicalRepresentation
from meteor_reasoner.utils.parser import parse_str_fact
from meteor_reasoner.classes.atom import Atom
from meteor_reasoner.canonical.utils import fact_entailment
from meteor_reasoner.utils.operate_dataset import get_min_max_rational
from produce_magic_pair import produce_magic_pair
from openpyxl import Workbook
import time
import os
import copy
import gc

program_path = f"./lubm_programs/p.txt"
with open(program_path, "r") as f:
    rules = f.readlines()
    original_program = load_program(rules)

predicate_list = [
    "AssistantProfessorCandidate",
    "AssociateProfessor",
    "AssociateProfessorCandidate",
    "Chair",
    "Course",
    "Employee",
    "Faculty",
    "FullProfessor",
    "FullProfessorCandidate",
    "GoodDepartment",
    "Lecturer",
    "LecturerCandidate",
    "Organization",
    "Publication",
    "ResearchAssistant",
    "ResearchAssistantCandidate",
    "Scientist",
    "ScientistCandidate",
    "SmartStudent",
    "Student",
    "TeachingAssistant",
    "University",
    "Work"
]

for dataset_index in range(2,7):
    datapath = f"./lubm_data/lubm_10^{dataset_index}.txt"
    dataset = load_dataset(datapath)
    coalescing_d(dataset)
    wb_for_statistics = Workbook()
    ws_for_statistics = wb_for_statistics.active

    ws_for_statistics.append(["Predicate", "Total query count", "Total entailed count", "Total not entailed count", "Total entailed time", "Total not entailed time","Total initial time", "Avg entailed time", "Avg not entailed time","Avg initial time"])

    for predicate in predicate_list:
        rulepath = f"./programs/lubm_{predicate}.txt"

        datapath_filename = os.path.basename(datapath).split('.')[0]
        program_filename = os.path.basename(rulepath).split('.')[0]

        query_results = f"./query_results/CR_10^{dataset_index}_{predicate}.txt"

        filename = query_results
        id_list = []

        with open(filename, 'r') as file:
            for line in file:
                if predicate in line:
                    start_index = line.find('ID') + 2
                    end_index = line.find(')', start_index)
                    candidate_id = int(line[start_index:end_index])
                    id_list.append(candidate_id)

        id_list.sort()
        with open(filename, 'r') as f:
            lines = f.readlines()

        min_intervals = []
        max_intervals = []

        for line in lines:
            id_start = line.find('SmartStudent(ID') + len('SmartStudent(ID')
            min_start = line.find('Min Interval: ', id_start) + len('Min Interval: ')
            max_start = line.find('Max Interval: ', min_start) + len('Max Interval: ')
            
            min_end = line.find(',', min_start)
            max_end = line.find('\n', max_start)
            
            try:
                min_interval = int(line[min_start:min_end])
                max_interval = int(line[max_start:max_end])
            except ValueError as e:
                continue
            
            min_intervals.append(min_interval)
            max_intervals.append(max_interval)

        total_query_count = 0
        total_entailed_count = 0
        total_not_entailed_count = 0
        total_entailed_time = 0
        total_not_entailed_time = 0
        total_init_time = 0

        # store the statistics
        statistics_file = open(f"./scalability_results/{datapath_filename}_{program_filename}_{predicate}_statistics.txt", 'w')

        wb = Workbook()
        ws = wb.active

        ws.append(["Query", "Final Entailment", "Query Time","Is CR?"])

        cnt = 0

        for i in id_list[0:10]:
            for j in range(0, 4):
                D = copy.deepcopy(dataset)
                min_rational, max_rational = get_min_max_rational(D)
                if(j == 0):
                    tmp_fact_str = f"{predicate}(ID{i})@{random.randint(min_intervals[cnt], max_intervals[cnt])}"
                    cnt += 1
                if(j == 1):
                    tmp_fact_str = f"{predicate}(ID{i})@{random.randint(max_rational, max_rational * 2)}"
                if(j == 2):
                    tmp_fact_str = f"{predicate}(ID{i})@{random.randint(-max_rational,0)}"
                if(j == 3):
                    tmp_fact_str = f"{predicate}(ID-{i})@{random.randint(0,max_rational)}"
                fact = parse_str_fact(tmp_fact_str)
                F = Atom(fact[0], fact[1], fact[2])

                program, D , magic_time = produce_magic_pair(original_program, D, F)

                # start initial time
                start_initial_time = time.time()

                # Find the Canonical Representation
                CR = CanonicalRepresentation(D, program)
                CR.initilization()

                # initial time
                end_init_time = time.time()
                init_time = end_init_time - start_initial_time

                # Start the canonical timer
                start_canonical_build_time = time.time()

                try:
                    D1, common, varrho_left, left_period, left_len, varrho_right, right_period, right_len = find_periods_with_query(CR,F,datasetname="lubm",is_entailed="entailed")
                except Exception as e:
                    ws.append([tmp_fact_str, True, f"{float(str(e)) + init_time + float(magic_time)}", "False"])
                    total_entailed_count += 1
                    total_query_count += 1
                    total_init_time += init_time
                    total_entailed_time += float(str(float(str(e)))) + init_time + float(magic_time)
                    del CR
                    del D
                    gc.collect()
                    continue

                # Stop the canonical timer
                end_canonical_build_time = time.time()

                # Test the entailment
                entailment_result = fact_entailment(D1, F, common, left_period, left_len, right_period, right_len)

                if entailment_result:
                    total_entailed_count += 1
                    total_entailed_time += end_canonical_build_time - start_canonical_build_time + float(magic_time)
                else:
                    total_not_entailed_count += 1
                    total_not_entailed_time += end_canonical_build_time - start_canonical_build_time + float(magic_time)
                
                total_query_count += 1
                total_init_time += init_time

                ws.append([tmp_fact_str, entailment_result, f"{end_canonical_build_time - start_canonical_build_time + init_time + float(magic_time)}","True"])
                del CR
                del D
                gc.collect()

        # excel file
        wb.save(f"./scalability_results/{datapath_filename}_{program_filename}_{predicate}.xlsx")

        statistics_file.write(f"Total query count: {total_query_count}\n")
        statistics_file.write(f"Total entailed count: {total_entailed_count}\n")
        statistics_file.write(f"Total not entailed count: {total_not_entailed_count}\n")
        statistics_file.write(f"Total entailed time: {total_entailed_time}\n")
        statistics_file.write(f"Total not entailed time: {total_not_entailed_time}\n")
        statistics_file.write(f"Total init time: {total_init_time}\n")
        if total_entailed_count != 0:
            statistics_file.write(f"Avg entailed time: {total_entailed_time/total_entailed_count}\n")
        else:
            statistics_file.write(f"Avg entailed time: 0\n")
        if total_not_entailed_count != 0:
            statistics_file.write(f"Avg not entailed time: {total_not_entailed_time/total_not_entailed_count}\n")
        else:
            statistics_file.write(f"Avg not entailed time: 0\n")

        avg_entailed_time = total_entailed_time / total_entailed_count if total_entailed_count != 0 else 0
        avg_not_entailed_time = total_not_entailed_time / total_not_entailed_count if total_not_entailed_count != 0 else 0
        avg_init_time = total_init_time / total_query_count if total_query_count != 0 else 0

        ws_for_statistics.append([
            predicate,
            total_query_count,
            total_entailed_count,
            total_not_entailed_count,
            total_entailed_time,
            total_not_entailed_time,
            total_init_time,
            avg_entailed_time,
            avg_not_entailed_time,
            avg_init_time
        ])
    
    wb_for_statistics.save(f"./scalability_results/{datapath_filename}_statistics.xlsx")