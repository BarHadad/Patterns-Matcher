import time
import sys
import json
# import ahocorasick
import re

BUFFER_SIZE = 4096


def main(output_file_name, binary_file_path, dict_file_path, rb_flag=-1, aho_corasick=False):
    expressions_dict = build_and_assert_dictionary_correctness(dict_file_path)
    with open(binary_file_path, "rb") as binary_file:  # Open binary file
        result = find_matching_patterns(expressions_dict, binary_file, aho_corasick, rb_flag)
        sort_result_dictionary_by_key(rb_flag, result)
        convert_to_json_file(result, output_file_name)


def collect_program_arguments():
    assert_args_correctness()
    output_f_name = sys.argv[1]
    bin_file_path = sys.argv[2]
    dic_path = sys.argv[3]
    repeating_bytes = int(sys.argv[4])
    if repeating_bytes < -1:
        repeating_bytes = -1
    aho_corasick = False  # Aho Corasick algorithm?
    if len(sys.argv) == 6:
        aho_corasick = sys.argv[5].lower() == 'true'
    main(output_f_name, bin_file_path, dic_path, repeating_bytes, aho_corasick)


def assert_args_correctness():
    if len(sys.argv) < 5:
        print("There is not enough arguments. Notice the args should be as follow:\n"
              "1: outputFileName. 2: path to binary file. 3: path to json file which holds the patterns as"
              " dictionary (keys = patterns).\n4: -1 or other threshold for repeating bytes, and 5: true/false"
              " for aho corasick algorithm")
        exit(-1)


def build_and_assert_dictionary_correctness(dict_file_path):
    with open(dict_file_path) as f:
        expression_map = json.load(f)  # Load dictionary from json
    if not expression_map:
        print("empty dictionary, exit")
        exit(-1)
    return expression_map


def sort_result_dictionary_by_key(rb_flag, result):
    result['pattern matching result'] = sorted(result['pattern matching result'], key=lambda k: k['Pattern'])
    if rb_flag != -1:
        result['repeating bytes result'] = sorted(result['repeating bytes result'], key=lambda k: k['Byte'])
    else:
        result.pop('repeating bytes result', None)


"""
Inputs: 
patters_dict - dictionary where its keys are hexes strings / valid regular expressions
binary file - file to read from
repeating bytes = if not equal to -1 sign to support repeating bytes with threshold = repeating_bytes
**
The function divide the binary file to several chunks, each of size 'BUFFER_SIZE', then
searching for patterns using two algorithms:
one -  regex finder, and (if asked for) two - aho corasick algorithm. Moreover,
the algorithm checked for repeated bytes (if needed). When find some pattern ->
add to "result" dictionary
At the end return "result" dictionary.
"""


def find_matching_patterns(patterns_dict, binary_file, aho_corasick, repeating_bytes=-1):
    overlap_bytes = ""
    offset = 0  # Current run offset
    result = {'pattern matching result': [], "repeating bytes result": []}
    max_length_pattern = calculate_max_pattern_size(patterns_dict)  # Hold the length of the longest pattern
    automaton = None  # Aho Corasick trie
    if aho_corasick:
        automaton = build_automaton_and_add_words(patterns_dict)

    buffer = binary_file.read(BUFFER_SIZE)  # Read first bytes to buffer
    reading_sz = BUFFER_SIZE - (max_length_pattern - 1)  # Reserve place for overlapping bytes

    while buffer:  # not EOF
        chunk = decode_bytes(overlap_bytes, buffer)
        if chunk is None:  # Problem while decoding bytes -> continue to next chunk
            buffer = binary_file.read(reading_sz)
            overlap_bytes = ""
            offset += reading_sz
            continue
        overlap_bytes = get_overlapping_bytes(chunk, max_length_pattern)  # <Max length pattern> - 1
        if aho_corasick:
            aho_corasick_algorithm_helper(automaton, offset, chunk, result)
        else:
            search_for_patterns_and_add(chunk, patterns_dict, offset, result)  # Add what we found to result.

        handle_repeating_bytes_if_needed(chunk, repeating_bytes, result)
        buffer = binary_file.read(reading_sz)
        offset += reading_sz

    return result


def decode_bytes(overlap_bytes, window):
    try:
        chunk = overlap_bytes + window.decode("UTF-8")  # decode bytes to string and update chunk
    except UnicodeDecodeError:
        return None
    return chunk


# Search for repeating bytes in chunk if asked for
def handle_repeating_bytes_if_needed(chunk, repeating_bytes, result):
    if repeating_bytes != -1:
        check_for_repeating_bytes(chunk, repeating_bytes, result)


# Search for patterns from exp_map in chunk
def search_for_patterns_and_add(chunk, exp_map, offset, result):
    for pattern in exp_map.keys():
        offsets = re.finditer(pattern, chunk)
        build_output_dictionary(offsets, offset, result)


# Return the last (max-pattern-len -1) chars
def get_overlapping_bytes(chunk, max_length_pattern):
    return chunk[-(max_length_pattern - 1)]


# Build suitable dictionary
def build_output_dictionary(offsets, offset, result):
    for i in offsets:
        dic = dict(Pattern=i.group(),
                   Offset="(" + hex(i.start() + offset + 1).__str__() + "," + hex(i.end() + offset).__str__() + ")")
        result['pattern matching result'].append(dic)


"""
Inputs: 
chunk - part of the file
threshold - threshold for the number of the repeating bytes
result - hold the result at the end
**
The function use regular expression - '(\w)(\1{x,}) which interpreting as: 
(\w) take every char - numbers, letters, etc. 
(\1{x,}) - the former expression to {x,} should appear at least x times.
\1 - the first reg expression in this pattern.
The function search for any number which appears at least threshold times 

"""


def check_for_repeating_bytes(chunk, threshold, result):
    # (\w) = every char,{4,} = the former should appear at least 4 times, \1= the first regExp
    reg = re.compile(r'(\w)(\1{x,})'.replace('x', (threshold - 1).__str__()))  # -1 Because of the first (\w)
    iterator = reg.finditer(chunk)  # Holds the solutions
    add_repeating_bytes_to_result(iterator, result)


"""
group - the bytes sequence we found
start -  sequence begin offset
end - sequence end offset 
"""


def add_repeating_bytes_to_result(iterator, result):
    for repeating_byte in iterator:
        dic = dict(Byte=repeating_byte.group()[0:1], Range=(hex(repeating_byte.start() + 1), hex(repeating_byte.end())),
                   size=repeating_byte.end() - repeating_byte.start())
        result['repeating bytes result'].append(dic)


# ------------------------------ Aho Corasick ------------------------------

# Build trie with failure links for the dictionary
def build_automaton_and_add_words(patterns_dictionary):
    automaton = ahocorasick.Automaton()
    for word in patterns_dictionary:
        automaton.add_word(word, (patterns_dictionary[word], word))  # Add words to the trie (Automaton)
    automaton.make_automaton()
    return automaton


# Search the chunk for the patterns in the automaton
def aho_corasick_algorithm_helper(automaton, offset, chunk, result):
    # --- Searching for the patterns in 'string'
    aho_run_res = []
    for end_index, (insert_order, original_value) in automaton.iter(chunk):
        start_index = end_index - len(original_value) + 1
        dic = dict(Pattern=original_value,
                   Offset="(" + hex(offset + start_index + 1).__str__() + "," + hex(
                       end_index + offset + 1).__str__() + ")")
        aho_run_res.append(dic)
    result['pattern matching result'] += aho_run_res


# --- Write the result dictionary to json file ---
def convert_to_json_file(dictionary, output_file_name):
    if not output_file_name[-len(".json"):] == ".json":  # Add .json suffix
        output_file_name += ".json"
    with open(output_file_name, 'w') as outfile:
        json.dump(dictionary, outfile)


def calculate_max_pattern_size(exp_map):
    return len(max(exp_map, key=len))


if __name__ == "__main__":
    start_time = time.time()
    collect_program_arguments()
    print("--- Program run time: %s seconds ---" % (time.time() - start_time))
