#include <magic.h>
#include <loader.h>
#include <iostream>
#include <parser.h>
#include <fstream>
#include <string>
#include <chrono>
#include <filesystem>

int main()
{
	std::string line;
	std::string query_string;
	std::vector<std::string> rules_string;

	bool readingQuery = false;
	bool readingRules = false;

	while (std::getline(cin, line))
	{
		// if read Input END! Then break
		if (line.find("Input END!") != std::string::npos)
		{
			break;
		}
		if (line.find("query:") != std::string::npos)
		{
			readingQuery = true;
			readingRules = false;
			continue;
		}
		if (line.find("rules:") != std::string::npos)
		{
			readingQuery = false;
			readingRules = true;
			continue;
		}
		if (readingQuery)
		{
			query_string = line;
		}
		else if (readingRules)
		{
			rules_string.push_back(line);
		}
	}

	// use magic set method
	MagicSet magicSet;
	// in this premature version, we only parse the head of the rule as the query, note that the body is empty and we need :- to separate the head and the body
	vector<string> querys; // input query
	vector<Rule> queryList;
	vector<string> rules; // input rules
	vector<Rule> ruleList;

	// Example from input file
	querys.push_back(query_string); // input query here
	for (const auto &rule : rules_string)
	{
		rules.push_back(rule); // input rules here
	}

	queryList = load_program(querys); // parse the query string
	ruleList = load_program(rules);	  // parse the rule string

	Literal query;
	query = queryList[0].head;								// get the query

	//start magic set timer
	auto start = std::chrono::high_resolution_clock::now();

	vector<Rule> magicRules = magicSet.MS(query, ruleList); // get the magic rules

	//end magic set timer
	auto end = std::chrono::high_resolution_clock::now();
	std::chrono::duration<double> elapsed_seconds = end - start;
	std::cout << "Time to get magic set:\n" << elapsed_seconds.count() << "\n";

	return 0;
}
