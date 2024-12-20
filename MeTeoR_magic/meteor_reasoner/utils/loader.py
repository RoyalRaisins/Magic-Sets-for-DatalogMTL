from meteor_reasoner.utils.parser import *
from collections import defaultdict
import time, os, datetime
import csv, json 

def load_dataset(file_or_path):
    """
    Read string-like facts into a dictionary object.

    Args:
        lines (list of strings): a list of facts in the form of  A(x,y,z)@[1,2] or A@[1,2)

    Returns:
        A defaultdict object, in which the key is the predicate and the value is a dictionary (key is
        the entity and the value is a list of Interval instances) or a list of Interval instance when
        there is no entity.

    """
    lines = []
    D = defaultdict(lambda: defaultdict(list))
    if isinstance(file_or_path, list):
        lines = file_or_path[:]

    elif os.path.isdir(file_or_path):
        # It is a folder contains a set of {predicate}.csv files
        base_path = file_or_path
        for filepath in os.listdir(base_path):
            if len(filepath.split("_")) == 3:
                predicate = filepath.split("_")[1]
            else:
                predicate = filepath.split(".")[0]
            with open(os.path.join(base_path, filepath)) as file:
                reader = csv.reader(file)
                next(reader, None)
                for item in reader:
                    left_timepoint, right_timepoint = item[-2], item[-1]
                    interval = Interval(decimal.Decimal(left_timepoint), decimal.Decimal(right_timepoint), False, False)
                    # for the timestamp
                    # try:
                    #     left_timepoint = time.mktime(
                    #         datetime.datetime.strptime(left_timepoint, "%Y-%m-%d %H:%M:%S").timetuple())
                    #     right_timepoint = time.mktime(
                    #         datetime.datetime.strptime(right_timepoint, "%Y-%m-%d %H:%M:%S").timetuple())
                    #     interval = Interval(int(left_timepoint), int(right_timepoint), False, False)
                    # except:
                    #     interval = Interval(int(left_timepoint), int(right_timepoint), False, False)

                    if len(item) == 2:  # propositional
                        entity = tuple([Term("nan")])
                    else:
                        entity = tuple([Term(const) for const in item[:-2]])
                    D[predicate][entity].append(interval)
        return D

    elif isinstance(file_or_path, str) and file_or_path.endswith("csv"):
        # it is a csv file with the first column representing the predicate and the last two columns
        # representing the interval and the middle columns denotes the constants
        with open(os.path.join(file_or_path)) as file:
            reader = csv.reader(file)
            next(reader, None)
            for item in reader:
                predicate = item[0]
                left_timepoint, right_timepoint = item[-2], item[-1]
                try:
                    left_timepoint = time.mktime(
                        datetime.datetime.strptime(left_timepoint, "%Y-%m-%d %H:%M:%S").timetuple())
                    right_timepoint = time.mktime(
                        datetime.datetime.strptime(right_timepoint, "%Y-%m-%d %H:%M:%S").timetuple())
                except ValueError:
                    left_timepoint, right_timepoint = item[-2], item[-1]
                interval = Interval(int(left_timepoint), int(right_timepoint), False, False)
                if len(item) == 2:  # propositional
                    entity = tuple([Term("nan")])
                else:
                    entity = tuple([Term(const) for const in item[1:-2]])
                D[predicate][entity].append(interval)
        return D
     

    elif isinstance(file_or_path, str) and file_or_path.endswith("json"):
        print("The input data format is json!")
        with open(file_or_path) as file:
             json_data = json.load(file)
             for key, values in json_data.items(): #values is a list
                predicate = key
                for fact in values: 
                    # if no entity, please use "nan" as the entity_str
                    for entity_str, intervals in fact.items():
                        entity = tuple([Term(const) for const in entity_str.split(",")])
                        intv = Interval(Decimal(intervals["left_value"]), Decimal(intervals["right_value"]), intervals["left_open"], intervals["right_open"])
                        D[predicate][entity].append(intv)
        return D
    
    elif isinstance(file_or_path, str) and not file_or_path.endswith("csv"):
        with open(os.path.join(file_or_path)) as file:
            for line in file:
                lines.append(line)

    else:
        raise ValueError('The input should be a file path or a list of rule string')

    for line in lines:
        line = line.strip().replace(" ","")
        if line == "":
            continue
        try:
          predicate, entity, interval = parse_str_fact(line)

        except:
            continue
        if predicate not in D:
            if entity:
               D[predicate][entity] = [interval]
            else:
               D[predicate] = [interval]
        else:
            if isinstance(D[predicate], list) and entity is not None:
                raise ValueError("One predicate can not have both entity and Null cases!")

            if not isinstance(D[predicate], list) and entity is None:
                raise ValueError("One predicate can not have both entity and Null cases!")

            if entity:
                if entity in D[predicate]:
                    D[predicate][entity].append(interval)
                else:
                    D[predicate][entity] = [interval]
            else:
                D[predicate].append(interval)


    return D


def load_dataset_for_program(file_or_path, program):
    """
    Read string-like facts into a dictionary object.

    Args:
        lines (list of strings): a list of facts in the form of  A(x,y,z)@[1,2] or A@[1,2)
        program: a program produced by load_program()

    Returns:
        A defaultdict object, in which the key is the predicate and the value is a dictionary (key is
        the entity and the value is a list of Interval instances) or a list of Interval instance when
        there is no entity.

    """
    predicates = get_predicates(program)
    lines = []
    D = defaultdict(lambda: defaultdict(list))
    if isinstance(file_or_path, list):
        lines = file_or_path[:]

    elif os.path.isdir(file_or_path):
        # It is a folder contains a set of {predicate}.csv files
        base_path = file_or_path
        for filepath in os.listdir(base_path):
            if len(filepath.split("_")) == 3:
                predicate = filepath.split("_")[1]
            else:
                predicate = filepath.split(".")[0]
            if(predicate not in predicates):
                continue
            with open(os.path.join(base_path, filepath)) as file:
                reader = csv.reader(file)
                next(reader, None)
                for item in reader:
                    left_timepoint, right_timepoint = item[-2], item[-1]
                    interval = Interval(decimal.Decimal(left_timepoint), decimal.Decimal(right_timepoint), False, False)
                    # for the timestamp
                    # try:
                    #     left_timepoint = time.mktime(
                    #         datetime.datetime.strptime(left_timepoint, "%Y-%m-%d %H:%M:%S").timetuple())
                    #     right_timepoint = time.mktime(
                    #         datetime.datetime.strptime(right_timepoint, "%Y-%m-%d %H:%M:%S").timetuple())
                    #     interval = Interval(int(left_timepoint), int(right_timepoint), False, False)
                    # except:
                    #     interval = Interval(int(left_timepoint), int(right_timepoint), False, False)

                    if len(item) == 2:  # propositional
                        entity = tuple([Term("nan")])
                    else:
                        entity = tuple([Term(const) for const in item[:-2]])
                    D[predicate][entity].append(interval)
        return D

    elif isinstance(file_or_path, str) and file_or_path.endswith("csv"):
        # it is a csv file with the first column representing the predicate and the last two columns
        # representing the interval and the middle columns denotes the constants
        with open(os.path.join(file_or_path)) as file:
            reader = csv.reader(file)
            next(reader, None)
            for item in reader:
                predicate = item[0]
                if predicate not in predicates:
                    continue
                left_timepoint, right_timepoint = item[-2], item[-1]
                try:
                    left_timepoint = time.mktime(
                        datetime.datetime.strptime(left_timepoint, "%Y-%m-%d %H:%M:%S").timetuple())
                    right_timepoint = time.mktime(
                        datetime.datetime.strptime(right_timepoint, "%Y-%m-%d %H:%M:%S").timetuple())
                except ValueError:
                    left_timepoint, right_timepoint = item[-2], item[-1]
                interval = Interval(int(left_timepoint), int(right_timepoint), False, False)
                if len(item) == 2:  # propositional
                    entity = tuple([Term("nan")])
                else:
                    entity = tuple([Term(const) for const in item[1:-2]])
                D[predicate][entity].append(interval)
        return D


    elif isinstance(file_or_path, str) and file_or_path.endswith("json"):
        print("The input data format is json!")
        with open(file_or_path) as file:
            json_data = json.load(file)
            for key, values in json_data.items():  # values is a list
                predicate = key
                for fact in values:
                    # if no entity, please use "nan" as the entity_str
                    for entity_str, intervals in fact.items():
                        entity = tuple([Term(const) for const in entity_str.split(",")])
                        intv = Interval(Decimal(intervals["left_value"]), Decimal(intervals["right_value"]),
                                        intervals["left_open"], intervals["right_open"])
                        D[predicate][entity].append(intv)
        return D

    elif isinstance(file_or_path, str) and not file_or_path.endswith("csv"):
        with open(os.path.join(file_or_path)) as file:
            for line in file:
                lines.append(line)

    else:
        raise ValueError('The input should be a file path or a list of rule string')

    for line in lines:
        line = line.strip().replace(" ", "")
        if line == "":
            continue
        try:
            predicate, entity, interval = parse_str_fact(line)

        except:
            continue

        if predicate not in predicates:
            continue
        
        if predicate not in D:
            if entity:
                D[predicate][entity] = [interval]
            else:
                D[predicate] = [interval]
        else:
            if isinstance(D[predicate], list) and entity is not None:
                raise ValueError("One predicate can not have both entity and Null cases!")

            if not isinstance(D[predicate], list) and entity is None:
                raise ValueError("One predicate can not have both entity and Null cases!")

            if entity:
                if entity in D[predicate]:
                    D[predicate][entity].append(interval)
                else:
                    D[predicate][entity] = [interval]
            else:
                D[predicate].append(interval)

    return D

def load_program(file_or_path):
    """
    Format each string-like rule into a rule instance.

    Args:
        rules (list of strings): each string represents a rule, e.g. A(X):- Boxminus[1,2]B(X)

    Returns:
        list of rule instances
    """
    rules = []
    if isinstance(file_or_path, str):
        # it is a file path
        with open(file_or_path) as file:
            for line in file:
                line = line.replace("[-]", "Boxminus")
                line = line.replace("<+>", "Diamondplus")
                line = line.replace("<->", "Diamondminus")
                line = line.replace("[+]", "Boxplus")
                line = line.replace(" ", "")
                line = line.replace(".", "")
                rules.append(line)
    elif isinstance(file_or_path, list):
        rules = file_or_path[:]

    else:
        raise ValueError('The input should be a file path or a list of rule string')

    program = []
    for line in rules:
        rule = parse_rule(line)
        program.append(rule)

    return program

def get_predicates(program):
    predicates = set()
    for rule in program:
        predicates.add(rule.head.get_predicate())
        for literal in rule.body:
            if isinstance(literal, BinaryLiteral):
                predicates.add(literal.left_literal.get_predicate())
                predicates.add(literal.right_literal.get_predicate())
            else:
                predicates.add(literal.get_predicate())
    return predicates