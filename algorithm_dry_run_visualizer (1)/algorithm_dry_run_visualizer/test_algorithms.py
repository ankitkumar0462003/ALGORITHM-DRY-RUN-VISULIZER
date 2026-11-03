# Tests for the three algorithms. They never open a window (no Tkinter needed).
# Run with:   python test_algorithms.py

import itertools  # itertools.combinations lists every subset (used for the brute-force knapsack)
import random  # random numbers for the random tests
import unittest  # Python's built-in test framework

import complexity
import dijkstra
import huffman
import knapsack

INF = float("inf")


# ---------------------------------------------------------------- helpers
def two_way(edges):
    """Turn [('A','B',4), ...] into a two-way graph dictionary."""
    graph = {}
    for a, b, w in edges:
        graph.setdefault(a, {})[b] = w  # road a -> b
        graph.setdefault(b, {})[a] = w  # road b -> a
    return graph


def brute_force_shortest(graph, source, target):
    """Try every simple path (no repeated city) and return the smallest total. Slow but obviously right."""
    best = INF
    stack = [(source, [source], 0)]  # (city, path so far, cost so far)
    while stack:
        city, path, cost = stack.pop()
        if city == target:
            best = min(best, cost)
            continue
        for nxt, w in graph[city].items():
            if nxt not in path:
                stack.append((nxt, path + [nxt], cost + w))
    return best


def path_cost(graph, path):
    """Add up the road weights along a path (raises KeyError if a road does not exist)."""
    total = 0
    for i in range(len(path) - 1):
        total = total + graph[path[i]][path[i + 1]]
    return total


def last_step(generator):
    """Run a generator to the end and return its final dictionary."""
    steps = list(generator)
    return steps[-1]


# ---------------------------------------------------------------- Dijkstra
DEFAULT_GRAPH = two_way([("A", "B", 4), ("A", "C", 2), ("B", "C", 1), ("B", "D", 5),
                         ("C", "D", 8), ("C", "E", 10), ("D", "E", 2)])


class TestDijkstra(unittest.TestCase):
    def test_default_example(self):
        path, total = dijkstra.dijkstra(DEFAULT_GRAPH, "A", "E")
        self.assertEqual(total, 10)  # A-C-B-D-E = 2+1+5+2
        self.assertEqual(path, ["A", "C", "B", "D", "E"])

    def test_generator_matches_function(self):
        for source, target in [("A", "E"), ("E", "A"), ("B", "C"), ("D", "A")]:
            path, total = dijkstra.dijkstra(DEFAULT_GRAPH, source, target)
            final = last_step(dijkstra.dijkstra_steps(DEFAULT_GRAPH, source, target))
            self.assertEqual(final["total"], total)
            self.assertEqual(final["path"], path)

    def test_message_format_of_example(self):
        # the assignment's example message: visiting B, checking C
        messages = [s["message"] for s in dijkstra.dijkstra_steps(DEFAULT_GRAPH, "A", "E")]
        self.assertTrue(any("Visiting B (distance 3)" in m and "update it" in m for m in messages))

    def test_unreachable_city(self):
        graph = two_way([("A", "B", 1)])
        graph["Z"] = {}  # Z has no roads
        self.assertEqual(dijkstra.dijkstra(graph, "A", "Z"), (None, INF))
        final = last_step(dijkstra.dijkstra_steps(graph, "A", "Z"))
        self.assertIsNone(final["path"])
        self.assertEqual(final["total"], INF)
        self.assertIn("NO route", final["message"])

    def test_same_source_and_target(self):
        path, total = dijkstra.dijkstra(DEFAULT_GRAPH, "C", "C")
        self.assertEqual((path, total), (["C"], 0))
        self.assertEqual(last_step(dijkstra.dijkstra_steps(DEFAULT_GRAPH, "C", "C"))["path"], ["C"])

    def test_bad_input(self):
        with self.assertRaises(ValueError):
            dijkstra.dijkstra({}, "A", "B")  # empty graph
        with self.assertRaises(ValueError):
            dijkstra.dijkstra(DEFAULT_GRAPH, "Q", "A")  # unknown source
        with self.assertRaises(ValueError):
            list(dijkstra.dijkstra_steps(DEFAULT_GRAPH, "A", "Q"))  # unknown target
        with self.assertRaises(ValueError):
            dijkstra.dijkstra({"A": {"B": -1}, "B": {}}, "A", "B")  # negative weight

    def test_zero_weight_road(self):
        graph = two_way([("A", "B", 0), ("B", "C", 3)])
        self.assertEqual(dijkstra.dijkstra(graph, "A", "C")[1], 3)

    def test_steps_snapshots_do_not_change(self):
        # an earlier step must keep its own distance table (needed for Previous Step)
        steps = list(dijkstra.dijkstra_steps(DEFAULT_GRAPH, "A", "E"))
        self.assertEqual(steps[0]["distance"]["B"], INF)
        self.assertEqual(steps[0]["current"], None)

    def test_random_graphs_against_brute_force(self):
        rng = random.Random(1)
        for trial in range(300):
            n = rng.randint(2, 7)
            cities = [chr(65 + i) for i in range(n)]
            edges = []
            for a, b in itertools.combinations(cities, 2):
                if rng.random() < 0.45:  # about half of all possible roads
                    edges.append((a, b, rng.randint(0, 9)))
            graph = two_way(edges)
            for c in cities:
                graph.setdefault(c, {})
            source, target = rng.sample(cities, 2)
            expected = brute_force_shortest(graph, source, target)
            path, total = dijkstra.dijkstra(graph, source, target)
            final = last_step(dijkstra.dijkstra_steps(graph, source, target))
            self.assertEqual(total, expected)
            self.assertEqual(final["total"], expected)
            self.assertEqual(final["path"], path)
            if path is not None:  # the path must really exist and cost the total
                self.assertEqual(path_cost(graph, path), total)


# ---------------------------------------------------------------- Huffman
class TestHuffman(unittest.TestCase):
    def check_text(self, text):
        result = huffman.huffman_coding(text)
        final = last_step(huffman.huffman_steps(text))
        self.assertEqual(final["codes"], result["codes"])  # same codes
        self.assertEqual(final["encoded"], result["encoded"])  # same bits
        self.assertEqual(final["decoded"], text)  # lossless
        self.assertEqual(result["decoded"], text)
        self.assertTrue(final["lossless"])
        self.assertEqual(final["original_bits"], 8 * len(text))
        self.assertEqual(final["compressed_bits"], len(final["encoded"]))
        codes = list(final["codes"].values())
        for a in codes:  # prefix-free: no code is the start of another
            for b in codes:
                if a is not b and len(codes) > 1:
                    self.assertFalse(b.startswith(a) and a != b)
        return final

    def test_abracadabra(self):
        final = self.check_text("ABRACADABRA")
        self.assertEqual(final["compressed_bits"], 23)  # known optimal size
        self.assertEqual(final["original_bits"], 88)
        self.assertEqual(len(final["codes"]["A"]), 1)  # most common letter gets the shortest code

    def test_single_character_text(self):
        final = self.check_text("AAAAA")
        self.assertEqual(final["codes"], {"A": "0"})
        self.assertEqual(final["encoded"], "00000")
        one = self.check_text("Z")
        self.assertEqual(one["encoded"], "0")

    def test_two_symbols(self):
        final = self.check_text("AB")
        self.assertEqual(sorted(final["codes"].values()), ["0", "1"])

    def test_spaces_digits_and_unicode(self):
        self.check_text("hello world 123")
        self.check_text("a b  c")
        self.check_text("café ☃")

    def test_empty_text(self):
        with self.assertRaises(ValueError):
            huffman.huffman_coding("")
        with self.assertRaises(ValueError):
            list(huffman.huffman_steps(""))

    def test_step_count_and_merges(self):
        steps = list(huffman.huffman_steps("ABRACADABRA"))
        merges = [s for s in steps if s["kind"] == "merge"]
        self.assertEqual(len(merges), 4)  # 5 distinct symbols -> 4 merges
        self.assertEqual(len(merges[-1]["nodes"]), 1)  # one tree left at the end
        self.assertEqual(merges[-1]["merged"]["freq"], 11)  # root frequency = text length

    def test_compressed_size_is_optimal_vs_heap_free_check(self):
        # cost of a Huffman code = sum of all merge frequencies; compare with sum(freq * code length)
        rng = random.Random(2)
        for trial in range(200):
            text = "".join(rng.choice("ABCDEFG") for _ in range(rng.randint(1, 40)))
            steps = list(huffman.huffman_steps(text))
            merge_cost = sum(s["merged"]["freq"] for s in steps if s["kind"] == "merge")
            final = steps[-1]
            if len(set(text)) > 1:
                self.assertEqual(final["compressed_bits"], merge_cost)
            self.assertEqual(final["decoded"], text)
            self.assertEqual(final["codes"], huffman.huffman_coding(text)["codes"])


# ---------------------------------------------------------------- Knapsack
def brute_force_knapsack(weights, values, capacity):
    """Try every subset of items and return the best value."""
    n = len(weights)
    best = 0
    for size in range(n + 1):
        for subset in itertools.combinations(range(n), size):
            w = sum(weights[i] for i in subset)
            if w <= capacity:
                best = max(best, sum(values[i] for i in subset))
    return best


class TestKnapsack(unittest.TestCase):
    def check_case(self, weights, values, capacity):
        result = knapsack.knapsack(weights, values, capacity)
        final = last_step(knapsack.knapsack_steps(weights, values, capacity))
        self.assertEqual(final["best_value"], result["best_value"])
        self.assertEqual(final["chosen"], result["chosen"])
        self.assertEqual(final["total_weight"], result["total_weight"])
        self.assertEqual(final["table"], result["table"])
        self.assertEqual(result["best_value"], brute_force_knapsack(weights, values, capacity))
        chosen_value = sum(values[i - 1] for i in result["chosen"])
        chosen_weight = sum(weights[i - 1] for i in result["chosen"])
        self.assertEqual(chosen_value, result["best_value"])  # chosen items add up to the answer
        self.assertEqual(chosen_weight, result["total_weight"])
        self.assertLessEqual(chosen_weight, capacity)  # and they fit
        return final

    def test_default_example(self):
        final = self.check_case([2, 3, 4, 5], [3, 4, 5, 6], 5)
        self.assertEqual(final["best_value"], 7)
        self.assertEqual(final["chosen"], [1, 2])
        self.assertEqual(final["total_weight"], 5)

    def test_classic_example(self):
        final = self.check_case([1, 3, 4, 5], [1, 4, 5, 7], 7)
        self.assertEqual(final["best_value"], 9)

    def test_item_heavier_than_capacity(self):
        final = self.check_case([10, 2], [100, 5], 5)
        self.assertEqual(final["chosen"], [2])  # the heavy item can never be taken
        self.assertEqual(final["best_value"], 5)
        everything_heavy = self.check_case([10, 20], [100, 200], 5)
        self.assertEqual(everything_heavy["chosen"], [])
        self.assertEqual(everything_heavy["best_value"], 0)

    def test_capacity_zero(self):
        final = self.check_case([1, 2, 3], [10, 20, 30], 0)
        self.assertEqual(final["best_value"], 0)
        self.assertEqual(final["chosen"], [])

    def test_exact_fit_and_ties(self):
        self.check_case([2, 2], [3, 3], 2)  # tie: either item is fine
        self.check_case([3], [9], 3)  # one item, exact fit
        self.check_case([1, 1, 1], [0, 0, 0], 3)  # all values zero

    def test_step_shape(self):
        steps = list(knapsack.knapsack_steps([2, 3, 4, 5], [3, 4, 5, 6], 5))
        cells = [s for s in steps if s["kind"] == "cell"]
        self.assertEqual(len(cells), 4 * 6)  # n * (W + 1) cells
        self.assertIsNone(steps[0]["table"][1][0])  # not computed yet
        self.assertEqual(steps[0]["table"][0], [0] * 6)  # row 0 is all zeros
        heavy = cells[0]  # item 1 (weight 2), capacity 0 does not fit
        self.assertIsNone(heavy["take"])
        self.assertEqual(heavy["choice"], "skip")

    def test_bad_input(self):
        with self.assertRaises(ValueError):
            knapsack.knapsack([], [], 5)  # no items
        with self.assertRaises(ValueError):
            knapsack.knapsack([1, 2], [3], 5)  # lengths differ
        with self.assertRaises(ValueError):
            list(knapsack.knapsack_steps([-1], [3], 5))  # negative weight
        with self.assertRaises(ValueError):
            knapsack.knapsack([1], [-3], 5)  # negative value
        with self.assertRaises(ValueError):
            knapsack.knapsack([1], [3], -5)  # negative capacity

    def test_random_against_brute_force(self):
        rng = random.Random(3)
        for trial in range(400):
            n = rng.randint(1, 8)
            weights = [rng.randint(1, 9) for _ in range(n)]
            values = [rng.randint(0, 20) for _ in range(n)]
            capacity = rng.randint(0, 25)
            self.check_case(weights, values, capacity)


# ---------------------------------------------------------------- formulas and detailed explanations
class TestFormulasAndDetails(unittest.TestCase):
    def every_step_has_text(self, steps):
        for number, step in enumerate(steps):
            self.assertTrue(step["formula"].strip() != "", msg="step " + str(number) + " has no formula")
            self.assertTrue(len(step["detail"]) > 60, msg="step " + str(number) + " has a too short explanation")

    def test_every_step_has_formula_and_detail(self):
        self.every_step_has_text(list(dijkstra.dijkstra_steps(DEFAULT_GRAPH, "A", "E")))
        self.every_step_has_text(list(huffman.huffman_steps("ABRACADABRA")))
        self.every_step_has_text(list(knapsack.knapsack_steps([2, 3, 4, 5], [3, 4, 5, 6], 5)))

    def test_edge_cases_also_have_text(self):
        unreachable = two_way([("A", "B", 1)])
        unreachable["Z"] = {}
        self.every_step_has_text(list(dijkstra.dijkstra_steps(unreachable, "A", "Z")))
        self.every_step_has_text(list(dijkstra.dijkstra_steps(DEFAULT_GRAPH, "C", "C")))
        self.every_step_has_text(list(huffman.huffman_steps("AAAA")))  # single symbol
        self.every_step_has_text(list(knapsack.knapsack_steps([10, 20], [100, 200], 5)))  # nothing fits
        self.every_step_has_text(list(knapsack.knapsack_steps([1, 2], [3, 4], 0)))  # capacity 0

    def test_dijkstra_formula_numbers(self):
        steps = list(dijkstra.dijkstra_steps(DEFAULT_GRAPH, "A", "E"))
        update = [s for s in steps if "Visiting C" in s["message"] and "neighbour B" in s["message"]][0]
        self.assertIn("new = dist[C] + weight(C,B) = 2 + 1 = 3", update["formula"])
        self.assertIn("3 < 4  YES", update["formula"])
        self.assertIn("previous[B] = C", update["formula"])
        # a graph where one check does NOT improve: A-B 1, A-C 1, B-C 1 (from B, 1 + 1 = 2 is not shorter than 1)
        triangle = two_way([("A", "B", 1), ("A", "C", 1), ("B", "C", 1)])
        keep = [s for s in dijkstra.dijkstra_steps(triangle, "A", "C") if "not shorter" in s["message"]]
        self.assertEqual(len(keep), 1)
        self.assertIn("1 + 1 = 2", keep[0]["formula"])
        self.assertIn("2 < 1  NO", keep[0]["formula"])
        self.assertIn("dist[C] stays 1", keep[0]["formula"])
        self.assertEqual(steps[-1]["formula"].splitlines()[1], "total = 2 + 1 + 5 + 2 = 10")
        self.assertIn("E <- D <- B <- C <- A", steps[-1]["formula"])

    def test_huffman_formula_numbers(self):
        steps = list(huffman.huffman_steps("ABRACADABRA"))
        self.assertIn("CD.freq = C.freq + D.freq = 1 + 1 = 2", steps[1]["formula"])
        self.assertIn("nodes left = n - merges = 5 - 1 = 4", steps[1]["formula"])
        self.assertIn("sum of all merged frequencies so far = 23", steps[4]["formula"])  # equals the compressed size
        self.assertIn("8 x 11 = 88 bits", steps[-1]["formula"])
        self.assertIn("= 23 bits", steps[-1]["formula"])
        self.assertIn("73.9%", steps[-1]["formula"])

    def test_knapsack_formula_numbers(self):
        steps = list(knapsack.knapsack_steps([2, 3, 4, 5], [3, 4, 5, 6], 5))
        cell = [s for s in steps if s["kind"] == "cell" and s["cell"] == (2, 5)][0]
        self.assertIn("skip = dp[1][5] = 3", cell["formula"])
        self.assertIn("take = value_2 + dp[1][5 - 3] = 4 + dp[1][2] = 4 + 3 = 7", cell["formula"])
        self.assertIn("dp[2][5] = max(3, 7) = 7", cell["formula"])
        heavy = [s for s in steps if s["kind"] == "cell" and s["cell"] == (1, 1)][0]
        self.assertIn("weight_1 > w   (2 > 1)", heavy["formula"])
        last = steps[-1]["formula"]
        self.assertIn("value  = 3 + 4 = 7", last)
        self.assertIn("weight = 2 + 3 = 5  <=  capacity 5", last)

    def test_explanations_use_correct_grammar_for_small_counts(self):
        self.assertEqual(knapsack.first_items(0), "no items")
        self.assertEqual(knapsack.first_items(1), "the first item")
        self.assertEqual(knapsack.first_items(3), "the first 3 items")
        for weights, values, capacity in ([2, 3, 4, 5], [3, 4, 5, 6], 5), ([1, 1], [2, 2], 3):
            for step in knapsack.knapsack_steps(weights, values, capacity):
                self.assertNotIn("first 1 items", step["detail"])
                self.assertNotIn("first 0 items", step["detail"])

    def test_knapsack_formula_matches_stored_table_value(self):
        # the number at the end of every 'dp[i][w] = max(a, b) = r' line must equal the table cell
        rng = random.Random(5)
        for trial in range(60):
            n = rng.randint(1, 5)
            weights = [rng.randint(1, 6) for _ in range(n)]
            values = [rng.randint(0, 9) for _ in range(n)]
            capacity = rng.randint(1, 10)
            for step in knapsack.knapsack_steps(weights, values, capacity):
                if step["kind"] == "cell" and step["take"] is not None:
                    i, w = step["cell"]
                    last_line = step["formula"].splitlines()[-1]
                    expected = "dp[" + str(i) + "][" + str(w) + "] = max(" + str(step["skip"]) + ", " + str(step["take"]) \
                               + ") = " + str(step["table"][i][w])
                    self.assertEqual(last_line, expected)
                    self.assertEqual(step["table"][i][w], max(step["skip"], step["take"]))


# ---------------------------------------------------------------- complexity graph data
class TestComplexity(unittest.TestCase):
    def test_dijkstra_cost_formula(self):
        # time = V * (V + 1) scans + 2E road checks for a connected graph; here V = 5, E = 7
        operations, memory = dijkstra.dijkstra_cost(DEFAULT_GRAPH, "A")
        self.assertEqual(operations, 5 * 6 + 14)
        self.assertEqual(memory, 15)

    def test_knapsack_cost_formula(self):
        operations, memory = knapsack.knapsack_cost([2, 3, 4, 5], [3, 4, 5, 6], 5)
        self.assertEqual(operations, 4 * 6 + 4)  # n*(W+1) cells + n backtracking moves
        self.assertEqual(memory, 5 * 6)  # (n+1)*(W+1) table cells

    def test_huffman_cost_simple_cases(self):
        operations, memory = huffman.huffman_cost("ABRACADABRA")
        self.assertGreater(operations, 11)
        self.assertEqual(memory, 9 + 5 + 5)  # 2n-1 nodes + n frequencies + n codes
        one_operations, one_memory = huffman.huffman_cost("AAAA")
        self.assertEqual(one_memory, 1 + 1 + 1)

    def test_cost_functions_reject_bad_input(self):
        with self.assertRaises(ValueError):
            huffman.huffman_cost("")
        with self.assertRaises(ValueError):
            knapsack.knapsack_cost([], [], 5)
        with self.assertRaises(ValueError):
            dijkstra.dijkstra_cost({}, "A")  # empty graph
        with self.assertRaises(ValueError):
            dijkstra.dijkstra_cost(DEFAULT_GRAPH, "Q")  # unknown source

    def test_measure_has_expected_shape(self):
        for algo in range(3):
            points = complexity.measure(algo)
            self.assertEqual(len(points), len(complexity.SIZES))
            previous_time = 0
            previous_space = 0
            for n, time_cost, space_cost in points:
                self.assertGreater(time_cost, previous_time)  # more input always costs more
                self.assertGreater(space_cost, previous_space)
                previous_time = time_cost
                previous_space = space_cost

    def test_growth_matches_big_o(self):
        # doubling n: quadratic time grows about 4 times, linear space about 2 times
        def ratio(algo, which):
            data = {}
            for n, time_cost, space_cost in complexity.measure(algo, [20, 40]):
                data[n] = (time_cost, space_cost)
            return data[40][which] / data[20][which]
        self.assertTrue(3.3 < ratio(0, 0) < 4.2)  # Dijkstra time ~ V^2
        self.assertTrue(1.8 < ratio(0, 1) < 2.2)  # Dijkstra space ~ V
        self.assertTrue(1.8 < ratio(1, 1) < 2.2)  # Huffman space ~ n
        self.assertTrue(3.3 < ratio(2, 0) < 4.2)  # Knapsack time ~ n*W with W = n
        self.assertTrue(3.3 < ratio(2, 1) < 4.2)  # Knapsack space ~ n*W

    def test_sample_inputs_are_valid_and_repeatable(self):
        for n in (2, 3, 10, 40):
            graph, source = complexity.sample_dijkstra(n)
            dijkstra.check_input(graph, source, source)
            self.assertEqual(len(graph), n)
            text = complexity.sample_huffman(n)
            self.assertEqual(len(set(text)), n)
            weights, values, capacity = complexity.sample_knapsack(n)
            knapsack.check_input(weights, values, capacity)
        self.assertEqual(complexity.sample_huffman(7), complexity.sample_huffman(7))

    def test_current_point(self):
        point = complexity.current_point(0, DEFAULT_GRAPH, "A", "", None)
        self.assertEqual(point[:3], (5, 44, 15))
        point = complexity.current_point(2, {}, "", "", ([2, 3, 4, 5], [3, 4, 5, 6], 5))
        self.assertEqual(point[:3], (4, 28, 30))
        point = complexity.current_point(1, {}, "", "ABRACADABRA", None)
        self.assertEqual(point[0], 5)
        self.assertIsNone(complexity.current_point(0, {}, "", "", None))  # empty graph
        self.assertIsNone(complexity.current_point(0, DEFAULT_GRAPH, "Q", "", None))  # unknown source
        self.assertIsNone(complexity.current_point(1, {}, "", "", None))  # empty text
        self.assertIsNone(complexity.current_point(2, {}, "", "", None))  # invalid knapsack input


if __name__ == "__main__":
    unittest.main(verbosity=2)  # verbosity=2 prints each test name
