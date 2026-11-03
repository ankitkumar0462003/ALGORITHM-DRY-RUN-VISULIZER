# ======================================================================
# Algorithm  : Huffman coding (lossless text compression)
# Technique  : Greedy (always merge the two least frequent nodes)
# Time       : O(n log n) with a heap, n = number of distinct symbols
#              (huffman_steps re-sorts a list each round: O(n^2 log n), fine for a demo)
# Space      : O(n) for the tree and the code table
# Use when   : You want a prefix-free variable-length code so that frequent
#              symbols get short codes (used inside ZIP, JPEG, MP3 ...).
# ======================================================================
# This file is PURE LOGIC: no Tkinter.
#
# A tree node is a dictionary:
#     {"id": 3, "symbol": "A" or None, "freq": 5, "left": node/None, "right": node/None}
# Leaves have a symbol; internal (merged) nodes have symbol None.
# Nodes are never changed after they are created, so it is safe to share them between steps.

import heapq  # used by huffman_coding() to get the smallest node quickly


def check_text(text):
    """Raise ValueError if the text cannot be compressed."""
    if text is None or text == "":  # nothing to compress
        raise ValueError("The text is empty. Type some text to compress.")


def count_frequencies(text):
    """Return a dictionary {symbol: how many times it appears}."""
    freq = {}  # empty table
    for ch in text:  # look at each character
        if ch in freq:  # seen before: add one
            freq[ch] = freq[ch] + 1
        else:  # first time: start at 1
            freq[ch] = 1
    return freq


def make_leaves(freq):
    """Make one leaf node per symbol. Sorted by (freq, symbol) so the result is repeatable."""
    pairs = []  # list of (frequency, symbol) so Python can sort it directly
    for symbol in freq:
        pairs.append((freq[symbol], symbol))
    pairs.sort()  # lowest frequency first; equal frequencies sorted by symbol
    leaves = []
    next_id = 0  # every node gets a unique number (used to break ties)
    for frequency, symbol in pairs:
        leaves.append({"id": next_id, "symbol": symbol, "freq": frequency, "left": None, "right": None})
        next_id = next_id + 1
    return leaves, next_id


def node_key(node):
    """Sorting key: lowest frequency first, ties broken by the older (smaller id) node."""
    return (node["freq"], node["id"])


def merge(first, second, new_id):
    """Join two nodes under a new parent whose frequency is the sum."""
    return {"id": new_id, "symbol": None, "freq": first["freq"] + second["freq"],
            "left": first, "right": second}  # smaller node goes LEFT (edge 0), the other RIGHT (edge 1)


def build_codes(root):
    """Walk the tree: left edge adds '0', right edge adds '1'. Returns {symbol: bits}."""
    codes = {}
    if root["symbol"] is not None:  # only one symbol in the text: give it the code "0"
        codes[root["symbol"]] = "0"
        return codes
    stack = [(root, "")]  # (node, bits so far); a stack replaces recursion
    while stack:
        node, bits = stack.pop()
        if node["symbol"] is not None:  # reached a leaf: the path is its code
            codes[node["symbol"]] = bits
        else:
            stack.append((node["right"], bits + "1"))  # right edge = 1
            stack.append((node["left"], bits + "0"))  # left edge = 0
    return codes


def encode(text, codes):
    """Replace every character by its code and join them."""
    result = ""
    for ch in text:
        result = result + codes[ch]
    return result


def decode(bits, root):
    """Walk the tree bit by bit; every time we hit a leaf we output its symbol."""
    if root["symbol"] is not None:  # single-symbol tree: every bit is that symbol
        return root["symbol"] * len(bits)
    text = ""
    node = root  # start at the top
    for bit in bits:
        if bit == "0":  # 0 means go left
            node = node["left"]
        else:  # 1 means go right
            node = node["right"]
        if node["symbol"] is not None:  # leaf reached
            text = text + node["symbol"]
            node = root  # go back to the top for the next symbol
    return text


def label(node):
    """Name of a node: its symbol, or the combined name like 'CD' made from its leaves."""
    if node["symbol"] is not None:
        return node["symbol"]
    return label(node["left"]) + label(node["right"])


def huffman_coding(text):
    """Return the final answer as a dictionary (no steps)."""
    check_text(text)
    freq = count_frequencies(text)
    leaves, next_id = make_leaves(freq)
    heap = []  # heap of (freq, id, node): ties broken by id, same as huffman_steps
    for leaf in leaves:
        heapq.heappush(heap, (leaf["freq"], leaf["id"], leaf))
    while len(heap) > 1:  # until one tree remains
        f1, id1, a = heapq.heappop(heap)  # smallest
        f2, id2, b = heapq.heappop(heap)  # second smallest
        parent = merge(a, b, next_id)
        next_id = next_id + 1
        heapq.heappush(heap, (parent["freq"], parent["id"], parent))
    root = heap[0][2]
    codes = build_codes(root)
    bits = encode(text, codes)
    return {"codes": codes, "encoded": bits, "original_bits": 8 * len(text),
            "compressed_bits": len(bits), "decoded": decode(bits, root), "root": root}


def huffman_cost(text):
    """Count the work of the simple list version for the complexity graph.
    Returns (operations, memory_cells). One operation = one character or one node looked at."""
    check_text(text)
    operations = 0
    freq = count_frequencies(text)
    operations = operations + len(text)  # counting: look at every character once
    nodes, next_id = make_leaves(freq)
    n = len(nodes)  # number of distinct symbols
    operations = operations + n * 2  # building and sorting the first list (about 2 looks per leaf)
    total_nodes = n  # every leaf and every merged node is stored
    while len(nodes) > 1:
        operations = operations + len(nodes)  # scanning the list to find the two lowest nodes
        nodes.sort(key=node_key)
        parent = merge(nodes[0], nodes[1], next_id)
        next_id = next_id + 1
        nodes = nodes[2:] + [parent]
        total_nodes = total_nodes + 1
    root = nodes[0]
    codes = build_codes(root)
    operations = operations + total_nodes  # walking the tree visits every node once
    bits = encode(text, codes)
    operations = operations + len(text)  # encoding: one code lookup per character
    memory_cells = total_nodes + len(freq) + len(codes)  # tree nodes + frequency table + code table
    return operations, memory_cells


def make_step(kind, message, nodes, picked=None, merged=None, formula="", detail=""):
    """Build one step dictionary."""
    return {
        "kind": kind,  # "start", "merge", "single" or "done"
        "message": message,  # short plain-English sentence
        "formula": formula,  # the formula of this step with the real numbers filled in
        "detail": detail,  # longer explanation of why and what it means
        "nodes": list(nodes),  # the current forest (list of root nodes)
        "picked": picked,  # the two lowest nodes chosen (list) or None
        "merged": merged,  # the new parent node or None
        "freq": None, "codes": None, "encoded": None,  # filled in on the last step only
        "original_bits": None, "compressed_bits": None, "decoded": None, "lossless": None,
        "root": None,
    }


def nodes_text(nodes):
    """Text such as 'C:1, D:1, B:2' for a list of nodes."""
    parts = []
    for node in nodes:
        parts.append(label(node) + ":" + str(node["freq"]))
    return ", ".join(parts)


def huffman_steps(text):
    """Generator: yields one dictionary per step. The LAST one holds the final result."""
    check_text(text)
    freq = count_frequencies(text)
    nodes, next_id = make_leaves(freq)  # starting list of leaf nodes
    n = len(nodes)  # number of distinct symbols

    freq_lines = []  # lines such as "A appears 5 times"
    for node in nodes:
        freq_lines.append(node["symbol"] + ":" + str(node["freq"]))
    yield make_step(
        "start", "Start: count each symbol. Nodes are (symbol:frequency) -> " + ", ".join(freq_lines) + ".", nodes,
        formula="frequency[c] = how many times c appears in the text\n"
                "length = " + str(len(text)) + " characters, distinct symbols n = " + str(n) + "\n"
                "merges needed = n - 1 = " + str(n - 1),
        detail="Huffman coding gives short bit codes to common symbols and long codes to rare ones. "
               "Step one is to count how often every symbol appears. Each symbol becomes a node "
               "(symbol:frequency): " + ", ".join(freq_lines) + ". Then we repeat: take the two nodes with the "
               "smallest frequencies and join them under a new parent whose frequency is their sum. "
               "Each merge removes one node from the list, so after n - 1 = " + str(n - 1) + " merges only "
               "one tree is left.")

    if n == 1:  # special case: only one distinct symbol
        yield make_step(
            "single", "Only one distinct symbol, so there is nothing to merge. We give it the code 0.", nodes,
            formula="n = 1  ->  merges needed = n - 1 = 0\ncode[" + nodes[0]["symbol"] + "] = 0",
            detail="With a single kind of character there is no choice to make, so no tree can be built. "
                   "By convention the symbol gets the 1-bit code 0, so every character costs 1 bit.")

    merge_number = 0  # how many merges are done so far
    merge_cost = 0  # running total of all merged frequencies
    while len(nodes) > 1:  # keep merging until one tree is left
        before = nodes_text(sorted(nodes, key=node_key))  # the list as it looks before this merge
        nodes.sort(key=node_key)  # lowest frequency first, ties by id
        a = nodes[0]  # lowest
        b = nodes[1]  # second lowest
        parent = merge(a, b, next_id)  # new node
        next_id = next_id + 1
        merge_number = merge_number + 1
        merge_cost = merge_cost + parent["freq"]
        sum_text = (label(parent) + ".freq = " + label(a) + ".freq + " + label(b) + ".freq = "
                    + str(a["freq"]) + " + " + str(b["freq"]) + " = " + str(parent["freq"]))
        message = ("Pick the two lowest: " + label(a) + "(" + str(a["freq"]) + ") and "
                   + label(b) + "(" + str(b["freq"]) + "). Merge them into a new node "
                   + label(parent) + "(" + str(parent["freq"]) + ") = "
                   + str(a["freq"]) + " + " + str(b["freq"]) + ". "
                   + label(a) + " goes on the left edge (0), " + label(b) + " on the right edge (1).")
        nodes = nodes[2:] + [parent]  # remove the two, add the parent
        formula = (sum_text + "\n"
                   "merge " + str(merge_number) + " of " + str(n - 1) + "   nodes left = n - merges = "
                   + str(n) + " - " + str(merge_number) + " = " + str(len(nodes)) + "\n"
                   "sum of all merged frequencies so far = " + str(merge_cost))
        detail = ("The list before this step, lowest first: " + before + ". The two smallest frequencies are "
                  + str(a["freq"]) + " (" + label(a) + ") and " + str(b["freq"]) + " (" + label(b) + "), so these "
                  "are the rarest parts. We join them under a new parent " + label(parent) + " with frequency "
                  + str(parent["freq"]) + ". The smaller node is placed on the left edge (bit 0) and the other on "
                  "the right edge (bit 1). Because the rarest symbols are merged first, they sink deepest in the "
                  "tree and get the longest codes. Useful fact: the compressed size in bits equals the sum of all "
                  "merged frequencies, which is " + str(merge_cost) + " so far.")
        yield make_step("merge", message, nodes, [a, b], parent, formula, detail)

    root = nodes[0]  # the finished tree
    codes = build_codes(root)
    bits = encode(text, codes)
    decoded = decode(bits, root)
    compressed = len(bits)
    original = 8 * len(text)  # normal ASCII uses 8 bits per character
    saved = 100.0 * (original - compressed) / original

    pairs = []  # (frequency, symbol) so we can list the biggest first
    for symbol in freq:
        pairs.append((freq[symbol], symbol))
    pairs.sort(reverse=True)
    sum_parts = []  # pieces such as "5x1"
    for frequency, symbol in pairs:
        sum_parts.append(str(frequency) + "x" + str(len(codes[symbol])))
    code_lines = []  # pieces such as "A=0"
    for frequency, symbol in pairs:
        code_lines.append(symbol + "=" + codes[symbol])

    last = make_step(
        "done", "", nodes,
        formula="original = 8 x length = 8 x " + str(len(text)) + " = " + str(original) + " bits\n"
                "compressed = sum(frequency x code length) = " + " + ".join(sum_parts) + " = " + str(compressed) + " bits\n"
                "saved = (original - compressed) / original = (" + str(original) + " - " + str(compressed)
                + ") / " + str(original) + " = " + str(round(saved, 1)) + "%",
        detail="Only one node is left: the root of the Huffman tree. To read a code, walk from the root to a leaf: "
               "left edge = 0, right edge = 1. Codes: " + ", ".join(code_lines) + ". No code is the beginning "
               "of another code (prefix-free), so the bit string can be decoded without separators. Encoded bits: "
               + bits + ". Normal text uses 8 bits per character, but here frequent symbols need only a few bits, "
               "so the size drops from " + str(original) + " to " + str(compressed) + " bits. Decoding the bits with "
               "the same tree gives '" + decoded + "', which is exactly the original text, so the compression is lossless.")
    last["freq"] = freq
    last["codes"] = codes
    last["encoded"] = bits
    last["original_bits"] = original
    last["compressed_bits"] = compressed
    last["decoded"] = decoded
    last["lossless"] = (decoded == text)
    last["root"] = root
    last["message"] = ("Tree complete. Read codes from the tree (left=0, right=1). Original size = "
                       + str(original) + " bits, compressed size = " + str(compressed)
                       + " bits. Decoding the bits gives back the text, so it is lossless: "
                       + str(decoded == text) + ".")
    yield last
