from meteor_reasoner.materialization.coalesce import *
from meteor_reasoner.materialization.index_build import *
from meteor_reasoner.utils.loader import *
import subprocess

def produce_magic_pair(program, dataset, query):
    query_string = str(query)
    fact = parse_str_fact(query_string)
    magic_prediacte = "magic_" + fact[0] + "_" + "b" * len(fact[1])
    magic_interval = Interval(decimal.Decimal("-inf"), decimal.Decimal("+inf"),True,True)

    # add magic fact into D
    dataset[magic_prediacte][tuple(fact[1])].append(magic_interval)

    # construct a temporary term list which contains char 'a' whose nubmer is equal to the number of fact[1]
    temp_term_list = [Term('a') for i in range(len(fact[1]))]
    # construct a new fact with the same predicate and the temporary term list
    fact_lowercase = Atom(fact[0], temp_term_list, fact[2])
    fact_lowercase_string = str(fact_lowercase)
    fact_lowercase_string = fact_lowercase_string.split('@')[0]

    # construct the input data for the executable file
    input_data = "query:\n" + fact_lowercase_string + ':-\n' + "rules:\n"
    for rule in program:
        rule_str = rule.__str__()
        input_data += rule_str + '\n'
    input_data += "Input END!\n"

    # execute
    process = subprocess.Popen(
        ['./DMT'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    # communicate
    stdout, stderr = process.communicate(input=input_data)

    magic_program = []
    magic_program_lines = extract_magic_program(stdout)
    for line in magic_program_lines:
        rule = parse_rule(line)
        magic_program.append(rule)
    
    magic_program_time = extract_magic_program_time(stdout)

    return magic_program, dataset, magic_program_time

def extract_magic_program(stdout):
    lines = stdout.splitlines()
    
    index = lines.index('Magic Program: ')

    magic_program_lines = lines[index + 1:-2] 
    
    return magic_program_lines

def extract_magic_program_time(stdout):
    lines = stdout.splitlines()
    
    index = lines.index('Time to get magic set:')

    magic_program_time = lines[index + 1:] 
    
    return magic_program_time[0]

if __name__ == "__main__":
    datapath = f"./data/lubm_10^2.txt"
    rulepath = f"./programs/p.txt"

    # Load the dataset
    dataset = load_dataset(datapath)
    # Load the rules
    program = load_program(rulepath)
    # Load the query
    query_string = "AssistantProfessorCandidate(ID0)@18"
    fact = parse_str_fact(query_string)
    query = Atom(fact[0], fact[1], fact[2])
    # Produce the magic pair
    magic_program,dataset,magic_program_time=produce_magic_pair(program, dataset, query)

    print("Magic Program:")
    for rule in magic_program:
        print(rule)

    print(magic_program_time)