from meteor_reasoner.materialization.index_build import *
from meteor_reasoner.materialization.coalesce import *
from meteor_reasoner.materialization.t_operator import naive_immediate_consequence_operator
from meteor_reasoner.utils.ruler_interval import *
from meteor_reasoner.canonical.class_common_fragment import CommonFragment
import time
import psutil
import os
import collections

def find_common_fragment(D1, D2, rules, varrho):
    points, min_x, max_x = get_dataset_points_x(D2, min_x_flag=True)
    _, gcd = get_gcd(rules)
    _, initial_window_ruler_intervals = get_initial_ruler_intervals(points, left_border=min_x, right_border=max_x, gcd=gcd)
    left_point = Interval(varrho.left_value, varrho.left_value, False, False)
    right_point = Interval(varrho.right_value, varrho.right_value, False, False)
    left_i = initial_window_ruler_intervals.index(left_point)
    right_i = initial_window_ruler_intervals.index(right_point)

    middle_i = left_i
    while middle_i <= right_i:
        flag = False
        ruler_interval = initial_window_ruler_intervals[middle_i]
        for predicate in D2:
            for entity in D2[predicate]:
                if interval_intesection_intervallist(ruler_interval, D2[predicate][entity]):
                    if predicate not in D1 or entity not in D1[predicate] or not \
                            interval_intesection_intervallist(ruler_interval, D1[predicate][entity]):
                        flag = True
                        break
            if flag:
                return None, None
        middle_i += 1

    left_border = None
    while left_i > 0:
        left_i -= 1
        ruler_interval = initial_window_ruler_intervals[left_i]
        for predicate in D2:
            flag = False
            for entity in D2[predicate]:
                if interval_intesection_intervallist(ruler_interval, D2[predicate][entity]):
                    if predicate not in D1 or entity not in D1[predicate] or not \
                            interval_intesection_intervallist(ruler_interval, D1[predicate][entity]):
                        left_border = ruler_interval
                        flag = True
                        break
            if flag:
                break

    right_border = None
    while right_i < len(initial_window_ruler_intervals)-1:
        right_i += 1
        ruler_interval = initial_window_ruler_intervals[right_i]
        flag = False
        for predicate in D2:
            for entity in D2[predicate]:
                if interval_inclusion_intervallist(ruler_interval, D2[predicate][entity]):
                    if predicate in D1 and entity in D1[predicate] and interval_inclusion_intervallist(
                            ruler_interval, D1[predicate][entity]):
                        continue
                    else:
                        if ruler_interval.left_open:
                            right_border = Interval(ruler_interval.left_value, ruler_interval.left_value, False, False)
                        else:
                            right_border = Interval(ruler_interval.left_value, ruler_interval.left_value, True, True)
                        flag = True
                        break
            if flag:
                break
        if flag:
            break

    if left_border is None:
        left_value, left_open = decimal.Decimal("-inf"), True
    else:
        left_value, left_open = left_border.left_value, left_border.left_open

    if right_border is None:
        right_value, right_open = decimal.Decimal("inf"), True
    else:
        right_value, right_open = right_border.left_value, right_border.left_open

    varrho_left_range = None
    if Interval.is_valid_interval(left_value, varrho.left_value, left_open, True):
        varrho_left_range = Interval(left_value, varrho.left_value, left_open, True)
    varrho_right_range = None
    if Interval.is_valid_interval(varrho.right_value, right_value, True, right_open):
        varrho_right_range = Interval(varrho.right_value, right_value, True, right_open)

    return varrho_left_range, varrho_right_range


def has_same_pattern(ruler_intervals1, ruler_intervals2):
    """
    Check whether the give two ruler interval lists have the same pattern
    Args:
        ruler_intervals1: a list of ruler-intervals
        ruler_intervals2: a list of ruler-intervals

    Returns:
        True or False
    """
    if len(ruler_intervals1) != len(ruler_intervals2):
        return False
    if ruler_intervals1[0].left_open != ruler_intervals2[0].left_open or \
            ruler_intervals1[-1].right_open != ruler_intervals2[-1].right_open:
        return False
    for ruler1, ruler2 in zip(ruler_intervals1, ruler_intervals2):
        if abs(ruler1.right_value-ruler1.left_value) != abs(ruler2.right_value - ruler2.left_value):
            return False
    return True


def has_same_facts(ruler_intervals1, ruler_intervals2, D):
    """
    Check whether the two same-pattern ruler lists have the same facts at each corresponding ruler-interval
    Args:
        ruler_intervals1: a list of ruler-intervals
        ruler_intervals2: a list of ruler-intervals
        D: contain all relational facts
    Returns:
        True or False
    """
    for ruler1, ruler2 in zip(ruler_intervals1, ruler_intervals2):
        for predicate in D:
            for entity in D[predicate]:
                if (interval_inclusion_intervallist(ruler1, D[predicate][entity]) and \
                        not interval_inclusion_intervallist(ruler2, D[predicate][entity])) or \
                        (interval_inclusion_intervallist(ruler2, D[predicate][entity]) and
                         not interval_inclusion_intervallist(ruler1, D[predicate][entity])):
                    return False
    return True


def find_left_period(D, left_interval_range, CR):
    big_ruler_intervals, starting_ruler_interval = build_left_ruler_intervals(left_interval_range, CR)
    big_ruler_intervals = big_ruler_intervals[0: big_ruler_intervals.index(starting_ruler_interval) + 1]

    len_big_ruler_intervals = len(big_ruler_intervals)
    for i in range(len_big_ruler_intervals - 1, -1, -1):
        if big_ruler_intervals[i].left_open:
            continue
        first = big_ruler_intervals[i]
        try:
            second_index = big_ruler_intervals.index(Interval(first.left_value - CR.w, first.left_value - CR.w, False, False))

        except:

            break

        first_interval = big_ruler_intervals[second_index: i+1]
        for k in range(i - 1, -1, -1):
            if big_ruler_intervals[k].left_open:
                continue
            first = big_ruler_intervals[k]
            try:
                second_index = big_ruler_intervals.index(
                    Interval(first.left_value - CR.w, first.left_value - CR.w, False, False))
            except:
                break
            second_interval = big_ruler_intervals[second_index: k+1]
            if has_same_pattern(second_interval, first_interval) and has_same_facts(first_interval, second_interval,
                                                                                    D):
                varrho_left_dict = defaultdict(list)
                start_index = second_interval[0].left_value
                end_index = first_interval[0].left_value

                left_period = Interval(start_index, end_index, False, True)

                for predicate in D:
                    for entity in D[predicate]:
                        for ruler in D[predicate][entity]:
                            intersection_ruler = Interval.intersection(ruler, left_period)
                            if intersection_ruler:
                                varrho_left_dict[intersection_ruler].append(str(Atom(predicate, entity)))
                return left_period, varrho_left_dict

    return None, None


def build_right_ruler_intervals(right_interval_range, CR):
    big_ruler_intervals = CR.right_initial_ruler_intervals[:]
    i = 0
    next_point = (big_ruler_intervals[-1].right_value, big_ruler_intervals[-1].right_value + CR.pattern_len[i % CR.pattern_num])
    while next_point[1] < right_interval_range.right_value:
        big_ruler_intervals.append(Interval(next_point[0], next_point[1], True, True))
        big_ruler_intervals.append(Interval(next_point[1], next_point[1], False, False))
        i += 1
        next_point = (big_ruler_intervals[-1].right_value, big_ruler_intervals[-1].right_value + CR.pattern_len[i % CR.pattern_num])
    return big_ruler_intervals, big_ruler_intervals[0]


def build_left_ruler_intervals(left_interval_range, CR):
    big_ruler_intervals = CR.left_initial_ruler_intervals[:]
    i = 0
    next_point = (big_ruler_intervals[0].left_value, big_ruler_intervals[0].left_value - CR.pattern_len[::-1][i % CR.pattern_num])
    while next_point[1] > left_interval_range.left_value:
        big_ruler_intervals = [Interval(next_point[1], next_point[0], True,  True)] + big_ruler_intervals
        big_ruler_intervals = [Interval(next_point[1], next_point[1], False, False)] + big_ruler_intervals
        i += 1
        next_point = (big_ruler_intervals[0].left_value, big_ruler_intervals[0].left_value - CR.pattern_len[::-1][i % CR.pattern_num])
    return big_ruler_intervals, big_ruler_intervals[-1]


def find_right_period(D, right_interval_range, CR):
    big_ruler_intervals,  starting_ruler_interval = build_right_ruler_intervals(right_interval_range, CR)
    big_ruler_intervals = big_ruler_intervals[big_ruler_intervals.index(starting_ruler_interval):]
    len_big_ruler_intervals = len(big_ruler_intervals)

    for i in range(0, len_big_ruler_intervals-1):
        if big_ruler_intervals[i].left_open:
            continue
        first = big_ruler_intervals[i]
        try:
            second_index = big_ruler_intervals.index(Interval(first.left_value + CR.w, first.left_value + CR.w, False, False))
        except:
            break

        first_interval = big_ruler_intervals[i:second_index+1]

        for k in range(i+1, len_big_ruler_intervals):
            if big_ruler_intervals[k].left_open:
                continue
            first = big_ruler_intervals[k]
            try:
                second_index = big_ruler_intervals.index(
                    Interval(first.left_value + CR.w, first.left_value + CR.w, False, False))
            except:
                break

            second_interval = big_ruler_intervals[k: second_index+1]
            if has_same_pattern(second_interval, first_interval) and has_same_facts(first_interval, second_interval, D):
                varrho_right_dict = defaultdict(list)
                start_index = first_interval[-1].right_value
                end_index = second_interval[-1].right_value
                right_period = Interval(start_index, end_index, True, False)

                for predicate in D:
                    for entity in D[predicate]:
                        for ruler in D[predicate][entity]:
                             intersection_ruler = Interval.intersection(ruler, right_period)
                             if intersection_ruler:
                                   varrho_right_dict[intersection_ruler].append(str(Atom(predicate, entity)))
                return right_period,  varrho_right_dict

    return None, None


def entail(fact, D):
    if fact.predicate not in D:
        return False
    else:
        if not fact.entity in D[fact.predicate]:
            return False
        else:
            intervals = D[fact.predicate][fact.entity]
            for interval in intervals:
                if Interval.inclusion(fact.interval, interval):
                    return True
            else:
                return False


def find_periods_with_query(CR,fact,datasetname,is_entailed):
    left_period, left_len = defaultdict(list), 0
    right_period, right_len = defaultdict(list), 0
    number_mat = 0

    # Start the timer
    start_time = time.time()
    while True:
        round_start = time.time()
        common_fragment = CommonFragment(CR.base_interval)
        common_fragment.common = Interval(Decimal("-inf"), Decimal("+inf"), True, True)
        common_fragment_end = time.time()
        common_fragment_time = common_fragment_end - round_start
        # print("common_fragment_time:",common_fragment_time, "seconds")
        if fact != None:
            if entail(fact,CR.D) == True:
                # Stop the timer
                end_time = time.time()
                execution_time = end_time - start_time
                # print("Entailment time:", execution_time, "seconds")
                # print("Entailment: True!")
                # with open(f"./{datasetname}_new_program_results_{is_entailed}/{str(fact)}_magic_new_inside.txt", 'a') as f:
                #     f.write("process_memory is(without CR):" + str(psutil.Process(os.getpid()).memory_info().rss / 1024 ** 2) + "MiB\n")
                raise Exception(execution_time)
        ICO_start = time.time()
        delta_new = naive_immediate_consequence_operator(D=CR.D, rules=CR.Program, D_index=CR.D_index)
        ICO_end = time.time()
        ICO_time = ICO_end - ICO_start
        # print("ICO time:", ICO_time, "seconds")
        number_mat += 1
        diff_delta = []
        terminate_flag = False

        for head_predicate in delta_new:
            for head_entity, T in delta_new[head_predicate].items():
                if head_predicate not in CR.D or head_entity not in CR.D[head_predicate]:
                    diff_delta = T
                else:
                    for interval1 in T:
                        diff_delta += Interval.diff(interval1, CR.D[head_predicate][head_entity])

                for cr_interval in diff_delta: 
                    if not Interval.is_valid_interval(cr_interval.left_value, cr_interval.right_value, cr_interval.left_open, cr_interval.right_open):
                        continue 
                    if Interval.intersection(cr_interval, common_fragment.base_interval):
                        # it denotes that now |\varrho_max != Dnext |\varrho_max
                        common_fragment.cr_flag = False
                        common_fragment.common = None
                        terminate_flag = True
                        break
                    else:
                        if cr_interval.right_value <= common_fragment.base_interval.left_value:
                            if cr_interval.right_value >= common_fragment.common.left_value:
                                common_fragment.common.left_value = cr_interval.right_value
                                common_fragment.common.left_open = not cr_interval.right_open
                        elif cr_interval.left_value >= common_fragment.base_interval.right_value:
                            if cr_interval.left_value <= common_fragment.common.right_value:
                                common_fragment.common.right_value = cr_interval.left_value
                                common_fragment.common.right_open = not cr_interval.left_open
                        else:
                            print(str(cr_interval))
                            print(str(common_fragment.common))
                            raise ValueError("Error Happen")
                if terminate_flag:
                    break

            if terminate_flag:
                break

        if len(diff_delta) == 0:
            # fixpoint
            common_fragment.common.left_value = decimal.Decimal("-inf")
            common_fragment.common.left_open = True
            common_fragment.common.right_value = decimal.Decimal("+inf")
            common_fragment.common.right_open = True
            return CR.D, common_fragment.common, None, None, None, None, None, None
        delta_end = time.time()
        delta_time = delta_end - ICO_end
        # print('delta time:', delta_time, "seconds")
        if common_fragment.common is None or abs(CR.min_x - common_fragment.common.left_value) <= 2 * CR.w or abs(common_fragment.common.right_value - CR.max_x) <= 2 * CR.w:
            altered_atoms = collections.defaultdict(set)
            # add the new facts to the dataset
            for tmp_predicate in delta_new:
                for tmp_entity in delta_new[tmp_predicate]:
                    altered_atoms[tmp_predicate].add(tmp_entity)
                    if tmp_predicate not in CR.D or tmp_entity not in CR.D[tmp_predicate]:
                        CR.D[tmp_predicate][tmp_entity] = CR.D[tmp_predicate][tmp_entity] + delta_new[tmp_predicate][tmp_entity]
                        # update index
                        for i, item in enumerate(tmp_entity):
                            CR.D_index[tmp_predicate][str(i) + "@" + item.name].append(tmp_entity)
                        if len(tmp_entity) > 2:
                            for i, item1 in enumerate(tmp_entity):
                                for j, item2 in enumerate(tmp_entity):
                                    if j <= i:
                                        continue
                                    CR.D_index[tmp_predicate][
                                        str(i) + "@" + item1.name + "||" + str(j) + "@" + item2.name].append(tmp_entity)
                    elif tmp_predicate in CR.D and tmp_entity in CR.D[tmp_predicate]:
                        CR.D[tmp_predicate][tmp_entity] += delta_new[tmp_predicate][tmp_entity]
            # no_period_add_facts_end = time.time()
            # no_period_add_facts_time = no_period_add_facts_end - delta_end
            # print("no_period_add_facts_time:", no_period_add_facts_time, "seconds")
            coalescing_d_altered_atoms(CR.D, altered_atoms)
            # no_period_coalesce_end = time.time()
            # no_period_coalesce_time = no_period_coalesce_end - no_period_add_facts_end
            # # print("no period coalesce_time:", no_period_coalesce_time, "seconds")
            continue

        # it denotes that now |\varrho_max == Dnext |\varrho_max and \varrho_max != \emptyset and t=t_D^- \in \varrho_max,
        # so it satisfies the while conditions in line 4 and line 12
        # \varrho_max = [common_fragment.common.left_value, common_fragment.common.right_value]
        varrho_left_range = Interval(common_fragment.common.left_value, CR.min_x, common_fragment.common.left_open, False)
        varrho_right_range = Interval(CR.max_x, common_fragment.common.right_value, False, common_fragment.common.right_open)

        if varrho_left_range.left_value in [Decimal("-inf")] and varrho_right_range.right_value in [Decimal("+inf")]:
            return CR.D, common_fragment.common, None, None, None, None, None, None

        if varrho_left_range.left_value in [Decimal("-inf")]:
            varrho_right, varrho_right_dict = find_right_period(CR.D, varrho_right_range, CR)
            if varrho_right is not None:
                right_len = varrho_right.right_value - varrho_right.left_value
                for key, values in varrho_right_dict.items():
                    for value in values:
                        right_period[value].append(key)
                for key, value in right_period.items():
                    right_period[key] = coalescing(value)

                return CR.D, common_fragment.common, None, None, None, varrho_right, right_period, right_len
        else:
            varrho_left, varrho_left_dict = find_left_period(CR.D, varrho_left_range, CR)
            if varrho_left is not None:
                if varrho_right_range.right_value in [Decimal("+inf")]:
                    left_len = varrho_left.right_value - varrho_left.left_value
                    for key, values in varrho_left_dict.items():
                        for value in values:
                            left_period[value].append(key)
                    for key, value in left_period.items():
                        left_period[key] = coalescing(value)
                    return CR.D, common_fragment.common, varrho_left, left_period, left_len, None, None, None

                else:
                    varrho_right, varrho_right_dict = find_right_period(CR.D, varrho_right_range, CR)
                    if varrho_right is not None:
                        left_len = varrho_left.right_value - varrho_left.left_value
                        for key, values in varrho_left_dict.items():
                            for value in values:
                                left_period[value].append(key)
                        for key, value in left_period.items():
                            left_period[key] = coalescing(value)

                        right_len = varrho_right.right_value - varrho_right.left_value
                        for key, values in varrho_right_dict.items():
                            for value in values:
                                right_period[value].append(key)
                        for key, value in right_period.items():
                            right_period[key] = coalescing(value)
                        return CR.D, common_fragment.common, varrho_left, left_period, left_len, varrho_right, right_period, right_len
        # periods_end = time.time()
        # find_periods_time = periods_end - delta_end
        # print('find periods time:', find_periods_time, 'seconds')
        altered_atoms = collections.defaultdict(set)
        for tmp_predicate in delta_new:
            for tmp_entity in delta_new[tmp_predicate]:
                altered_atoms[tmp_predicate].add(tmp_entity)
                if tmp_predicate not in CR.D or tmp_entity not in CR.D[tmp_predicate]:
                    CR.D[tmp_predicate][tmp_entity] = delta_new[tmp_predicate][tmp_entity]
                    # update index
                    for i, item in enumerate(tmp_entity):
                        CR.D_index[tmp_predicate][str(i) + "@" + item.name].append(tmp_entity)
                    if len(tmp_entity) > 2:
                        for i, item1 in enumerate(tmp_entity):
                            for j, item2 in enumerate(tmp_entity):
                                if j <= i:
                                    continue
                                CR.D_index[tmp_predicate][
                                    str(i) + "@" + item1.name + "||" + str(j) + "@" + item2.name].append(tmp_entity)
                elif tmp_predicate in CR.D and tmp_entity in CR.D[tmp_predicate]:
                    CR.D[tmp_predicate][tmp_entity] += delta_new[tmp_predicate][tmp_entity]
        # delta_add_end = time.time()
        # add_delta_time = delta_add_end - periods_end
        # print('add delta time:', add_delta_time, 'seconds')
        coalescing_d_altered_atoms(CR.D, altered_atoms)

def find_periods_with_query_list(CR,fact_list,init_time,datasetname):
    left_period, left_len = defaultdict(list), 0
    right_period, right_len = defaultdict(list), 0
    number_mat = 0
    # Start the timer
    start_time = time.time()
    entailed_fact = set()
    while True:
        # append the materialization round and memory usage into the path
        print("Materialization Round: ", number_mat)
        process = psutil.Process()
        print(psutil.Process(os.getpid()).memory_info().rss / 1024 ** 2) # in MiB

        common_fragment = CommonFragment(CR.base_interval)
        common_fragment.common = Interval(Decimal("-inf"), Decimal("+inf"), True, True)

        for fact in fact_list:
            if entail(fact,CR.D) == True and fact not in entailed_fact:
                # Stop the timer
                end_time = time.time()
                execution_time = end_time - start_time + init_time
                #append the result to the output file
                with open(f"./{datasetname}_baseline_results/"+ str(fact) +"_inside.txt", 'w') as f:
                    f.write("total_time is(without CR):" + str(execution_time))
                    f.write("\ninitial time is:" + str(init_time))
                    # f.write("\nprocess_memory is(without CR):" + str(psutil.Process(os.getpid()).memory_info().rss / 1024 ** 2) + "MiB\n")
                    #delete the fact from the list
                entailed_fact.add(fact)

        ICO_start = time.time()
        delta_new = naive_immediate_consequence_operator(D=CR.D, rules=CR.Program, D_index=CR.D_index)
        ICO_end = time.time()
        ICO_time = ICO_end - ICO_start
        # print("ICO time:", ICO_time, "seconds")
        number_mat += 1
        diff_delta = []
        terminate_flag = False

        for head_predicate in delta_new:
            for head_entity, T in delta_new[head_predicate].items():
                if head_predicate not in CR.D or head_entity not in CR.D[head_predicate]:
                    diff_delta = T
                else:
                    for interval1 in T:
                        diff_delta += Interval.diff(interval1, CR.D[head_predicate][head_entity])

                for cr_interval in diff_delta: 
                    if not Interval.is_valid_interval(cr_interval.left_value, cr_interval.right_value, cr_interval.left_open, cr_interval.right_open):
                        continue 
                    if Interval.intersection(cr_interval, common_fragment.base_interval):
                        # it denotes that now |\varrho_max != Dnext |\varrho_max
                        common_fragment.cr_flag = False
                        common_fragment.common = None
                        terminate_flag = True
                        break
                    else:
                        if cr_interval.right_value <= common_fragment.base_interval.left_value:
                            if cr_interval.right_value >= common_fragment.common.left_value:
                                common_fragment.common.left_value = cr_interval.right_value
                                common_fragment.common.left_open = not cr_interval.right_open
                        elif cr_interval.left_value >= common_fragment.base_interval.right_value:
                            if cr_interval.left_value <= common_fragment.common.right_value:
                                common_fragment.common.right_value = cr_interval.left_value
                                common_fragment.common.right_open = not cr_interval.left_open
                        else:
                            print(str(cr_interval))
                            print(str(common_fragment.common))
                            raise ValueError("Error Happen")
                if terminate_flag:
                    break

            if terminate_flag:
                break

        if len(diff_delta) == 0:
            # fixpoint
            common_fragment.common.left_value = decimal.Decimal("-inf")
            common_fragment.common.left_open = True
            common_fragment.common.right_value = decimal.Decimal("+inf")
            common_fragment.common.right_open = True
            return CR.D, common_fragment.common, None, None, None, None, None, None
        delta_end = time.time()
        delta_time = delta_end - ICO_end
        print('delta time:', delta_time, "seconds")
        if common_fragment.common is None or abs(CR.min_x - common_fragment.common.left_value) <= 2 * CR.w or abs(common_fragment.common.right_value - CR.max_x) <= 2 * CR.w:
            altered_atoms = collections.defaultdict(set)
            # add the new facts to the dataset
            for tmp_predicate in delta_new:
                for tmp_entity in delta_new[tmp_predicate]:
                    altered_atoms[tmp_predicate].add(tmp_entity)
                    if tmp_predicate not in CR.D or tmp_entity not in CR.D[tmp_predicate]:
                        CR.D[tmp_predicate][tmp_entity] = CR.D[tmp_predicate][tmp_entity] + delta_new[tmp_predicate][tmp_entity]
                        # update index
                        for i, item in enumerate(tmp_entity):
                            CR.D_index[tmp_predicate][str(i) + "@" + item.name].append(tmp_entity)
                        if len(tmp_entity) > 2:
                            for i, item1 in enumerate(tmp_entity):
                                for j, item2 in enumerate(tmp_entity):
                                    if j <= i:
                                        continue
                                    CR.D_index[tmp_predicate][
                                        str(i) + "@" + item1.name + "||" + str(j) + "@" + item2.name].append(tmp_entity)
                    elif tmp_predicate in CR.D and tmp_entity in CR.D[tmp_predicate]:
                        CR.D[tmp_predicate][tmp_entity] += delta_new[tmp_predicate][tmp_entity]
            coalescing_d_altered_atoms(CR.D, altered_atoms)
            continue

        # it denotes that now |\varrho_max == Dnext |\varrho_max and \varrho_max != \emptyset and t=t_D^- \in \varrho_max,
        # so it satisfies the while conditions in line 4 and line 12
        # \varrho_max = [common_fragment.common.left_value, common_fragment.common.right_value]
        varrho_left_range = Interval(common_fragment.common.left_value, CR.min_x, common_fragment.common.left_open, False)
        varrho_right_range = Interval(CR.max_x, common_fragment.common.right_value, False, common_fragment.common.right_open)

        if varrho_left_range.left_value in [Decimal("-inf")] and varrho_right_range.right_value in [Decimal("+inf")]:
            return CR.D, common_fragment.common, None, None, None, None, None, None

        if varrho_left_range.left_value in [Decimal("-inf")]:
            varrho_right, varrho_right_dict = find_right_period(CR.D, varrho_right_range, CR)
            if varrho_right is not None:
                right_len = varrho_right.right_value - varrho_right.left_value
                for key, values in varrho_right_dict.items():
                    for value in values:
                        right_period[value].append(key)
                for key, value in right_period.items():
                    right_period[key] = coalescing(value)

                return CR.D, common_fragment.common, None, None, None, varrho_right, right_period, right_len
        else:
            varrho_left, varrho_left_dict = find_left_period(CR.D, varrho_left_range, CR)
            if varrho_left is not None:
                if varrho_right_range.right_value in [Decimal("+inf")]:
                    left_len = varrho_left.right_value - varrho_left.left_value
                    for key, values in varrho_left_dict.items():
                        for value in values:
                            left_period[value].append(key)
                    for key, value in left_period.items():
                        left_period[key] = coalescing(value)
                    return CR.D, common_fragment.common, varrho_left, left_period, left_len, None, None, None

                else:
                    varrho_right, varrho_right_dict = find_right_period(CR.D, varrho_right_range, CR)
                    if varrho_right is not None:
                        left_len = varrho_left.right_value - varrho_left.left_value
                        for key, values in varrho_left_dict.items():
                            for value in values:
                                left_period[value].append(key)
                        for key, value in left_period.items():
                            left_period[key] = coalescing(value)

                        right_len = varrho_right.right_value - varrho_right.left_value
                        for key, values in varrho_right_dict.items():
                            for value in values:
                                right_period[value].append(key)
                        for key, value in right_period.items():
                            right_period[key] = coalescing(value)
                        return CR.D, common_fragment.common, varrho_left, left_period, left_len, varrho_right, right_period, right_len
        altered_atoms = collections.defaultdict(set)
        for tmp_predicate in delta_new:
            for tmp_entity in delta_new[tmp_predicate]:
                altered_atoms[tmp_predicate].add(tmp_entity)
                if tmp_predicate not in CR.D or tmp_entity not in CR.D[tmp_predicate]:
                    CR.D[tmp_predicate][tmp_entity] = delta_new[tmp_predicate][tmp_entity]
                    # update index
                    for i, item in enumerate(tmp_entity):
                        CR.D_index[tmp_predicate][str(i) + "@" + item.name].append(tmp_entity)
                    if len(tmp_entity) > 2:
                        for i, item1 in enumerate(tmp_entity):
                            for j, item2 in enumerate(tmp_entity):
                                if j <= i:
                                    continue
                                CR.D_index[tmp_predicate][
                                    str(i) + "@" + item1.name + "||" + str(j) + "@" + item2.name].append(tmp_entity)
                elif tmp_predicate in CR.D and tmp_entity in CR.D[tmp_predicate]:
                    CR.D[tmp_predicate][tmp_entity] += delta_new[tmp_predicate][tmp_entity]

        coalescing_d_altered_atoms(CR.D, altered_atoms)

def find_periods_with_query_old_coal(CR,fact,datasetname,is_entailed):
    left_period, left_len = defaultdict(list), 0
    right_period, right_len = defaultdict(list), 0
    number_mat = 0

    # Start the timer
    start_time = time.time()
    while True:
        round_start = time.time()
        common_fragment = CommonFragment(CR.base_interval)
        common_fragment.common = Interval(Decimal("-inf"), Decimal("+inf"), True, True)
        common_fragment_end = time.time()
        common_fragment_time = common_fragment_end - round_start
        # print("common_fragment_time:",common_fragment_time, "seconds")
        if fact != None:
            if entail(fact,CR.D) == True:
                # Stop the timer
                end_time = time.time()
                execution_time = end_time - start_time
                # print("Entailment time:", execution_time, "seconds")
                # print("Entailment: True!")
                # with open(f"./{datasetname}_new_program_results_{is_entailed}/{str(fact)}_magic_new_inside.txt", 'a') as f:
                #     f.write("process_memory is(without CR):" + str(psutil.Process(os.getpid()).memory_info().rss / 1024 ** 2) + "MiB\n")
                raise Exception(execution_time)
        ICO_start = time.time()
        delta_new = naive_immediate_consequence_operator(D=CR.D, rules=CR.Program, D_index=CR.D_index)
        ICO_end = time.time()
        ICO_time = ICO_end - ICO_start
        # print("ICO time:", ICO_time, "seconds")
        number_mat += 1
        diff_delta = []
        terminate_flag = False

        for head_predicate in delta_new:
            for head_entity, T in delta_new[head_predicate].items():
                if head_predicate not in CR.D or head_entity not in CR.D[head_predicate]:
                    diff_delta = T
                else:
                    for interval1 in T:
                        diff_delta += Interval.diff(interval1, CR.D[head_predicate][head_entity])

                for cr_interval in diff_delta: 
                    if not Interval.is_valid_interval(cr_interval.left_value, cr_interval.right_value, cr_interval.left_open, cr_interval.right_open):
                        continue 
                    if Interval.intersection(cr_interval, common_fragment.base_interval):
                        # it denotes that now |\varrho_max != Dnext |\varrho_max
                        common_fragment.cr_flag = False
                        common_fragment.common = None
                        terminate_flag = True
                        break
                    else:
                        if cr_interval.right_value <= common_fragment.base_interval.left_value:
                            if cr_interval.right_value >= common_fragment.common.left_value:
                                common_fragment.common.left_value = cr_interval.right_value
                                common_fragment.common.left_open = not cr_interval.right_open
                        elif cr_interval.left_value >= common_fragment.base_interval.right_value:
                            if cr_interval.left_value <= common_fragment.common.right_value:
                                common_fragment.common.right_value = cr_interval.left_value
                                common_fragment.common.right_open = not cr_interval.left_open
                        else:
                            print(str(cr_interval))
                            print(str(common_fragment.common))
                            raise ValueError("Error Happen")
                if terminate_flag:
                    break

            if terminate_flag:
                break

        if len(diff_delta) == 0:
            # fixpoint
            common_fragment.common.left_value = decimal.Decimal("-inf")
            common_fragment.common.left_open = True
            common_fragment.common.right_value = decimal.Decimal("+inf")
            common_fragment.common.right_open = True
            return CR.D, common_fragment.common, None, None, None, None, None, None
        delta_end = time.time()
        delta_time = delta_end - ICO_end
        # print('delta time:', delta_time, "seconds")
        if common_fragment.common is None or abs(CR.min_x - common_fragment.common.left_value) <= 2 * CR.w or abs(common_fragment.common.right_value - CR.max_x) <= 2 * CR.w:
            # add the new facts to the dataset
            for tmp_predicate in delta_new:
                for tmp_entity in delta_new[tmp_predicate]:
                    if tmp_predicate not in CR.D or tmp_entity not in CR.D[tmp_predicate]:
                        CR.D[tmp_predicate][tmp_entity] = CR.D[tmp_predicate][tmp_entity] + delta_new[tmp_predicate][tmp_entity]
                        # update index
                        for i, item in enumerate(tmp_entity):
                            CR.D_index[tmp_predicate][str(i) + "@" + item.name].append(tmp_entity)
                        if len(tmp_entity) > 2:
                            for i, item1 in enumerate(tmp_entity):
                                for j, item2 in enumerate(tmp_entity):
                                    if j <= i:
                                        continue
                                    CR.D_index[tmp_predicate][
                                        str(i) + "@" + item1.name + "||" + str(j) + "@" + item2.name].append(tmp_entity)
                    elif tmp_predicate in CR.D and tmp_entity in CR.D[tmp_predicate]:
                        CR.D[tmp_predicate][tmp_entity] += delta_new[tmp_predicate][tmp_entity]
            # no_period_add_facts_end = time.time()
            # no_period_add_facts_time = no_period_add_facts_end - delta_end
            # print("no_period_add_facts_time:", no_period_add_facts_time, "seconds")
            coalescing_d(CR.D)
            # no_period_coalesce_end = time.time()
            # no_period_coalesce_time = no_period_coalesce_end - no_period_add_facts_end
            # # print("no period coalesce_time:", no_period_coalesce_time, "seconds")
            continue

        # it denotes that now |\varrho_max == Dnext |\varrho_max and \varrho_max != \emptyset and t=t_D^- \in \varrho_max,
        # so it satisfies the while conditions in line 4 and line 12
        # \varrho_max = [common_fragment.common.left_value, common_fragment.common.right_value]
        varrho_left_range = Interval(common_fragment.common.left_value, CR.min_x, common_fragment.common.left_open, False)
        varrho_right_range = Interval(CR.max_x, common_fragment.common.right_value, False, common_fragment.common.right_open)

        if varrho_left_range.left_value in [Decimal("-inf")] and varrho_right_range.right_value in [Decimal("+inf")]:
            return CR.D, common_fragment.common, None, None, None, None, None, None

        if varrho_left_range.left_value in [Decimal("-inf")]:
            varrho_right, varrho_right_dict = find_right_period(CR.D, varrho_right_range, CR)
            if varrho_right is not None:
                right_len = varrho_right.right_value - varrho_right.left_value
                for key, values in varrho_right_dict.items():
                    for value in values:
                        right_period[value].append(key)
                for key, value in right_period.items():
                    right_period[key] = coalescing(value)

                return CR.D, common_fragment.common, None, None, None, varrho_right, right_period, right_len
        else:
            varrho_left, varrho_left_dict = find_left_period(CR.D, varrho_left_range, CR)
            if varrho_left is not None:
                if varrho_right_range.right_value in [Decimal("+inf")]:
                    left_len = varrho_left.right_value - varrho_left.left_value
                    for key, values in varrho_left_dict.items():
                        for value in values:
                            left_period[value].append(key)
                    for key, value in left_period.items():
                        left_period[key] = coalescing(value)
                    return CR.D, common_fragment.common, varrho_left, left_period, left_len, None, None, None

                else:
                    varrho_right, varrho_right_dict = find_right_period(CR.D, varrho_right_range, CR)
                    if varrho_right is not None:
                        left_len = varrho_left.right_value - varrho_left.left_value
                        for key, values in varrho_left_dict.items():
                            for value in values:
                                left_period[value].append(key)
                        for key, value in left_period.items():
                            left_period[key] = coalescing(value)

                        right_len = varrho_right.right_value - varrho_right.left_value
                        for key, values in varrho_right_dict.items():
                            for value in values:
                                right_period[value].append(key)
                        for key, value in right_period.items():
                            right_period[key] = coalescing(value)
                        return CR.D, common_fragment.common, varrho_left, left_period, left_len, varrho_right, right_period, right_len
        # periods_end = time.time()
        # find_periods_time = periods_end - delta_end
        # print('find periods time:', find_periods_time, 'seconds')
        for tmp_predicate in delta_new:
            for tmp_entity in delta_new[tmp_predicate]:
                if tmp_predicate not in CR.D or tmp_entity not in CR.D[tmp_predicate]:
                    CR.D[tmp_predicate][tmp_entity] = delta_new[tmp_predicate][tmp_entity]
                    # update index
                    for i, item in enumerate(tmp_entity):
                        CR.D_index[tmp_predicate][str(i) + "@" + item.name].append(tmp_entity)
                    if len(tmp_entity) > 2:
                        for i, item1 in enumerate(tmp_entity):
                            for j, item2 in enumerate(tmp_entity):
                                if j <= i:
                                    continue
                                CR.D_index[tmp_predicate][
                                    str(i) + "@" + item1.name + "||" + str(j) + "@" + item2.name].append(tmp_entity)
                elif tmp_predicate in CR.D and tmp_entity in CR.D[tmp_predicate]:
                    CR.D[tmp_predicate][tmp_entity] += delta_new[tmp_predicate][tmp_entity]
        # delta_add_end = time.time()
        # add_delta_time = delta_add_end - periods_end
        # print('add delta time:', add_delta_time, 'seconds')
        coalescing_d(CR.D)

# def find_periods_with_query_list(CR,fact_list,init_time,datasetname):
#     left_period, left_len = defaultdict(list), 0
#     right_period, right_len = defaultdict(list), 0
#     number_mat = 0

#     # Start the timer
#     start_time = time.time()
#     entailed_fact = set()
#     while True:
#         # append the materialization round and memory usage into the path
#         print("Materialization Round: ", number_mat)
#         process = psutil.Process()
#         print(psutil.Process(os.getpid()).memory_info().rss / 1024 ** 2) # in MiB
#         # append the result to the output file
#         # with open(outputpath, 'a') as f:
#         #     f.write("Materialization Round: " + str(number_mat) + "\n")
#         #     f.write("Memory Usage: " + str(psutil.Process(os.getpid()).memory_info().rss / 1024 ** 2) + "MiB\n")

#         common_fragment = CommonFragment(CR.base_interval)
#         common_fragment.common = Interval(Decimal("-inf"), Decimal("+inf"), True, True)

#         for fact in fact_list:
#             if entail(fact,CR.D) == True and fact not in entailed_fact:
#                 # Stop the timer
#                 end_time = time.time()
#                 execution_time = end_time - start_time + init_time
#                 #append the result to the output file
#                 with open(f"./{datasetname}_baseline_results/"+ str(fact) +"_inside.txt", 'a') as f:
#                     f.write("total_time is(without CR):" + str(execution_time))
#                     f.write("\nprocess_memory is(without CR):" + str(psutil.Process(os.getpid()).memory_info().rss / 1024 ** 2) + "MiB\n")
#                     #delete the fact from the list
#                 entailed_fact.add(fact)

#         delta_new = naive_immediate_consequence_operator(D=CR.D, rules=CR.Program, D_index=CR.D_index)
#         number_mat += 1
#         diff_delta = []
#         terminate_flag = False
#         for head_predicate in delta_new:
#             for head_entity, T in delta_new[head_predicate].items():
#                 if head_predicate not in CR.D or head_entity not in CR.D[head_predicate]:
#                     diff_delta = T
#                 else:
#                     for interval1 in T:
#                         diff_delta += Interval.diff(interval1, CR.D[head_predicate][head_entity])

#                 for cr_interval in diff_delta: 
#                     if not Interval.is_valid_interval(cr_interval.left_value, cr_interval.right_value, cr_interval.left_open, cr_interval.right_open):
#                         continue 
#                     if Interval.intersection(cr_interval, common_fragment.base_interval):
#                         # it denotes that now |\varrho_max != Dnext |\varrho_max
#                         common_fragment.cr_flag = False
#                         common_fragment.common = None
#                         terminate_flag = True
#                         break
#                     else:
#                         if cr_interval.right_value <= common_fragment.base_interval.left_value:
#                             if cr_interval.right_value >= common_fragment.common.left_value:
#                                 common_fragment.common.left_value = cr_interval.right_value
#                                 common_fragment.common.left_open = not cr_interval.right_open
#                         elif cr_interval.left_value >= common_fragment.base_interval.right_value:
#                             if cr_interval.left_value <= common_fragment.common.right_value:
#                                 common_fragment.common.right_value = cr_interval.left_value
#                                 common_fragment.common.right_open = not cr_interval.left_open
#                         else:
#                             print(str(cr_interval))
#                             print(str(common_fragment.common))
#                             raise ValueError("Error Happen")
#                 if terminate_flag:
#                     break

#             if terminate_flag:
#                 break

#         if len(diff_delta) == 0:
#             # fixpoint
#             common_fragment.common.left_value = decimal.Decimal("-inf")
#             common_fragment.common.left_open = True
#             common_fragment.common.right_value = decimal.Decimal("+inf")
#             common_fragment.common.right_open = True
#             return CR.D, common_fragment.common, None, None, None, None, None, None

#         if common_fragment.common is None or abs(CR.min_x - common_fragment.common.left_value) <= 2 * CR.w or abs(common_fragment.common.right_value - CR.max_x) <= 2 * CR.w:
#             # add the new facts to the dataset
#             for tmp_predicate in delta_new:
#                 for tmp_entity in delta_new[tmp_predicate]:
#                     if tmp_predicate not in CR.D or tmp_entity not in CR.D[tmp_predicate]:
#                         CR.D[tmp_predicate][tmp_entity] = CR.D[tmp_predicate][tmp_entity] + delta_new[tmp_predicate][tmp_entity]
#                         # update index
#                         for i, item in enumerate(tmp_entity):
#                             CR.D_index[tmp_predicate][str(i) + "@" + item.name].append(tmp_entity)
#                         if len(tmp_entity) > 2:
#                             for i, item1 in enumerate(tmp_entity):
#                                 for j, item2 in enumerate(tmp_entity):
#                                     if j <= i:
#                                         continue
#                                     CR.D_index[tmp_predicate][
#                                         str(i) + "@" + item1.name + "||" + str(j) + "@" + item2.name].append(tmp_entity)
#                     elif tmp_predicate in CR.D and tmp_entity in CR.D[tmp_predicate]:
#                         CR.D[tmp_predicate][tmp_entity] += delta_new[tmp_predicate][tmp_entity]
#             coalescing_d(CR.D)
#             continue

#         # it denotes that now |\varrho_max == Dnext |\varrho_max and \varrho_max != \emptyset and t=t_D^- \in \varrho_max,
#         # so it satisfies the while conditions in line 4 and line 12
#         # \varrho_max = [common_fragment.common.left_value, common_fragment.common.right_value]
#         varrho_left_range = Interval(common_fragment.common.left_value, CR.min_x, common_fragment.common.left_open, False)
#         varrho_right_range = Interval(CR.max_x, common_fragment.common.right_value, False, common_fragment.common.right_open)

#         if varrho_left_range.left_value in [Decimal("-inf")] and varrho_right_range.right_value in [Decimal("+inf")]:
#             return CR.D, common_fragment.common, None, None, None, None, None, None

#         if varrho_left_range.left_value in [Decimal("-inf")]:
#             varrho_right, varrho_right_dict = find_right_period(CR.D, varrho_right_range, CR)
#             if varrho_right is not None:
#                 right_len = varrho_right.right_value - varrho_right.left_value
#                 for key, values in varrho_right_dict.items():
#                     for value in values:
#                         right_period[value].append(key)
#                 for key, value in right_period.items():
#                     right_period[key] = coalescing(value)

#                 return CR.D, common_fragment.common, None, None, None, varrho_right, right_period, right_len
#         else:
#             varrho_left, varrho_left_dict = find_left_period(CR.D, varrho_left_range, CR)
#             if varrho_left is not None:
#                 if varrho_right_range.right_value in [Decimal("+inf")]:
#                     left_len = varrho_left.right_value - varrho_left.left_value
#                     for key, values in varrho_left_dict.items():
#                         for value in values:
#                             left_period[value].append(key)
#                     for key, value in left_period.items():
#                         left_period[key] = coalescing(value)
#                     return CR.D, common_fragment.common, varrho_left, left_period, left_len, None, None, None

#                 else:
#                     varrho_right, varrho_right_dict = find_right_period(CR.D, varrho_right_range, CR)
#                     if varrho_right is not None:
#                         left_len = varrho_left.right_value - varrho_left.left_value
#                         for key, values in varrho_left_dict.items():
#                             for value in values:
#                                 left_period[value].append(key)
#                         for key, value in left_period.items():
#                             left_period[key] = coalescing(value)

#                         right_len = varrho_right.right_value - varrho_right.left_value
#                         for key, values in varrho_right_dict.items():
#                             for value in values:
#                                 right_period[value].append(key)
#                         for key, value in right_period.items():
#                             right_period[key] = coalescing(value)
#                         return CR.D, common_fragment.common, varrho_left, left_period, left_len, varrho_right, right_period, right_len

#         for tmp_predicate in delta_new:
#             for tmp_entity in delta_new[tmp_predicate]:
#                 if tmp_predicate not in CR.D or tmp_entity not in CR.D[tmp_predicate]:
#                     CR.D[tmp_predicate][tmp_entity] = delta_new[tmp_predicate][tmp_entity]
#                     # update index
#                     for i, item in enumerate(tmp_entity):
#                         CR.D_index[tmp_predicate][str(i) + "@" + item.name].append(tmp_entity)
#                     if len(tmp_entity) > 2:
#                         for i, item1 in enumerate(tmp_entity):
#                             for j, item2 in enumerate(tmp_entity):
#                                 if j <= i:
#                                     continue
#                                 CR.D_index[tmp_predicate][
#                                     str(i) + "@" + item1.name + "||" + str(j) + "@" + item2.name].append(tmp_entity)
#                 elif tmp_predicate in CR.D and tmp_entity in CR.D[tmp_predicate]:
#                     CR.D[tmp_predicate][tmp_entity] += delta_new[tmp_predicate][tmp_entity]

#         coalescing_d(CR.D)


def fact_entailment(D, fact, base_interval, left_period, left_len, right_period, right_len):
    if fact.predicate not in D:
        return False
    else:
        if not fact.entity in D[fact.predicate]:
            return False
        else:
            intervals = D[fact.predicate][fact.entity]
            for interval in intervals:
                if Interval.inclusion(fact.interval, interval):
                    return True
            else:
                if Interval.inclusion(fact.interval, base_interval):
                    return False
                # using the canonical representation to do the checking
                elif fact.interval.left_value < base_interval.left_value and not left_period:
                    # less than the base interval and the left_period is empty
                    return False
                elif fact.interval.right_value > base_interval.right_value and not right_period:
                    # greater than the base interval and the right_period is empty
                    return False
                else:
                    target_interval = fact.interval
                    if target_interval.left_value >= base_interval.left_value:
                        if not right_period:
                            return False
                        last_interval = D[fact.predicate][fact.entity][-1]
                        remain_interval = Interval.diff(target_interval, [last_interval])
                        if len(remain_interval) != 1:
                            return False

                        else:
                            remain_interval = remain_interval[0]
                            repeated_intervals = right_period[str(Atom(fact.predicate, fact.entity))]
                            for interval in repeated_intervals:
                                if interval.right_value - interval.left_value == right_len:
                                    #infinity range
                                    return True
                                else:
                                    new_interval = Interval(interval.left_value + right_len * math.ceil((target_interval.right_value-interval.right_value)/right_len),
                                                            interval.right_value + right_len * math.ceil((target_interval.right_value-interval.right_value)/right_len),
                                                            interval.left_open, interval.right_open)
                                    if Interval.inclusion(remain_interval, new_interval):
                                        return True
                            return False

                    elif target_interval.right_value <= base_interval.right_value:
                        if not left_period:
                            return False
                        last_interval = D[fact.predicate][fact.entity][0]
                        remain_interval = Interval.diff(target_interval, [last_interval])
                        if len(remain_interval) != 1:
                            return False

                        else:
                            remain_interval = remain_interval[0]
                            repeated_intervals = left_period[str(Atom(fact.predicate, fact.entity))]
                            for interval in repeated_intervals:
                                if interval.right_value - interval.left_value == right_len:
                                    # infinity range
                                    return True
                                else:
                                    new_interval = Interval(
                                        interval.left_value - left_len * math.ceil(abs(target_interval.right_value-interval.left_value) / left_len),
                                        interval.right_value - left_len * math.ceil(abs(target_interval.right_value-interval.left_value) / left_len),
                                        interval.left_open, interval.right_open)
                                    if Interval.inclusion(remain_interval, new_interval):
                                        return True
                            return False
                    else:
                        if not left_period or not right_period:
                            return False

                        remain_interval = Interval.diff(target_interval, [D[fact.predicate][fact.entity][0]])
                        if len(remain_interval) != 1:
                            return False
                        remain_interval = remain_interval[0]
                        repeated_intervals = left_period[str(Atom(fact.predicate, fact.entity))]
                        for interval in repeated_intervals:
                            if interval.right_value - interval.left_value == right_len:
                                # infinity range
                               break
                            else:
                                new_interval = Interval(
                                    interval.left_value - left_len * math.ceil(abs(target_interval.left_value-interval.left_value) / left_len),
                                    interval.right_value - left_len * math.ceil(abs(target_interval.left_value-interval.left_value) / left_len),
                                    interval.left_open, interval.right_open)
                                if Interval.inclusion(remain_interval, new_interval):
                                    break
                        else:
                            return False

                        remain_interval = Interval.diff(target_interval, [D[fact.predicate][fact.entity][-1]])
                        if len(remain_interval) != 1:
                            return False

                        remain_interval = remain_interval[0]
                        repeated_intervals = right_period[str(fact.atom)]
                        for interval in repeated_intervals:
                            if interval.right_value - interval.left_value == right_len:
                                # infinity range
                                return True
                            else:
                                new_interval = Interval(
                                    interval.left_value + right_len * math.ceil((target_interval.right_value - interval.right_value) / right_len),
                                    interval.right_value + right_len * math.ceil((target_interval.right_value - interval.right_value) / right_len),
                                    interval.left_open, interval.right_open)
                                if Interval.inclusion(remain_interval, new_interval):
                                    return True
                        else:
                            return False





