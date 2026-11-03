# ======================================================================
# complexity.py - data for the "Time and Space Complexity Graph".
# PURE LOGIC: no Tkinter. The GUI only draws the numbers produced here.
#
# Idea: instead of just drawing a textbook curve, we RUN each algorithm on inputs
# of growing size n (2, 4, 6, ... 40) and COUNT
#   time  = number of basic operations (comparisons / cells computed / items looked at)
#   space = number of extra memory cells the algorithm needs (tables, tree nodes, DP table)
# The counting functions live next to each algorithm: dijkstra_cost(), huffman_cost(),
# knapsack_cost(). Time and space are drawn together in ONE chart (log scale on the y axis).
# ======================================================================

import dijkstra  # dijkstra_cost()
import huffman  # huffman_cost()
import knapsack  # knapsack_cost()

SIZES = list(range(2, 42, 2))  # the input sizes n that are measured: 2, 4, 6, ... 40

# What each algorithm calls its input size and what the textbook says about it.
INFO = [
    {   # 0 = Dijkstra
        "name": "Dijkstra",
        "x_label": "n = number of cities V (sample graph: ring + shortcut roads, E = 2V)",
        "time_big_o": "O(V^2)",
        "space_big_o": "O(V)",
        "time_formula": "time  = V x V (scan for the closest city, once per city) + 2E (check every road)",
        "space_formula": "space = 3V (distance table + previous table + finished list)",
        "note": "The simple scan version is O(V^2). With a heap it becomes O((V + E) log V).",
    },
    {   # 1 = Huffman
        "name": "Huffman coding",
        "x_label": "n = number of different symbols (sample text: about 2.5 characters per symbol)",
        "time_big_o": "O(n log n) with a heap, O(n^2) for the simple list used here",
        "space_big_o": "O(n)",
        "time_formula": "time  = length (count) + sum of the list sizes while merging + 2n (tree walk, encode)",
        "space_formula": "space = (2n - 1) tree nodes + n frequencies + n codes",
        "note": "Merging n symbols takes n - 1 merges. The counted version scans the list each time, so it grows like n^2.",
    },
    {   # 2 = Knapsack
        "name": "0/1 Knapsack",
        "x_label": "n = number of items (sample input: capacity W = n)",
        "time_big_o": "O(n x W)",
        "space_big_o": "O(n x W)",
        "time_formula": "time  = n x (W + 1) cells, one comparison each, + n backtracking moves",
        "space_formula": "space = (n + 1) x (W + 1) cells of the DP table",
        "note": "Here time and space are both about n x W, so the two lines lie almost on top of each other. "
                "Only O(W) space is needed if you want just the value, but then you cannot backtrack.",
    },
]


def sample_dijkstra(n):
    """Graph with n cities in a ring (0-1-2-...-0) plus a shortcut from every city to the city two steps ahead."""
    names = []
    for i in range(n):
        names.append("c" + str(i))
    graph = {}
    for name in names:
        graph[name] = {}
    for i in range(n):
        a = names[i]
        b = names[(i + 1) % n]  # next city on the ring
        c = names[(i + 2) % n]  # shortcut
        if a != b:
            graph[a][b] = 1 + i % 4  # weights 1..4, repeatable
            graph[b][a] = 1 + i % 4
        if a != c and c not in graph[a]:
            graph[a][c] = 2 + i % 3
            graph[c][a] = 2 + i % 3
    return graph, names[0]


def sample_huffman(n):
    """Text with n different symbols; symbol k appears (k % 4) + 1 times."""
    text = ""
    for k in range(n):
        text = text + chr(256 + k) * (k % 4 + 1)  # chr(256+k) gives n different characters
    return text


def sample_knapsack(n):
    """n items with small repeatable weights and values; capacity W = n."""
    weights = []
    values = []
    for k in range(n):
        weights.append(1 + k % 5)
        values.append(3 + (k * 7) % 11)
    return weights, values, n


def measure_one(algo, n):
    """Return (operations, memory_cells) for the sample input of size n."""
    if algo == 0:
        graph, source = sample_dijkstra(n)
        return dijkstra.dijkstra_cost(graph, source)
    if algo == 1:
        return huffman.huffman_cost(sample_huffman(n))
    weights, values, capacity = sample_knapsack(n)
    return knapsack.knapsack_cost(weights, values, capacity)


def measure(algo, sizes=None):
    """Return a list of (n, operations, memory_cells), one entry per size."""
    if sizes is None:
        sizes = SIZES
    points = []
    for n in sizes:
        operations, memory = measure_one(algo, n)
        points.append((n, operations, memory))
    return points


def current_point(algo, graph, source, text, knap):
    """Measure the user's OWN input. Returns (n, operations, memory_cells, description) or None if the input is not valid.
    graph/source are the Dijkstra input, text the Huffman input, knap the (weights, values, capacity) tuple or None."""
    try:
        if algo == 0:
            operations, memory = dijkstra.dijkstra_cost(graph, source)
            n = len(graph)
            return n, operations, memory, "V = " + str(n) + " cities"
        if algo == 1:
            operations, memory = huffman.huffman_cost(text)
            n = len(huffman.count_frequencies(text))
            return n, operations, memory, "n = " + str(n) + " symbols"
        if knap is None:
            return None
        weights, values, capacity = knap
        operations, memory = knapsack.knapsack_cost(weights, values, capacity)
        n = len(weights)
        return n, operations, memory, "n = " + str(n) + " items, W = " + str(capacity)
    except (ValueError, KeyError):  # empty graph, unknown source, empty text ...
        return None
