# DatalogMTL-MagicSet-Transformer

This is the source code of our magic sets transformation implementation in C++.

## Source Code Usage

Follow the steps below to basically use the source code, for further details, please refer to main.cpp

```cpp
MagicSet magicSet;                                          // use magic set method
Literal query;                                              // get the query
vector<Rule> ruleList;                                      // get the rules
vector<Rule> magicRules = magicSet.MS(query, ruleList);     // get the magic rules
```

## Run

0. cd DatalogMTL-MagicSet-Transformer

1. make

2. ./DMT

3. Notice that the input is from the console and there is no reminder for the input, so you can paste the input directly ( remember to end the query string with ":-" string and end input with "Input END!" string )

```bash
query:
g4863(n0,n1):-
rules:
g4859(N0,N1) :- Boxplus[0,10000] g4868(N1,N0)
g4860(N0,N1) :- g4861(N1,N0)
g4862(N0,N1) :- Diamondplus[0,10000] g4869(N1,N0)
g4863(N0,N1) :- g4857(N1,N0)
g4863(N0,N1) :- g4866(N0,N1)
g4864(N0,N1) :- g4854(N0), g4856(N1), g4857(N1,N2)
g4866(N0,N1) :- g4862(N1,N0), g4863(N0,N1)
g4867(N0,N1) :- g4858(N1,N0)
g4867(N0,N1) :- g4863(N0,N1)
g4869(N0,N1) :- g4855(N1,N0), g4864(N0,N1)
g4901(N0,N1) :- Diamondminus[1000,10000] g4867(N1,N0)
Input END!
```

4. get the output in the console

### Notice

Does not support "make clean" command, if you want to clean the project, you can delete the files directly.
