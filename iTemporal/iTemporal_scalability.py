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
import copy
import os
import re
import gc

rulepath = f"./iTemporal_programs/iTemporal_program.txt"
with open(rulepath) as file:
    rules = file.readlines()
    original_program = load_program(rules)

iTemporal_predicate_list = [
    "g4859",
    "g4860",
    "g4862",
    "g4863",
    "g4864",
    "g4866",
    "g4867",
    "g4869",
    "g4901"
]

predicate_list = iTemporal_predicate_list

for dataset_index in range(1,6):
    datapath = f"./iTemporal_data/10^{dataset_index}/"
    dataset = load_dataset(datapath)
    wb_for_statistics = Workbook()
    ws_for_statistics = wb_for_statistics.active

    ws_for_statistics.append(["Predicate", "Total query count", "Total entailed count", "Total not entailed count", "Total entailed time", "Total not entailed time","Total initial time", "Avg entailed time", "Avg not entailed time","Avg initial time"])

    for predicate in predicate_list:
        rulepath = f"./iTemporal_programs/iTemporal_{predicate}.txt"

        datapath_filename = "iTemporal_10^" + str(dataset_index)
        program_filename = os.path.basename(rulepath).split('.')[0]

        query_results = f"./query_results/ITemporal_10^{dataset_index}_{predicate}.txt"

        filename = query_results

        pattern = r'g(\d+)\(([\d.]+),([\d.]+)\)'

        with open(f'./query_results/ITemporal_10^{dataset_index}_{predicate}.txt', 'r') as file:
            text = file.read()

        matches = re.findall(pattern, text)

        for match in matches:
            entity1 = match[1]
            entity2 = match[2]
            print(f"Predicate: g{match[0]}, Entity 1: {entity1}, Entity 2: {entity2}")

        with open(filename, 'r') as f:
            lines = f.readlines()

        min_intervals = []
        max_intervals = []

        for line in lines:
            id_start = 0
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
        total_initial_time = 0

        # store the statistics
        statistics_file = open(f"./scalability_results/{datapath_filename}_{program_filename}_{predicate}_statistics.txt", 'w')

        wb = Workbook()
        ws = wb.active

        ws.append(["Query", "Final Entailment", "Query Time","Is CR?"])

        cnt = 0

        for match in matches[:10]:
            for j in range(0, 12):
                D = copy.deepcopy(dataset)
                min_rational, max_rational = get_min_max_rational(D)
                if(j <= 5):
                    tmp_fact_str = f"{predicate}({match[1]},{match[2]})@{random.randint(min_intervals[cnt], max_intervals[cnt])}"
                if(j <= 8 and j > 5):
                    tmp_fact_str = f"{predicate}({match[1]},{match[2]})@{random.randint(max_rational, max_rational * 2)}"
                if(j == 9):
                    tmp_fact_str = f"{predicate}({match[1]},{match[2]})@{random.randint(-max_rational,0)}"
                    cnt += 1
                if(j == 10 or j == 11):
                    tmp_fact_str = f"{predicate}(-{match[1]},-{match[2]})@{random.randint(-max_rational, max_rational * 2)}"
                fact = parse_str_fact(tmp_fact_str)
                F = Atom(fact[0], fact[1], fact[2])

                if j <= 10:
                    D[f"magic_{predicate}_bb"][tuple([Term(match[1]),Term(match[2])])].append(Interval(decimal.Decimal("-inf"), decimal.Decimal("+inf"),True,True))
                elif j == 11 or j == 12:
                    D[f"magic_{predicate}_bb"][tuple([Term("-"+match[1]),Term("-"+match[2])])].append(Interval(decimal.Decimal("-inf"), decimal.Decimal("+inf"),True,True))
                
                program, D, magic_time = produce_magic_pair(original_program, D, F)
                #start the initial time
                start_initial_time = time.time()

                # Find the Canonical Representation
                CR = CanonicalRepresentation(D, program)
                CR.initilization()

                # initial time
                end_initial_time = time.time()
                init_time = end_initial_time - start_initial_time

                # Start the canonical timer
                start_canonical_build_time = time.time()
                
                try:
                    D1, common, varrho_left, left_period, left_len, varrho_right, right_period, right_len = find_periods_with_query(CR,F,datasetname="iTemporal",is_entailed="entailed")
                except Exception as e:
                    ws.append([tmp_fact_str, True, f"{float(str(e)) + init_time + float(magic_time)}", "False"])
                    total_entailed_count += 1
                    total_query_count += 1
                    total_entailed_time += float(str(e)) + float(magic_time)
                    total_initial_time += init_time
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
                total_initial_time += init_time

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
        statistics_file.write(f"Total initial time: {total_initial_time}\n")
        if total_entailed_count != 0:
            statistics_file.write(f"Avg entailed time: {total_entailed_time/total_entailed_count}\n")
        else:
            statistics_file.write(f"Avg entailed time: 0\n")
        if total_not_entailed_count != 0:
            statistics_file.write(f"Avg not entailed time: {total_not_entailed_time/total_not_entailed_count}\n")
        else:
            statistics_file.write(f"Avg not entailed time: 0\n")
        if total_query_count != 0:
            statistics_file.write(f"Avg initial time: {total_initial_time/total_query_count}\n")
        else:
            statistics_file.write(f"Avg initial time: 0\n")
        
        avg_entailed_time = total_entailed_time / total_entailed_count if total_entailed_count != 0 else 0
        avg_not_entailed_time = total_not_entailed_time / total_not_entailed_count if total_not_entailed_count != 0 else 0
        avg_initial_time = total_initial_time / total_query_count if total_query_count != 0 else 0

        ws_for_statistics.append([
            predicate,
            total_query_count,
            total_entailed_count,
            total_not_entailed_count,
            total_entailed_time,
            total_not_entailed_time,
            total_initial_time,
            avg_entailed_time,
            avg_not_entailed_time,
            avg_initial_time
        ])
    
    wb_for_statistics.save(f"./scalability_results/{datapath_filename}_statistics.xlsx")
