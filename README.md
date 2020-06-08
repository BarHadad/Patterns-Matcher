# Patterns-Matcher
Python tool that can find matching patterns in binary files.
The tool also supports a very efficient pattern matching algorithm - "Aho Corasick algorithm". Notice that in contrast to the second algorithm of this tool, this algorithm doesn’t support regular expressions matching, and in order to activate this algorithm you'll have to download the "ahocorasick" package.

How to use the tool:

the tool should get 4 mandatory inputs and 1 optional:
1: Output File Name - the name of the output JSON file.
2: Path to binary file - path to the binary file the tool should search in.
3: Path to JSON file which holds the patterns as a dictionary (keys = hex strings patterns or regular expressions). Given example in the project files named "dictionary. JSON".
4: Threshold Number: if you want the tool to search for repeating bytes with a threshold (= this Number) insert some non-negative natural number. If not - insert -1.
5: true - sign the tool to run aho corasick algorithm, as mentioned above - this algorithm doesn’t support regular expressions matching, but only regular hex - string matching
