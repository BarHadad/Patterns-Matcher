# Patterns-Matcher-Tool

Python tool that can find matching patterns in binary files.
In addition to the tool default search algorithm (which supports regular expressions matching), the tool also supports a very efficient pattern matching algorithm - "[Aho Corasick algorithm]". Notice that in contrast to the default algorithm of this tool, this algorithm doesn’t support regular expressions matching, and to activate this algorithm you'll have to download the "ahocorasick" package and uncomment the import to ahocorasick package.

### How to use the tool:

The tool should get 4 mandatory inputs and 1 optional:
- Output File Name - the name of the output JSON file.
- Path to binary file - path to the binary file the tool should search in.
- Path to JSON file which holds the patterns as a dictionary (keys = hex strings patterns or regular expressions). Given example in the project files named "dictionary. JSON".
- Threshold Number: if you want the tool to search for repeating bytes with a threshold (= this Number) insert some non-negative natural number. If not -> insert -1.
- true (optional) - sign the tool to run Aho Corasick algorithm, as mentioned above - this algorithm doesn’t support regular expressions matching, but only regular hex - string matching.

### Output:
Finally,  the tool prints the number of seconds it runs and generates a JSON format file,  that contains all the matching patterns and repeating bytes (if asked for).

[Aho Corasick algorithm] = <https://en.wikipedia.org/wiki/Aho%E2%80%93Corasick_algorithm>

### Usage:
* Finding offsets of paddings in a binary file.
* Finding offsets of zip archives in a binary file.
* Finding magic numbers to identify or verify the content of a file.

