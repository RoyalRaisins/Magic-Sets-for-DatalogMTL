## Introduction

We implemented our algorithm1 and evaluated it on LUBM<sub>t</sub>(Wang et al. 2022), a temporal version of LUBM (Guo,Pan, and Heflin 2005), on iTemporal (Bellomarini, Nissl,and Sallinger 2022), and on the meteorological (Wang et al. 2022) benchmarks using MeTeoR (Wałe¸ga et al. 2023) to see how the magic programs fare against the original programs in terms of query answering. The three test programs have 85, 11, and 4 rules, respectively.

This repository contains 11 datasets (5 for iTemporal 10^1 to 10^5, 5 for LUBM<sub>t</sub> 10^2 to 10^6, 1 for the meteorological benchmark) and 3 programs, the source code of our magic sets transformation implementation, the adapted MeTeoR DatalogMTL reasoner, and the source code for running our experiments. Due to Github's file size limit, we provided a subset of the dataset we used for the meteorological benchmark, which is stored in MagicMTL/weather/weather_data/weather_dataset.txt. The full dataset is stored in  MagicMTL/weather/weather_data/weather_dataset.zip and 6 compressed volumes. You can unzip the compressed volumes and derive another file named weather_dataset.txt but containing the full dataset. Use this file to replace the file containing a subset if you wish to run the experiments on the full dataset. 
## Structure

The structure of the repository is as follows (some folders are initially empty):

```
MagicMTL/
├── datasetname/
│   ├── datasetname_data/
│   ├── datasetname_programs/
│   |   ├── magic_programs/
|   |   └── program.txt
│   ├── query_results/
|   ├── datasetname_baseline_results/                 (initially empty)
│   ├── datasetname_new_program_results_entailed/     (initially empty)
│   ├── datasetname_new_program_results_not_entailed/ (initially empty)
│   ├── scalability_results/                          (initially empty)
│   ├── DMT
│   ├── produce_magic_pair.py
│   ├── datasetname_baseline.py
│   ├── datasetname_magic_fixed_query_entailed.py
│   ├── datasetname_magic_fixed_query_not_entailed.py
│   └── datasetname_scalability.py
├── MeTeoR_magic/
├── DatalogMTL-MagicSet-Transformer/
├── README.md
└── requirements.txt
```

**DMT** and **produce_magic_pair.py** are the executable file (DatalogMTL-MagicSet-Transformer) and source code used to generate the magic program-dataset pair, used across all experiments.

**DatalogMTL-MagicSet-Transformer/** contains the source code of our magic sets transformation implementation in C++.

**magic_programs/** contains the magic programs for different queres in each program, generated by our C++ implementation. Note that given an input pair, facts with the same predicate always generate the same magic program.

**query_results/** contains summaries of some of the entailed facts of the original pairs.

**MeTeoR_magic/** is the source code of the MeTeoR DatalogMTL reasoner we adapted and used in the experiments.

---

### Folders for **Experiment 1:** Comparison With Baseline Programs.

**datasetname/datasetname_baseline_results/** contains the output of **datasetname_baseline.py**.

**datasetname/datasetname_new_program_results_entailed/** contains the output of **datasetname_magic_fixed_query_entailed.py**.

**datasetname/datasetname_new_program_results_not_entailed/** contains the output of **datasetname_magic_fixed_query_not_entailed.py**.

---

### The Folder for **Experiment 2:** Scalability Experiments.

**datasetname/scalability_results/** contains the output of **datasetname_scalability.py**, "datasetname_statistics.xlsx" contains the statistics of the scalability experiments.

## Setup

Our setup uses conda to manage the environment.

Example OS version: Fedora Linux 40

This is a set of bash commands to set up experiment environment.

```bash
git clone https://github.com/RoyalRaisins/MagicMTL.git
cd MagicMTL/
conda create -n MagicSet python=3.7
conda activate MagicSet
pip install -r requirements.txt
chmod +x ./weather/DMT ./iTemporal/DMT ./lubm/DMT
cd ./MeTeoR_magic
pip install -e .
cd ..
```

## Run Experiments

### LUBM

Follow the steps below to reproduce the results of our experiments on the LUBM benchmark, and the results will be saved in the corresponding folders and printed to the console:

```bash
cd ./lubm

# Experiment 1: Comparison With Baseline Programs.
# Run the entailed queries with the baseline program
python lubm_baseline.py
# Run the entailed queries with magic programs
python lubm_magic_fixed_query_entailed.py
# Run the not entailed queries with magic programs
python lubm_magic_fixed_query_not_entailed.py

# Experiment 2: Scalability Experiments.
python lubm_scalability.py
cd ..
```

### iTemporal

Follow the steps below to reproduce the results of our experiment on the iTemporal benchmark, and the results will be saved in the corresponding folders and printed to the console:

```bash
cd ./iTemporal

# Experiment 1: Comparison With Baseline Programs.
# Run the entailed queries with the baseline program
python iTemporal_baseline.py
# Run the entailed queries with magic programs
python iTemporal_magic_fixed_query_entailed.py
# Run the not entailed queries with magic programs
python iTemporal_magic_fixed_query_not_entailed.py

# Experiment 2: Scalability Experiments.
python iTemporal_scalability.py
cd ..
```

### Weather

Due to file size limit of Github, we included a smaller meteorological dataset as an example. Follow the steps below to run experiment queries on the example dataset, and the results will be saved in the corresponding folders and printed to the console:

```bash
cd ./weather

# Experiment 1: Comparison With Baseline Programs.
# Run the entailed queries with the baseline program
python weather_baseline.py
# Run the entailed queries with magic programs
python weather_magic_fixed_query_entailed.py
# Run the not entailed queries with magic programs
python weather_magic_fixed_query_not_entailed.py
cd ..
```

#### Notice

To run an experiment process with a high priority and only one kernel to avoid context switching, we can use the following command:

```bash
# Example
sudo taskset -c 0 nice -n -20 python lubm_baseline.py
```
