# OPTIONAL extra test: drives the REAL Tkinter window by "pressing" its buttons from code.
# It needs a display. On Windows/macOS just run:   python test_gui.py
# On a Linux machine without a screen use a virtual one:   xvfb-run -a python test_gui.py
# (test_algorithms.py is the main test file and does not need any display.)

import time  # used to wait while Play is running
import tkinter as tk
import unittest

from gui import App


def pump(root, seconds):
    """Let Tkinter handle events (timers, redraws) for a number of seconds."""
    end = time.time() + seconds
    while time.time() < end:
        root.update()
        time.sleep(0.01)


class GuiBase(unittest.TestCase):
    """Shared set-up: one real window, helper functions. It has no tests of its own."""

    @classmethod
    def setUpClass(cls):
        cls.root = tk.Tk()  # one real window for all tests
        cls.root.geometry("1220x800")
        cls.app = App(cls.root)
        pump(cls.root, 0.3)

    @classmethod
    def tearDownClass(cls):
        cls.app.on_close()

    def setUp(self):
        # go back to a clean default state before every test
        app = self.app
        app.notebook.select(0)
        pump(self.root, 0.05)
        app.load_default_graph()
        app.text_var.set("ABRACADABRA")
        app.weights_var.set("2, 3, 4, 5")
        app.values_var.set("3, 4, 5, 6")
        app.capacity_var.set("5")
        app.speed_var.set(200)
        app.reset()
        pump(self.root, 0.05)

    def state(self, button):
        return str(button.cget("state"))

    def result(self):
        return self.app.result_text.get("1.0", "end").strip()

    def dry(self):
        return self.app.dry_text.get("1.0", "end").strip()

    def go_to_end(self):
        while self.app.index < len(self.app.steps) - 1:
            self.app.next_btn.invoke()
            self.root.update()

class TestGui(GuiBase):
    # ---------------------------------------------------------- buttons and stepping
    def test_initial_button_states(self):
        app = self.app
        self.assertEqual(self.state(app.start_btn), "normal")
        for button in (app.prev_btn, app.next_btn, app.play_btn, app.pause_btn):
            self.assertEqual(self.state(button), "disabled")
        self.assertEqual(app.counter_var.get(), "Not started")

    def test_dijkstra_full_walkthrough(self):
        app = self.app
        app.start_btn.invoke()
        total = len(app.steps)
        self.assertGreater(total, 5)
        self.assertEqual(app.counter_var.get(), "Step 1 of " + str(total))
        self.assertEqual(self.state(app.prev_btn), "disabled")  # nothing before step 1
        self.assertEqual(self.state(app.next_btn), "normal")
        app.next_btn.invoke()
        app.next_btn.invoke()
        self.assertEqual(app.counter_var.get(), "Step 3 of " + str(total))
        message_at_3 = self.dry()
        app.next_btn.invoke()
        app.prev_btn.invoke()  # Previous Step must show the earlier step again
        self.assertEqual(app.counter_var.get(), "Step 3 of " + str(total))
        self.assertEqual(self.dry(), message_at_3)
        self.go_to_end()
        self.assertEqual(app.counter_var.get(), "Step " + str(total) + " of " + str(total))
        self.assertIn("A -> C -> B -> D -> E", self.result())
        self.assertIn("10", self.result())
        self.assertEqual(self.state(app.play_btn), "disabled")  # nothing left to play
        self.assertEqual(self.state(app.next_btn), "normal")  # Next still works at the end
        app.next_btn.invoke()  # Next after finish: friendly message, result shown again
        self.assertIn("already finished", app.status_var.get())
        self.assertIn("A -> C -> B -> D -> E", self.result())
        self.assertEqual(app.counter_var.get(), "Step " + str(total) + " of " + str(total))

    def test_play_pause_and_speed(self):
        app = self.app
        app.start_btn.invoke()
        app.play_btn.invoke()
        self.assertTrue(app.playing)
        self.assertEqual(self.state(app.pause_btn), "normal")
        self.assertEqual(self.state(app.next_btn), "disabled")  # manual buttons off while playing
        pump(self.root, 0.9)  # about 4 ticks at 200 ms
        app.pause_btn.invoke()
        stopped_at = app.index
        self.assertGreater(stopped_at, 1)
        self.assertFalse(app.playing)
        pump(self.root, 0.6)
        self.assertEqual(app.index, stopped_at)  # really paused
        app.play_btn.invoke()  # continue to the end
        pump(self.root, 0.3 + 0.25 * len(app.steps))
        self.assertEqual(app.index, len(app.steps) - 1)
        self.assertFalse(app.playing)
        self.assertEqual(self.state(app.play_btn), "disabled")

    def test_reset_button(self):
        app = self.app
        app.start_btn.invoke()
        app.next_btn.invoke()
        app.reset_btn.invoke()
        self.assertEqual(app.index, -1)
        self.assertEqual(app.counter_var.get(), "Not started")
        self.assertEqual(self.state(app.next_btn), "disabled")

    def test_changing_input_resets(self):
        app = self.app
        app.start_btn.invoke()
        app.next_btn.invoke()
        app.dst_var.set("D")
        app.dst_box.event_generate("<<ComboboxSelected>>")  # what picking from the drop-down does
        self.root.update()
        self.assertEqual(app.index, -1)
        app.start_btn.invoke()
        app.notebook.select(1)
        pump(self.root, 0.05)
        self.assertEqual(app.index, -1)  # switching tab resets too
        app.start_btn.invoke()
        app.text_var.set("HELLO")  # typing in the box resets
        self.assertEqual(app.index, -1)

    # ---------------------------------------------------------- Dijkstra errors and editing
    def test_dijkstra_same_source_and_destination(self):
        app = self.app
        app.dst_var.set("A")
        app.start_btn.invoke()
        self.assertEqual(app.index, -1)
        self.assertIn("same city", app.status_var.get())

    def test_dijkstra_unreachable(self):
        app = self.app
        app.city_var.set("Z")
        app.add_city()  # Z has no roads
        app.dst_var.set("Z")
        app.start_btn.invoke()
        self.assertGreater(app.index, -1)  # the dry run still runs
        self.go_to_end()
        self.assertIn("No route", self.result())
        self.assertIn("Unreachable", app.status_var.get())

    def test_dijkstra_empty_graph_and_editing(self):
        app = self.app
        app.clear_graph()
        app.start_btn.invoke()
        self.assertIn("empty", app.status_var.get())
        app.city_var.set("")
        app.add_city()
        self.assertIn("Type a city name", app.status_var.get())
        for name in ("X", "Y"):
            app.city_var.set(name)
            app.add_city()
        app.city_var.set("X")
        app.add_city()  # duplicate
        self.assertIn("already exists", app.status_var.get())
        app.road_a.set("X")
        app.road_b.set("X")
        app.add_road()
        self.assertIn("two different", app.status_var.get())
        app.road_b.set("Y")
        app.weight_var.set("-3")
        app.add_road()
        self.assertIn("negative", app.status_var.get())
        app.weight_var.set("abc")
        app.add_road()
        self.assertIn("not a whole number", app.status_var.get())
        app.weight_var.set("")
        app.add_road()
        self.assertIn("Please enter", app.status_var.get())
        app.weight_var.set("7")
        app.add_road()
        self.assertEqual(app.graph["X"]["Y"], 7)
        self.assertEqual(app.graph["Y"]["X"], 7)
        app.src_var.set("X")
        app.dst_var.set("Y")
        app.start_btn.invoke()
        self.go_to_end()
        self.assertIn("X -> Y", self.result())
        app.city_var.set("Y")
        app.remove_city()
        self.assertNotIn("Y", app.graph)
        self.assertNotIn("Y", app.graph["X"])
        app.city_var.set("nope")
        app.remove_city()
        self.assertIn("existing city", app.status_var.get())

    # ---------------------------------------------------------- Huffman
    def test_huffman_walkthrough(self):
        app = self.app
        app.notebook.select(1)
        pump(self.root, 0.05)
        app.start_btn.invoke()
        self.assertEqual(len(app.steps), 6)  # start + 4 merges + final
        self.go_to_end()
        self.assertIn("23 bits", self.result())
        self.assertIn("lossless", self.result())
        self.assertIn("ABRACADABRA", self.result())
        rows = app.table.get_children()
        self.assertEqual(len(rows), 5)  # 5 different letters
        codes = [app.table.item(row, "values")[2] for row in rows]
        self.assertNotIn("-", codes)  # codes are filled in at the end

    def test_huffman_errors_and_edge_cases(self):
        app = self.app
        app.notebook.select(1)
        pump(self.root, 0.05)
        app.text_var.set("")
        self.assertIn("empty", app.status_var.get())
        app.start_btn.invoke()
        self.assertEqual(app.index, -1)
        self.assertIn("empty", app.status_var.get())
        app.text_var.set("   ")
        app.start_btn.invoke()
        self.assertEqual(app.index, -1)
        app.text_var.set("abcdefghijklmnopqrstuvwxyz")
        app.start_btn.invoke()
        self.assertEqual(app.index, -1)
        self.assertIn("at most", app.status_var.get())
        app.text_var.set("AAAA")  # single symbol
        app.start_btn.invoke()
        self.go_to_end()
        self.assertIn("A=0", self.result())
        app.text_var.set("hello world 123")  # spaces and digits
        app.start_btn.invoke()
        self.go_to_end()
        self.assertIn("lossless", self.result())

    # ---------------------------------------------------------- Knapsack
    def test_knapsack_walkthrough(self):
        app = self.app
        app.notebook.select(2)
        pump(self.root, 0.05)
        self.assertEqual(len(app.items_table.get_children()), 4)  # the item table is filled before Start
        app.start_btn.invoke()
        self.go_to_end()
        self.assertIn("Best total value: 7", self.result())
        self.assertIn("1, 2", self.result())
        statuses = [app.items_table.item(row, "values")[3] for row in app.items_table.get_children()]
        self.assertEqual(statuses, ["taken", "taken", "not taken", "not taken"])
        app.prev_btn.invoke()  # back into the backtracking steps
        self.root.update()
        self.assertIn("Backtrack", self.dry())

    def test_knapsack_errors(self):
        app = self.app
        app.notebook.select(2)
        pump(self.root, 0.05)
        cases = [("2, 3, 4", "3, 4", "5", "weights but"),  # different lengths
                 ("2, -3", "3, 4", "5", "negative"),  # negative weight
                 ("2, x", "3, 4", "5", "not a whole number"),  # non-numeric
                 ("2, 3", "3, -4", "5", "negative"),  # negative value
                 ("", "3, 4", "5", "Please enter"),  # empty
                 ("2, 3", "3, 4", "0", "capacity is 0"),  # zero capacity
                 ("2, 3", "3, 4", "-5", "negative"),  # negative capacity
                 ("2, 3", "3, 4", "five", "not a whole number"),  # non-numeric capacity
                 ("2, 3", "3, 4", "", "Please enter"),  # empty capacity
                 ("0, 3", "3, 4", "5", "at least 1"),  # zero weight
                 ("2, 3", "3, 4", "26", "at most"),  # capacity just over the limit
                 ("1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1", "1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1", "5", "at most"),  # 11 items
                 ("2, 3", "3, 4", "500", "at most")]  # far too big for the table
        for weights, values, capacity, expected in cases:
            app.weights_var.set(weights)
            app.values_var.set(values)
            app.capacity_var.set(capacity)
            app.start_btn.invoke()
            self.assertEqual(app.index, -1, msg=str(weights) + "|" + capacity)
            self.assertIn(expected, app.status_var.get(), msg=str(weights) + "|" + capacity)

    def test_knapsack_heavy_item(self):
        app = self.app
        app.notebook.select(2)
        pump(self.root, 0.05)
        app.weights_var.set("10, 2")
        app.values_var.set("100, 5")
        app.capacity_var.set("5")
        app.start_btn.invoke()
        self.go_to_end()
        self.assertIn("Best total value: 5", self.result())
        self.assertIn("heavier", app.steps[1]["message"])

    def test_resizing_window_does_not_crash(self):
        app = self.app
        app.start_btn.invoke()
        self.root.geometry("1000x700")
        pump(self.root, 0.2)
        self.root.geometry("1400x900")
        pump(self.root, 0.2)
        for tab in (1, 2, 0):
            app.notebook.select(tab)
            pump(self.root, 0.05)
            app.start_btn.invoke()
            self.go_to_end()
            pump(self.root, 0.05)


class TestFormulasAndGraph(GuiBase):
    """New features: the formula / explanation sections and the Complexity Graph window."""

    def canvas_texts(self, canvas):
        found = []
        for item in canvas.find_all():
            if canvas.type(item) == "text":
                found.append(canvas.itemcget(item, "text"))
        return found

    def graph_text(self):
        return self.app.graph_text.get("1.0", "end")

    def tearDown(self):
        self.app.close_complexity_graph()  # every test starts with the graph window closed

    def test_dry_box_has_three_sections_for_every_step_of_every_algorithm(self):
        app = self.app
        for tab in (0, 1, 2):
            app.notebook.select(tab)
            pump(self.root, 0.05)
            app.start_btn.invoke()
            for number in range(len(app.steps)):
                app.index = number
                app.show_step()
                text = self.dry()
                self.assertIn("WHAT IS HAPPENING", text)
                self.assertIn("FORMULA", text)
                self.assertIn("WHY / EXPLANATION", text)
                self.assertIn(app.steps[number]["message"], text)
                self.assertIn(app.steps[number]["formula"].splitlines()[0], text)
                self.assertIn(app.steps[number]["detail"][:40], text)

    def test_before_start_the_box_explains_the_three_parts(self):
        self.assertIn("WHAT IS HAPPENING", self.dry())
        self.assertIn("FORMULA", self.dry())

    def test_knapsack_formula_is_visible_in_the_box(self):
        app = self.app
        app.notebook.select(2)
        pump(self.root, 0.05)
        app.start_btn.invoke()
        while app.steps[app.index]["cell"] != (2, 5) or app.steps[app.index]["kind"] != "cell":
            app.next_btn.invoke()
        self.assertIn("take = value_2 + dp[1][5 - 3] = 4 + dp[1][2] = 4 + 3 = 7", self.dry())
        self.assertIn("dp[2][5] = max(3, 7) = 7", self.dry())
        self.assertIn("Two options for item 2", self.dry())

    def test_formula_tag_is_used(self):
        app = self.app
        app.start_btn.invoke()
        app.next_btn.invoke()
        app.next_btn.invoke()
        tagged = app.dry_text.tag_ranges("formula")
        self.assertEqual(len(tagged), 2)  # one formula block
        self.assertIn("new = dist[", str(app.dry_text.get(tagged[0], tagged[1])))

    def test_graph_window_opens_once_and_draws_time_and_space(self):
        app = self.app
        self.assertIsNone(app.graph_window)
        app.graph_btn.invoke()
        pump(self.root, 0.3)
        first = app.graph_window
        self.assertIsNotNone(first)
        self.assertTrue(first.winfo_exists())
        app.graph_btn.invoke()  # a second press must not open a second window
        pump(self.root, 0.1)
        self.assertIs(app.graph_window, first)
        texts = self.canvas_texts(app.graph_canvas)
        joined = " | ".join(texts)
        self.assertIn("Dijkstra", joined)
        self.assertIn("Time = basic operations", joined)
        self.assertIn("Space = memory cells", joined)  # both quantities are in the same chart
        self.assertIn("count (log scale)", joined)
        self.assertIn("time = 1,800", joined)  # end label of the time line for n = 40
        self.assertIn("space = 120", joined)  # end label of the space line
        self.assertIn("Your input: V = 5 cities", joined)  # the user's own input is marked
        self.assertIn("O(V^2)", self.graph_text())
        self.assertIn("O(V)", self.graph_text())
        self.assertIn("grows x", self.graph_text())
        kinds = {}  # how many canvas items of each type were drawn
        for item in app.graph_canvas.find_all():
            kind = app.graph_canvas.type(item)
            kinds[kind] = kinds.get(kind, 0) + 1
        self.assertGreaterEqual(kinds["oval"], 20 + 1)  # 20 time markers (+1 legend marker)
        self.assertGreaterEqual(kinds["rectangle"], 20 + 1)  # 20 space markers (+1 legend marker)
        self.assertGreaterEqual(kinds["polygon"], 2 + 1)  # 2 diamonds for the user's input (+1 legend)
        self.assertGreaterEqual(kinds["line"], 2 + 4)  # the time line, the space line, axes and grid

    def test_graph_follows_the_chosen_algorithm_and_input(self):
        app = self.app
        app.graph_btn.invoke()
        pump(self.root, 0.2)
        app.notebook.select(1)
        pump(self.root, 0.2)
        self.assertIn("Huffman coding", " | ".join(self.canvas_texts(app.graph_canvas)))
        self.assertIn("n = 5 symbols", " | ".join(self.canvas_texts(app.graph_canvas)))
        self.assertIn("O(n log n)", self.graph_text())
        app.text_var.set("AABBCC")  # typing changes the marker
        pump(self.root, 0.1)
        self.assertIn("n = 3 symbols", " | ".join(self.canvas_texts(app.graph_canvas)))
        app.notebook.select(2)
        pump(self.root, 0.2)
        joined = " | ".join(self.canvas_texts(app.graph_canvas))
        self.assertIn("0/1 Knapsack", joined)
        self.assertIn("n = 4 items, W = 5", joined)
        self.assertIn("time = 28, space = 30", joined)
        self.assertIn("O(n x W)", self.graph_text())

    def test_graph_with_invalid_input_does_not_crash(self):
        app = self.app
        app.graph_btn.invoke()
        app.notebook.select(2)
        pump(self.root, 0.2)
        app.weights_var.set("x, y")  # invalid knapsack input
        pump(self.root, 0.1)
        self.assertIn("Enter a valid input", " | ".join(self.canvas_texts(app.graph_canvas)))
        self.assertNotIn("Your input (", self.graph_text())
        app.weights_var.set("2, 3, 4, 5")
        pump(self.root, 0.1)
        self.assertIn("Your input (", self.graph_text())
        app.notebook.select(0)
        pump(self.root, 0.1)
        app.clear_graph()  # empty graph
        pump(self.root, 0.1)
        self.assertIn("Enter a valid input", " | ".join(self.canvas_texts(app.graph_canvas)))
        app.notebook.select(1)
        pump(self.root, 0.1)
        app.text_var.set("")  # empty text
        pump(self.root, 0.1)
        self.assertIn("Enter a valid input", " | ".join(self.canvas_texts(app.graph_canvas)))

    def test_graph_window_close_reopen_and_resize(self):
        app = self.app
        app.graph_btn.invoke()
        pump(self.root, 0.2)
        app.graph_window.geometry("1000x800")
        pump(self.root, 0.3)
        app.graph_window.geometry("700x600")
        pump(self.root, 0.3)
        app.close_complexity_graph()
        self.assertIsNone(app.graph_window)
        app.reset()  # resetting with the window closed must be fine
        app.draw_complexity()
        app.graph_btn.invoke()  # reopen
        pump(self.root, 0.2)
        self.assertTrue(app.graph_window.winfo_exists())
        app.graph_window.destroy()  # closed with the window's own X button (bypasses our handler)
        pump(self.root, 0.1)
        app.reset()  # must notice the window is gone
        self.assertIsNone(app.graph_window)

    def test_graph_marker_for_a_larger_graph(self):
        app = self.app
        app.graph_btn.invoke()
        for name in ("F", "G", "H"):
            app.city_var.set(name)
            app.add_city()
        pump(self.root, 0.2)
        self.assertIn("V = 8 cities", " | ".join(self.canvas_texts(app.graph_canvas)))


if __name__ == "__main__":
    unittest.main(verbosity=2)
