# gui.py - ALL the Tkinter code of the Algorithm Dry Run Visualizer.
# The algorithms themselves live in dijkstra.py, huffman.py and knapsack.py (no GUI there).
# This file only: reads the inputs, asks the generators for a list of steps,
# and draws one step at a time on a Canvas.

import math  # math.cos / math.sin place the cities on a circle
import tkinter as tk  # the GUI library that ships with Python
from tkinter import ttk  # nicer widgets: Notebook (tabs), Combobox, Treeview (tables)

import complexity  # measured time / space numbers for the complexity graph
import dijkstra  # pure logic for Dijkstra
import huffman  # pure logic for Huffman coding
import knapsack  # pure logic for 0/1 knapsack

# ---------------------------------------------------------------- colours and limits
ORANGE = "#FFA726"  # the thing being worked on right now
YELLOW = "#FFEE58"  # the thing being checked / compared
LIGHT_GREEN = "#AED581"  # finished
GREEN = "#2E9E3E"  # final answer
LIGHT_BLUE = "#81D4FA"  # second comparison cell in the knapsack
GREY = "#ECEFF1"  # normal, untouched
RED = "#C62828"  # error text
BLUE = "#1565C0"  # information text and the "0" edges
DARK_GREEN = "#1B5E20"  # good-news text

MAX_CITIES = 10  # more cities would not fit nicely on the circle
MAX_CITY_NAME = 6  # longer names would not fit inside the circle
MAX_SYMBOLS = 16  # more different characters would not fit in the Huffman tree picture
MAX_ITEMS = 10  # more items would make the knapsack grid too tall
MAX_CAPACITY = 25  # larger capacity would make the knapsack grid cells too small to read

DEFAULT_ROADS = [("A", "B", 4), ("A", "C", 2), ("B", "C", 1), ("B", "D", 5),
                 ("C", "D", 8), ("C", "E", 10), ("D", "E", 2)]  # the preloaded example graph


# ---------------------------------------------------------------- small input helpers
def parse_one_int(text, what):
    """Turn text into a whole number >= 0, or raise ValueError with a friendly message."""
    text = text.strip()  # remove spaces at both ends
    if text == "":  # nothing typed
        raise ValueError("Please enter the " + what + ".")
    try:
        number = int(text)  # try to convert to a whole number
    except ValueError:  # letters, decimals, symbols ...
        raise ValueError("'" + text + "' is not a whole number. Please type a whole number for the " + what + ".")
    if number < 0:  # negative numbers are not allowed anywhere in this project
        raise ValueError("The " + what + " cannot be negative (you typed " + text + ").")
    return number


def parse_number_list(text, what):
    """Turn '2, 3 4' into [2, 3, 4], or raise ValueError with a friendly message."""
    parts = text.replace(",", " ").split()  # commas and spaces both separate numbers
    if len(parts) == 0:  # nothing typed
        raise ValueError("Please enter the " + what + " (for example 2, 3, 4, 5).")
    numbers = []  # the converted numbers
    for part in parts:  # convert one piece at a time
        numbers.append(parse_one_int(part, what))  # reuse the single-number checker
    return numbers


def parse_knapsack_input(weights_text, values_text, capacity_text):
    """Return (weights, values, capacity) or raise ValueError with a friendly message."""
    weights = parse_number_list(weights_text, "weights")  # list of weights
    values = parse_number_list(values_text, "values")  # list of values
    if len(weights) != len(values):  # every item needs both
        raise ValueError("You typed " + str(len(weights)) + " weights but " + str(len(values))
                         + " values. They must be the same number.")
    for weight in weights:
        if weight == 0:  # a weightless item would be free to take
            raise ValueError("Every weight must be at least 1.")
    capacity = parse_one_int(capacity_text, "capacity")  # the bag size
    if capacity == 0:  # nothing fits in an empty bag
        raise ValueError("The capacity is 0, so nothing can be packed. Please use a capacity of at least 1.")
    if len(weights) > MAX_ITEMS:  # keep the table readable
        raise ValueError("Please use at most " + str(MAX_ITEMS) + " items so the table fits on the screen.")
    if capacity > MAX_CAPACITY:  # keep the table readable
        raise ValueError("Please use a capacity of at most " + str(MAX_CAPACITY) + " so the table fits on the screen.")
    return weights, values, capacity


def symbol_text(symbol):
    """Show a space as the word 'space' so it is visible."""
    if symbol == " ":
        return "space"
    return symbol


# ---------------------------------------------------------------- the one and only class
class App:
    def __init__(self, root):
        self.root = root  # the main window
        self.ready = False  # becomes True once every widget exists (stops early event callbacks)
        root.title("Algorithm Dry Run Visualizer")  # window title
        width = min(1360, root.winfo_screenwidth() - 20)  # as big as is useful, but never bigger than the screen
        height = min(880, root.winfo_screenheight() - 80)  # (80 pixels are left for the task bar and title bar)
        root.geometry(str(width) + "x" + str(height))  # starting size
        root.minsize(min(1000, width), min(600, height))  # smallest allowed size

        # ----- state of the dry run
        self.algo = 0  # 0 = Dijkstra, 1 = Huffman, 2 = Knapsack
        self.steps = []  # list of all step dictionaries (this is what makes Previous Step possible)
        self.index = -1  # which step is shown; -1 means "not started"
        self.playing = False  # True while Play is running
        self.after_id = None  # id of the pending root.after() call, so Pause can cancel it
        self.graph = {}  # Dijkstra graph: {city: {neighbour: weight}}
        self.knap = None  # parsed knapsack input (weights, values, capacity) or None if invalid
        self.huff_freq = {}  # symbol frequencies of the Huffman text
        self.graph_window = None  # the Complexity Graph window (None while it is closed)
        self.graph_canvas = None  # the canvas inside that window
        self.graph_text = None  # the text box under the chart
        self.measure_cache = {}  # algorithm number -> measured points (so we measure only once)

        # ----- tkinter variables that are linked to entry boxes
        self.city_var = tk.StringVar()  # new / removed city name
        self.road_a = tk.StringVar()  # road start city
        self.road_b = tk.StringVar()  # road end city
        self.weight_var = tk.StringVar(value="1")  # road weight text
        self.src_var = tk.StringVar()  # Dijkstra source
        self.dst_var = tk.StringVar()  # Dijkstra destination
        self.text_var = tk.StringVar(value="ABRACADABRA")  # Huffman text
        self.weights_var = tk.StringVar(value="2, 3, 4, 5")  # knapsack weights
        self.values_var = tk.StringVar(value="3, 4, 5, 6")  # knapsack values
        self.capacity_var = tk.StringVar(value="5")  # knapsack capacity
        self.speed_var = tk.IntVar(value=800)  # delay between steps in ms
        self.counter_var = tk.StringVar(value="Not started")  # "Step 7 of 25"
        self.status_var = tk.StringVar(value="")  # one-line friendly message

        self.build_widgets()  # create every widget
        self.load_default_graph(reset=False)  # preload the default graph
        self.ready = True  # from now on callbacks may run
        self.reset("Welcome! Pick a tab, check the input and press Start.")  # draw the first picture
        root.protocol("WM_DELETE_WINDOW", self.on_close)  # clean up when the window is closed

    # ================================================================ building the window
    def build_widgets(self):
        """Create all the widgets once."""
        # ----- tabs: one per algorithm, each holds that algorithm's input area
        self.notebook = ttk.Notebook(self.root)  # the tab bar
        self.notebook.pack(fill="x", padx=8, pady=(8, 2))  # stretch across the top
        self.tab_dijkstra = ttk.Frame(self.notebook, padding=6)  # tab 1 page
        self.tab_huffman = ttk.Frame(self.notebook, padding=6)  # tab 2 page
        self.tab_knapsack = ttk.Frame(self.notebook, padding=6)  # tab 3 page
        self.notebook.add(self.tab_dijkstra, text="  Dijkstra (shortest path)  ")  # add the pages as tabs
        self.notebook.add(self.tab_huffman, text="  Huffman coding  ")
        self.notebook.add(self.tab_knapsack, text="  0/1 Knapsack  ")
        self.build_dijkstra_tab()  # fill each tab with its input widgets
        self.build_huffman_tab()
        self.build_knapsack_tab()
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)  # switching tabs resets

        # ----- control buttons
        bar = ttk.Frame(self.root, padding=(8, 4))  # a row for the buttons
        bar.pack(fill="x")
        self.start_btn = ttk.Button(bar, text="Start", command=self.start)  # build the steps, show step 1
        self.prev_btn = ttk.Button(bar, text="Previous Step", command=self.prev_step)  # go back one step
        self.next_btn = ttk.Button(bar, text="Next Step", command=self.next_step)  # go forward one step
        self.play_btn = ttk.Button(bar, text="Play", command=self.play)  # automatic stepping
        self.pause_btn = ttk.Button(bar, text="Pause", command=self.pause)  # stop automatic stepping
        self.reset_btn = ttk.Button(bar, text="Reset", command=self.reset_clicked)  # back to the beginning
        self.graph_btn = ttk.Button(bar, text="Complexity Graph", command=self.open_complexity_graph)  # time + space chart
        for button in (self.start_btn, self.prev_btn, self.next_btn, self.play_btn, self.pause_btn, self.reset_btn,
                       self.graph_btn):
            button.pack(side="left", padx=3)  # place them in a row
        ttk.Label(bar, text="   Delay per step (ms):").pack(side="left")  # slider caption
        self.speed_scale = tk.Scale(bar, from_=200, to=2000, resolution=100, orient="horizontal",
                                    length=220, variable=self.speed_var)  # 200 ms = fast, 2000 ms = slow
        self.speed_scale.pack(side="left", padx=4)

        # ----- one-line status / error message
        self.status_label = tk.Label(self.root, textvariable=self.status_var, anchor="w",
                                     font=("Arial", 11, "bold"), fg=BLUE)  # colour changes for errors
        self.status_label.pack(fill="x", padx=12)

        # ----- main area: canvas on the left, text panels on the right
        main = ttk.Frame(self.root, padding=8)  # holds the two columns
        main.pack(fill="both", expand=True)
        main.columnconfigure(0, weight=5)  # canvas column gets a little more room
        main.columnconfigure(1, weight=4)  # right column (formulas and explanations need width too)
        main.rowconfigure(0, weight=1)  # both grow downward
        self.canvas = tk.Canvas(main, bg="white", highlightthickness=1, highlightbackground="#90A4AE")
        self.canvas.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        self.canvas.bind("<Configure>", self.on_canvas_resize)  # redraw when the window is resized

        self.right = ttk.Frame(main)  # the right column
        right = self.right
        right.grid(row=0, column=1, sticky="nsew")
        right.columnconfigure(0, weight=1)
        right.rowconfigure(1, weight=4)  # the dry run box gets most of the extra height
        right.rowconfigure(2, weight=1)  # the side table row stretches (setup_side_table changes this for Knapsack)

        ttk.Label(right, textvariable=self.counter_var, font=("Arial", 14, "bold")).grid(row=0, column=0, sticky="w")
        dry_frame = ttk.LabelFrame(right, text="Dry run: what happens, the formula, and why", padding=4)
        dry_frame.grid(row=1, column=0, sticky="nsew", pady=4)
        dry_scroll = ttk.Scrollbar(dry_frame, orient="vertical")  # long explanations can be scrolled
        self.dry_text = tk.Text(dry_frame, height=12, width=44, wrap="word", font=("Arial", 10),
                                state="disabled", bg="#FFFDE7", yscrollcommand=dry_scroll.set)  # read-only box
        dry_scroll.config(command=self.dry_text.yview)  # link the scrollbar to the box
        dry_scroll.pack(side="right", fill="y")
        self.dry_text.pack(side="left", fill="both", expand=True)
        self.dry_text.tag_configure("heading", font=("Arial", 9, "bold"), foreground=BLUE, spacing1=2)  # small blue titles
        self.dry_text.tag_configure("body", font=("Arial", 10))  # normal sentences
        self.dry_text.tag_configure("formula", font=("Courier", 10, "bold"), background="#E3F2FD",
                                    lmargin1=6, lmargin2=18, spacing1=1)  # formulas in a light blue block

        self.table_frame = ttk.LabelFrame(right, text="Table", padding=4)  # side table (Dijkstra / Huffman)
        self.table_frame.grid(row=2, column=0, sticky="nsew", pady=4)
        table_scroll = ttk.Scrollbar(self.table_frame, orient="vertical")  # for graphs with many cities
        self.table = ttk.Treeview(self.table_frame, columns=("c1", "c2", "c3"), show="headings", height=3,
                                  yscrollcommand=table_scroll.set)
        table_scroll.config(command=self.table.yview)
        table_scroll.pack(side="right", fill="y")
        self.table.pack(side="left", fill="both", expand=True)
        self.table.tag_configure("current", background=ORANGE)  # row colours
        self.table.tag_configure("finished", background=LIGHT_GREEN)
        self.table.tag_configure("checking", background=YELLOW)
        self.table.tag_configure("final", background=GREEN, foreground="white")

        result_frame = ttk.LabelFrame(right, text="Result", padding=4)
        result_frame.grid(row=3, column=0, sticky="nsew", pady=4)
        result_scroll = ttk.Scrollbar(result_frame, orient="vertical")  # long results can be scrolled
        self.result_text = tk.Text(result_frame, height=7, width=44, wrap="word", font=("Courier", 10),
                                   state="disabled", bg="#E8F5E9", yscrollcommand=result_scroll.set)  # read-only box
        result_scroll.config(command=self.result_text.yview)
        result_scroll.pack(side="right", fill="y")
        self.result_text.pack(side="left", fill="both", expand=True)
        self.result_text.tag_configure("error", foreground=RED)  # red text for "no route"
        self.result_text.tag_configure("good", foreground=DARK_GREEN)  # green text for success

    def build_dijkstra_tab(self):
        """Input widgets for Dijkstra: add cities, add roads, choose source and destination."""
        tab = self.tab_dijkstra
        row1 = ttk.Frame(tab)  # first row: cities and roads
        row1.pack(fill="x")
        ttk.Label(row1, text="City name:").pack(side="left")
        ttk.Entry(row1, textvariable=self.city_var, width=8).pack(side="left", padx=3)
        ttk.Button(row1, text="Add city", command=self.add_city).pack(side="left")
        ttk.Button(row1, text="Remove city", command=self.remove_city).pack(side="left", padx=3)
        ttk.Label(row1, text="     Road from").pack(side="left")
        self.road_a_box = ttk.Combobox(row1, textvariable=self.road_a, width=6, state="readonly")
        self.road_a_box.pack(side="left", padx=3)
        ttk.Label(row1, text="to").pack(side="left")
        self.road_b_box = ttk.Combobox(row1, textvariable=self.road_b, width=6, state="readonly")
        self.road_b_box.pack(side="left", padx=3)
        ttk.Label(row1, text="weight").pack(side="left")
        ttk.Entry(row1, textvariable=self.weight_var, width=5).pack(side="left", padx=3)
        ttk.Button(row1, text="Add / update road", command=self.add_road).pack(side="left")

        row2 = ttk.Frame(tab)  # second row: source, destination, graph buttons
        row2.pack(fill="x", pady=(6, 0))
        ttk.Label(row2, text="Source:").pack(side="left")
        self.src_box = ttk.Combobox(row2, textvariable=self.src_var, width=6, state="readonly")
        self.src_box.pack(side="left", padx=3)
        self.src_box.bind("<<ComboboxSelected>>", self.on_input_changed)  # choosing resets the animation
        ttk.Label(row2, text="Destination:").pack(side="left", padx=(10, 0))
        self.dst_box = ttk.Combobox(row2, textvariable=self.dst_var, width=6, state="readonly")
        self.dst_box.pack(side="left", padx=3)
        self.dst_box.bind("<<ComboboxSelected>>", self.on_input_changed)
        ttk.Button(row2, text="Load default graph", command=self.load_default_graph).pack(side="left", padx=(20, 3))
        ttk.Button(row2, text="Clear graph", command=self.clear_graph).pack(side="left")
        ttk.Label(row2, text="   (Roads are two-way. To remove a city, type its name in 'City name' and press Remove city.)",
                  foreground="#546E7A").pack(side="left")

    def build_huffman_tab(self):
        """Input widgets for Huffman: one text box."""
        tab = self.tab_huffman
        ttk.Label(tab, text="Text to compress:").pack(side="left")
        ttk.Entry(tab, textvariable=self.text_var, width=50).pack(side="left", padx=6)
        ttk.Label(tab, text="(default ABRACADABRA, at most " + str(MAX_SYMBOLS) + " different characters)",
                  foreground="#546E7A").pack(side="left")
        self.text_var.trace_add("write", self.on_input_changed)  # typing resets the animation

    def build_knapsack_tab(self):
        """Input widgets for Knapsack: weights, values, capacity and a table of the items."""
        tab = self.tab_knapsack
        left = ttk.Frame(tab)  # entry fields on the left
        left.pack(side="left", anchor="n")
        ttk.Label(left, text="Weights:").grid(row=0, column=0, sticky="e", pady=1)
        ttk.Entry(left, textvariable=self.weights_var, width=28).grid(row=0, column=1, padx=4)
        ttk.Label(left, text="Values:").grid(row=1, column=0, sticky="e", pady=1)
        ttk.Entry(left, textvariable=self.values_var, width=28).grid(row=1, column=1, padx=4)
        ttk.Label(left, text="Capacity:").grid(row=2, column=0, sticky="e", pady=1)
        ttk.Entry(left, textvariable=self.capacity_var, width=8).grid(row=2, column=1, sticky="w", padx=4)
        ttk.Label(left, text="Separate numbers with commas or spaces.\nUp to " + str(MAX_ITEMS) + " items, capacity up to "
                  + str(MAX_CAPACITY) + ".", foreground="#546E7A").grid(row=3, column=0, columnspan=2, sticky="w")
        for variable in (self.weights_var, self.values_var, self.capacity_var):
            variable.trace_add("write", self.on_input_changed)  # typing resets the animation
        holder = ttk.Frame(tab)  # holds the item table and its scrollbar side by side
        holder.pack(side="left", padx=20)
        self.items_table = ttk.Treeview(holder, columns=("item", "weight", "value", "status"), show="headings", height=4)
        for name, title, width in (("item", "Item", 60), ("weight", "Weight", 70), ("value", "Value", 70),
                                   ("status", "Decision", 110)):
            self.items_table.heading(name, text=title)  # column title
            self.items_table.column(name, width=width, anchor="center")  # column width
        scrollbar = ttk.Scrollbar(holder, orient="vertical", command=self.items_table.yview)  # for more than 4 items
        self.items_table.config(yscrollcommand=scrollbar.set)  # link table and scrollbar
        self.items_table.pack(side="left")
        scrollbar.pack(side="left", fill="y")
        self.items_table.tag_configure("taken", background=LIGHT_GREEN)  # chosen items turn green

    # ================================================================ small helpers
    def show_error(self, message):
        """Show a red one-line message (no popup window)."""
        self.status_label.config(fg=RED)
        self.status_var.set(message)

    def show_info(self, message):
        """Show a blue one-line message."""
        self.status_label.config(fg=BLUE)
        self.status_var.set(message)

    def set_text(self, widget, text, tag=None):
        """Replace the text of a read-only Text widget."""
        widget.config(state="normal")  # unlock so we can edit
        widget.delete("1.0", "end")  # remove the old text
        if tag is None:
            widget.insert("end", text)
        else:
            widget.insert("end", text, tag)
        widget.config(state="disabled")  # lock again so the user cannot type in it

    def set_enabled(self, button, enabled):
        """Enable or disable a button."""
        if enabled:
            button.config(state="normal")
        else:
            button.config(state="disabled")

    def show_dry(self, step):
        """Fill the Dry run box. For a step: WHAT IS HAPPENING, FORMULA and WHY. For None: instructions."""
        box = self.dry_text
        box.config(state="normal")  # unlock so we can edit
        box.delete("1.0", "end")  # remove the old text
        if step is None:  # before Start
            box.insert("end", "Press Start to begin the dry run.\nThen use Next Step, or Play.\n\n", "body")
            box.insert("end", "Every step will show three parts:\n", "body")
            box.insert("end", "WHAT IS HAPPENING", "heading")
            box.insert("end", "  a short sentence\n", "body")
            box.insert("end", "FORMULA", "heading")
            box.insert("end", "  the formula with the real numbers filled in\n", "body")
            box.insert("end", "WHY", "heading")
            box.insert("end", "  a longer explanation of the idea behind the step\n", "body")
        else:
            box.insert("end", "WHAT IS HAPPENING\n", "heading")
            box.insert("end", step["message"] + "\n\n", "body")
            box.insert("end", "FORMULA\n", "heading")
            box.insert("end", step["formula"] + "\n\n", "formula")
            box.insert("end", "WHY / EXPLANATION\n", "heading")
            box.insert("end", step["detail"], "body")
        box.config(state="disabled")  # lock again so the user cannot type in it
        box.yview_moveto(0)  # always start reading from the top

    def clear_table(self):
        """Remove every row of the side table."""
        for row in self.table.get_children():
            self.table.delete(row)

    def on_close(self):
        """Stop any pending timer, then close the window."""
        self.stop_playing()
        self.root.destroy()

    # ================================================================ button state
    def update_buttons(self):
        """Enable only the buttons that make sense right now."""
        started = self.index >= 0  # has Start been pressed?
        at_end = started and self.index >= len(self.steps) - 1  # are we on the last step?
        self.set_enabled(self.start_btn, not self.playing)  # cannot restart while playing
        self.set_enabled(self.prev_btn, started and self.index > 0 and not self.playing)
        self.set_enabled(self.next_btn, started and not self.playing)  # still enabled at the end (shows the result again)
        self.set_enabled(self.play_btn, started and not at_end and not self.playing)
        self.set_enabled(self.pause_btn, self.playing)  # only useful while playing
        self.set_enabled(self.reset_btn, True)  # Reset is always available

    # ================================================================ events
    def on_tab_changed(self, event=None):
        """User picked another algorithm tab."""
        if not self.ready:
            return
        self.algo = self.notebook.index("current")  # 0, 1 or 2
        self.reset("Switched algorithm. Check the input and press Start.")

    def on_input_changed(self, *args):
        """Any input changed: the old animation no longer matches, so reset it."""
        if not self.ready:
            return
        self.reset("Input changed. Press Start to run the dry run again.")

    def on_canvas_resize(self, event=None):
        """Window was resized: draw the current picture again at the new size."""
        if self.ready:
            self.redraw()

    def reset_clicked(self):
        """Reset button."""
        self.reset("Reset. Press Start to begin again.")

    # ================================================================ reset
    def reset(self, message=""):
        """Forget all steps and show the starting picture for the chosen algorithm."""
        self.stop_playing()  # cancel Play
        self.steps = []  # throw away old steps
        self.index = -1  # not started
        self.counter_var.set("Not started")
        self.show_dry(None)  # instructions instead of a step
        self.set_text(self.result_text, "The result will appear here when the dry run finishes.")
        self.setup_side_table()  # right column layout for this algorithm
        problem = ""  # input problem found while preparing the first picture
        if self.algo == 1:  # Huffman
            try:
                self.huff_freq = huffman.count_frequencies(self.get_huffman_text())
            except ValueError as error:
                self.huff_freq = {}
                problem = str(error)
        if self.algo == 2:  # Knapsack
            try:
                self.knap = parse_knapsack_input(self.weights_var.get(), self.values_var.get(), self.capacity_var.get())
            except ValueError as error:
                self.knap = None
                problem = str(error)
            self.fill_items_table(None)
        self.redraw()  # first picture
        self.update_side(None)  # first table
        self.update_buttons()
        self.draw_complexity()  # keep the complexity graph window (if open) in step with the input
        if problem != "":
            self.show_error(problem)
        else:
            self.show_info(message)

    # ================================================================ Dijkstra: editing the graph
    def refresh_city_lists(self):
        """Put the current city names into every drop-down."""
        names = list(self.graph.keys())  # cities in the order they were added
        for box in (self.road_a_box, self.road_b_box, self.src_box, self.dst_box):
            box["values"] = names  # what the drop-down offers
        if self.road_a.get() not in names:  # keep valid choices, fix invalid ones
            self.road_a.set("")
        if self.road_b.get() not in names:
            self.road_b.set("")
        if self.src_var.get() not in names:
            if len(names) > 0:
                self.src_var.set(names[0])
            else:
                self.src_var.set("")
        if self.dst_var.get() not in names:
            if len(names) > 0:
                self.dst_var.set(names[-1])
            else:
                self.dst_var.set("")

    def load_default_graph(self, reset=True):
        """Replace the graph by the small example graph."""
        self.graph = {}  # start empty
        for city in ("A", "B", "C", "D", "E"):
            self.graph[city] = {}
        for a, b, weight in DEFAULT_ROADS:  # roads are two-way
            self.graph[a][b] = weight
            self.graph[b][a] = weight
        self.src_var.set("A")
        self.dst_var.set("E")
        self.refresh_city_lists()
        if reset:
            self.reset("Default graph loaded (A to E).")

    def clear_graph(self):
        """Remove every city."""
        self.graph = {}
        self.refresh_city_lists()
        self.reset("Graph cleared. Add cities and roads.")

    def add_city(self):
        """Add one city."""
        name = self.city_var.get().strip()  # what the user typed
        if name == "":
            self.show_error("Type a city name first, then press Add city.")
        elif name in self.graph:
            self.show_error("The city '" + name + "' already exists.")
        elif len(name) > MAX_CITY_NAME:
            self.show_error("Please use a short name (at most " + str(MAX_CITY_NAME) + " characters).")
        elif len(self.graph) >= MAX_CITIES:
            self.show_error("At most " + str(MAX_CITIES) + " cities, so the picture stays readable.")
        else:
            self.graph[name] = {}  # new city with no roads yet
            self.city_var.set("")  # clear the box
            self.refresh_city_lists()
            self.reset("City '" + name + "' added.")

    def remove_city(self):
        """Remove the city whose name is in the box, and every road to it."""
        name = self.city_var.get().strip()
        if name not in self.graph:
            self.show_error("To remove a city, type the name of an existing city in the 'City name' box.")
            return
        del self.graph[name]  # remove the city itself
        for city in self.graph:  # remove roads that led to it
            if name in self.graph[city]:
                del self.graph[city][name]
        self.city_var.set("")
        self.refresh_city_lists()
        self.reset("City '" + name + "' removed.")

    def add_road(self):
        """Add (or change the weight of) a two-way road."""
        a = self.road_a.get()
        b = self.road_b.get()
        if a == "" or b == "":
            self.show_error("Choose both cities for the road first.")
            return
        if a == b:
            self.show_error("A road must join two different cities.")
            return
        try:
            weight = parse_one_int(self.weight_var.get(), "road weight")  # whole number >= 0
        except ValueError as error:
            self.show_error(str(error))
            return
        self.graph[a][b] = weight  # road a -> b
        self.graph[b][a] = weight  # road b -> a (two-way)
        self.reset("Road " + a + " - " + b + " with weight " + str(weight) + " saved.")

    # ================================================================ Huffman input
    def get_huffman_text(self):
        """Return the text to compress, or raise ValueError with a friendly message."""
        text = self.text_var.get()
        if text.strip() == "":  # empty or only spaces
            raise ValueError("The text is empty. Type some text to compress.")
        if len(set(text)) > MAX_SYMBOLS:  # set() keeps one copy of each character
            raise ValueError("Please use at most " + str(MAX_SYMBOLS) + " different characters so the tree fits on the screen.")
        return text

    # ================================================================ starting and stepping
    def make_generator(self):
        """Check the input and return the right step generator (raises ValueError if the input is bad)."""
        if self.algo == 0:  # Dijkstra
            source = self.src_var.get()
            target = self.dst_var.get()
            if len(self.graph) == 0:
                raise ValueError("The graph is empty. Add some cities and roads first.")
            if source == "" or target == "":
                raise ValueError("Please choose a source and a destination city.")
            if source == target:
                raise ValueError("Source and destination are the same city. Please choose two different cities.")
            return dijkstra.dijkstra_steps(self.graph, source, target)
        if self.algo == 1:  # Huffman
            return huffman.huffman_steps(self.get_huffman_text())
        weights, values, capacity = parse_knapsack_input(self.weights_var.get(), self.values_var.get(),
                                                         self.capacity_var.get())  # Knapsack
        self.knap = (weights, values, capacity)
        return knapsack.knapsack_steps(weights, values, capacity)

    def start(self):
        """Build the whole list of steps and show step 1."""
        self.stop_playing()
        try:
            self.steps = list(self.make_generator())  # run the generator to the end and keep every step
        except ValueError as error:  # bad input: friendly message, nothing crashes
            self.steps = []
            self.index = -1
            self.show_error(str(error))
            self.update_buttons()
            return
        self.index = 0  # show the first step
        self.show_info("Dry run started. Press Next Step, or Play.")
        self.show_step()

    def next_step(self):
        """Go one step forward. On the last step, show the final result again."""
        if self.index < 0:
            return
        if self.index >= len(self.steps) - 1:  # already finished
            self.show_result(self.steps[self.index])  # show the result again
            self.show_info("The algorithm has already finished. Here is the final result again.")
            return
        self.index = self.index + 1
        self.show_step()

    def prev_step(self):
        """Go one step back (works because every step was saved in the list)."""
        if self.index <= 0:
            return
        self.index = self.index - 1
        self.show_step()

    def play(self):
        """Start automatic stepping with root.after (no threads)."""
        if self.index < 0 or self.index >= len(self.steps) - 1:
            return
        self.playing = True
        self.show_info("Playing... press Pause to stop.")
        self.update_buttons()
        self.after_id = self.root.after(self.speed_var.get(), self.tick)  # call tick() after the delay

    def tick(self):
        """One automatic step."""
        self.after_id = None
        if not self.playing:  # paused in the meantime
            return
        self.index = self.index + 1  # move forward
        self.show_step()
        if self.index >= len(self.steps) - 1:  # reached the end
            self.playing = False
            self.show_info("Finished.")
            self.update_buttons()
        else:  # schedule the next tick using the current slider value
            self.after_id = self.root.after(self.speed_var.get(), self.tick)

    def stop_playing(self):
        """Cancel the timer and clear the playing flag."""
        self.playing = False
        if self.after_id is not None:
            self.root.after_cancel(self.after_id)  # cancel the pending call
            self.after_id = None

    def pause(self):
        """Pause button."""
        self.stop_playing()
        self.show_info("Paused. Use Next Step, Previous Step or Play.")
        self.update_buttons()

    # ================================================================ showing one step
    def show_step(self):
        """Display the step number self.index everywhere."""
        step = self.steps[self.index]
        self.counter_var.set("Step " + str(self.index + 1) + " of " + str(len(self.steps)))
        self.show_dry(step)  # what happens + formula + explanation
        self.redraw()  # canvas
        self.update_side(step)  # side table
        if self.index == len(self.steps) - 1:  # last step: show the result
            if not self.playing:
                self.show_info("Last step reached. The final result is in the Result box.")
            self.show_result(step)  # (an 'unreachable' error from here replaces the line above)
        else:
            self.set_text(self.result_text, "The result will appear here when the dry run finishes.")
        self.update_buttons()

    def redraw(self):
        """Draw the current step (or the starting picture) on the canvas."""
        if self.index >= 0 and self.index < len(self.steps):
            step = self.steps[self.index]
        else:
            step = None
        if self.algo == 0:
            self.draw_dijkstra(step)
        elif self.algo == 1:
            self.draw_huffman(step)
        else:
            self.draw_knapsack(step)

    def show_result(self, step):
        """Fill the Result box from the last step."""
        if self.algo == 0:
            if step["path"] is None:  # unreachable
                self.set_text(self.result_text, "No route exists from " + self.src_var.get() + " to "
                              + self.dst_var.get() + ".\nThe two cities are not connected by any roads.", "error")
                self.show_error("Unreachable: there is no route between these two cities.")
            else:
                text = ("Shortest path:\n  " + " -> ".join(step["path"]) + "\nTotal distance: " + str(step["total"]))
                self.set_text(self.result_text, text, "good")
        elif self.algo == 1:
            pieces = []  # code table on ONE wrapped line, such as "A=0, C=100, D=101"
            for symbol in step["codes"]:
                pieces.append(symbol_text(symbol) + "=" + step["codes"][symbol])
            saved = 100.0 * (step["original_bits"] - step["compressed_bits"]) / step["original_bits"]
            text = "Codes: " + ", ".join(pieces) + "\n"
            text = text + "Encoded bits: " + step["encoded"] + "\n"
            text = text + "Original  : " + str(step["original_bits"]) + " bits (8 per character)\n"
            text = text + "Compressed: " + str(step["compressed_bits"]) + " bits (" + str(round(saved, 1)) + "% smaller)\n"
            text = text + "Decoded   : " + step["decoded"] + "\n"
            if step["lossless"]:
                text = text + "Decoded text equals the original: lossless!"
            else:
                text = text + "WARNING: decoded text differs from the original."
            self.set_text(self.result_text, text, "good")
        else:
            chosen = step["chosen"]
            if len(chosen) == 0:
                names = "none"
            else:
                names = ""
                for item in chosen:
                    if names != "":
                        names = names + ", "
                    names = names + str(item)
            text = ("Best total value: " + str(step["best_value"]) + "\nItems chosen   : " + names
                    + "\nTotal weight   : " + str(step["total_weight"]) + " (capacity " + str(self.knap[2]) + ")")
            self.set_text(self.result_text, text, "good")

    # ================================================================ side tables
    def setup_side_table(self):
        """Show the right table for the chosen algorithm."""
        if self.algo == 2:  # Knapsack has its item table in the input area instead
            self.table_frame.grid_remove()  # hide the side table
            self.right.rowconfigure(2, weight=0)  # the Result box takes the freed space
            self.right.rowconfigure(3, weight=1)
            return
        self.table_frame.grid()  # show it again
        self.right.rowconfigure(2, weight=1)  # the table stretches again
        self.right.rowconfigure(3, weight=0)
        if self.algo == 0:
            self.table_frame.config(text="Distance table")
            titles = ("City", "Distance", "Status")
        else:
            self.table_frame.config(text="Symbols, frequencies and codes")
            titles = ("Symbol", "Frequency", "Code")
        for column, title in zip(("c1", "c2", "c3"), titles):
            self.table.heading(column, text=title)  # column title
            self.table.column(column, width=100, anchor="center")  # column width

    def update_side(self, step):
        """Fill the side table for the given step (None = before Start)."""
        if self.algo == 0:
            self.update_distance_table(step)
        elif self.algo == 1:
            self.update_code_table(step)
        else:
            self.fill_items_table(step)

    def update_distance_table(self, step):
        """Rows: city, distance, status."""
        self.clear_table()
        for city in self.graph:
            if step is None:  # before Start
                self.table.insert("", "end", values=(city, "-", "not started"))
                continue
            distance = step["distance"][city]
            if distance == dijkstra.INF:
                distance_text = "infinity"
            else:
                distance_text = str(distance)
            tag = ""
            if step["path"] is not None and city in step["path"]:
                status = "on final path"
                tag = "final"
            elif city == step["current"]:
                status = "visiting now"
                tag = "current"
            elif city in step["finished"]:
                status = "finished"
                tag = "finished"
            elif step["edge"] is not None and city == step["edge"][1]:
                status = "being checked"
                tag = "checking"
            elif distance == dijkstra.INF:
                status = "not reached yet"
            else:
                status = "tentative"
            self.table.insert("", "end", values=(city, distance_text, status), tags=(tag,))

    def update_code_table(self, step):
        """Rows: symbol, frequency, code (code is known only at the end)."""
        self.clear_table()
        codes = None
        if step is not None and step["codes"] is not None:
            codes = step["codes"]
        pairs = []  # (frequency, symbol) so we can sort lowest frequency first
        for symbol in self.huff_freq:
            pairs.append((self.huff_freq[symbol], symbol))
        pairs.sort()
        for frequency, symbol in pairs:
            if codes is None:
                code_text = "-"
            else:
                code_text = codes[symbol]
            self.table.insert("", "end", values=(symbol_text(symbol), frequency, code_text))

    def fill_items_table(self, step):
        """Knapsack item table in the input area: item, weight, value, decision."""
        for row in self.items_table.get_children():
            self.items_table.delete(row)
        if self.knap is None:
            return
        weights, values, capacity = self.knap
        decisions = {}  # item number -> "taken" / "skipped" decided so far
        if step is not None and step["kind"] == "done":
            for item in range(1, len(weights) + 1):
                if item in step["chosen"]:
                    decisions[item] = "taken"
                else:
                    decisions[item] = "not taken"
        elif step is not None and step["kind"] == "backtrack":
            for earlier in self.steps[:self.index + 1]:  # every backtrack step shown so far
                if earlier["kind"] == "backtrack":
                    i, w = earlier["cell"]
                    if earlier["table"][i][w] != earlier["table"][i - 1][w]:
                        decisions[i] = "taken"
                    else:
                        decisions[i] = "not taken"
        for item in range(1, len(weights) + 1):
            text = decisions.get(item, "-")
            tag = ""
            if text == "taken":
                tag = "taken"
            self.items_table.insert("", "end", values=(item, weights[item - 1], values[item - 1], text), tags=(tag,))

    # ================================================================ drawing helpers
    def canvas_size(self):
        """Current canvas width and height (with a safe minimum before the window is shown)."""
        return max(self.canvas.winfo_width(), 400), max(self.canvas.winfo_height(), 300)

    def draw_legend(self, items, width, height):
        """Draw small coloured squares with a label along the bottom of the canvas."""
        rows = [[]]  # the legend may need more than one row if the canvas is narrow
        x = 10
        for color, text in items:
            item_width = 19 + len(text) * 6.5 + 16  # rough width of one legend entry
            if x + item_width > width - 10 and len(rows[-1]) > 0:  # does not fit: start a new row
                rows.append([])
                x = 10
            rows[-1].append((color, text))
            x = x + item_width
        y = height - 16 - 20 * (len(rows) - 1)  # first row's height so the last row sits at the bottom
        for row in rows:
            x = 10
            for color, text in row:
                self.canvas.create_rectangle(x, y - 7, x + 14, y + 7, fill=color, outline="#455A64")  # colour swatch
                label = self.canvas.create_text(x + 19, y, text=text, anchor="w", font=("Arial", 9))  # its meaning
                box = self.canvas.bbox(label)  # where the text ended up
                x = box[2] + 16  # next swatch starts after this label
            y = y + 20  # next row

    # ================================================================ drawing: Dijkstra
    def draw_dijkstra(self, step):
        """Graph on a circle. Colours follow the legend."""
        canvas = self.canvas
        canvas.delete("all")  # clear the old picture
        width, height = self.canvas_size()
        cities = list(self.graph.keys())
        if len(cities) == 0:
            canvas.create_text(width / 2, height / 2, text="The graph is empty.\nAdd cities and roads above.",
                               font=("Arial", 14), fill="#546E7A")
            return
        centre_x = width / 2  # centre of the circle
        centre_y = height / 2 - 12
        radius = min(width, height) / 2 - 75  # circle radius, leave room for labels and the legend
        if radius < 40:
            radius = 40
        positions = {}  # city -> (x, y) pixel position
        for k in range(len(cities)):
            angle = -math.pi / 2 + 2 * math.pi * k / len(cities)  # start at the top, go clockwise
            positions[cities[k]] = (centre_x + radius * math.cos(angle), centre_y + radius * math.sin(angle))

        path_edges = []  # roads of the final path
        if step is not None and step["path"] is not None:
            for k in range(len(step["path"]) - 1):
                path_edges.append(frozenset((step["path"][k], step["path"][k + 1])))
        checking = None  # road being checked now
        if step is not None and step["edge"] is not None:
            checking = frozenset(step["edge"])

        drawn = []  # roads already drawn (each road is stored under both cities)
        for a in cities:
            for b in self.graph[a]:
                road = frozenset((a, b))
                if road in drawn:
                    continue
                drawn.append(road)
                x1, y1 = positions[a]
                x2, y2 = positions[b]
                colour = "#78909C"  # normal road
                line_width = 2
                if road in path_edges:  # final path: thick green
                    colour = GREEN
                    line_width = 7
                elif road == checking:  # being checked: yellow
                    colour = "#FBC02D"
                    line_width = 6
                canvas.create_line(x1, y1, x2, y2, fill=colour, width=line_width)
                label = canvas.create_text((x1 + x2) / 2, (y1 + y2) / 2, text=str(self.graph[a][b]),
                                           font=("Arial", 11, "bold"), fill="#263238")  # weight label
                box = canvas.bbox(label)
                backing = canvas.create_rectangle(box[0] - 2, box[1], box[2] + 2, box[3], fill="white", outline="")
                canvas.tag_lower(backing, label)  # white backing so the number is easy to read

        for city in cities:  # draw the cities on top of the roads
            x, y = positions[city]
            fill = GREY
            if step is not None:
                if step["path"] is not None and city in step["path"]:
                    fill = GREEN
                elif city == step["current"]:
                    fill = ORANGE
                elif city in step["finished"]:
                    fill = LIGHT_GREEN
                elif step["edge"] is not None and city == step["edge"][1]:
                    fill = YELLOW
            canvas.create_oval(x - 24, y - 24, x + 24, y + 24, fill=fill, outline="#37474F", width=2)
            canvas.create_text(x, y, text=city, font=("Arial", 13, "bold"))
            if step is not None:  # tentative distance under the city
                distance = step["distance"][city]
                if distance == dijkstra.INF:
                    distance_text = "d = inf"
                else:
                    distance_text = "d = " + str(distance)
                label = canvas.create_text(x, y + 36, text=distance_text, font=("Arial", 10), fill="#37474F")
                box = canvas.bbox(label)
                backing = canvas.create_rectangle(box[0] - 2, box[1], box[2] + 2, box[3], fill="white", outline="")
                canvas.tag_lower(backing, label)  # white backing so roads do not cut through the text
        self.draw_legend([(ORANGE, "Current city"), (LIGHT_GREEN, "Finished city"),
                          (YELLOW, "Road / neighbour being checked"), (GREEN, "Final path")], width, height)

    # ================================================================ drawing: Huffman
    def layout_tree(self, node, depth, slots, positions, nodes, edges):
        """Give every node an x slot and a depth. Leaves get the next free slot; a parent sits between its children."""
        if node["left"] is None:  # leaf
            x = slots[0]
            slots[0] = slots[0] + 1  # next leaf goes one slot to the right
        else:  # merged node
            left_x = self.layout_tree(node["left"], depth + 1, slots, positions, nodes, edges)
            right_x = self.layout_tree(node["right"], depth + 1, slots, positions, nodes, edges)
            x = (left_x + right_x) / 2  # centred above its two children
            edges.append((node["id"], node["left"]["id"], "0"))  # left edge is 0
            edges.append((node["id"], node["right"]["id"], "1"))  # right edge is 1
        positions[node["id"]] = (x, depth)
        nodes.append(node)
        return x

    def draw_huffman(self, step):
        """Draw every tree of the current list of nodes."""
        canvas = self.canvas
        canvas.delete("all")
        width, height = self.canvas_size()
        if step is None:
            canvas.create_text(width / 2, height / 2, text="Press Start to build the Huffman tree.\n"
                               "Each step merges the two lowest-frequency nodes.", font=("Arial", 14),
                               fill="#546E7A", justify="center")
            return
        positions = {}  # node id -> (slot x, depth)
        nodes = []  # every node to draw
        edges = []  # (parent id, child id, "0" or "1")
        slots = [0]  # a one-item list so the recursive function can change it
        for tree in step["nodes"]:  # lay out each tree one after another
            self.layout_tree(tree, 0, slots, positions, nodes, edges)
            slots[0] = slots[0] + 0.6  # small gap between trees
        total_slots = max(slots[0] - 0.6, 1)
        max_depth = 0
        for node_id in positions:
            if positions[node_id][1] > max_depth:
                max_depth = positions[node_id][1]
        slot_width = min(85, (width - 30) / total_slots)  # pixels per slot
        left_margin = (width - slot_width * total_slots) / 2  # centre the whole drawing
        row_height = min(85, (height - 110) / (max_depth + 1))  # pixels per level
        radius = max(12, min(22, slot_width / 2 - 3))  # node size
        font_size = 10
        if radius < 18:
            font_size = 8
        pixel = {}  # node id -> (x, y) in pixels
        for node_id in positions:
            slot_x, depth = positions[node_id]
            pixel[node_id] = (left_margin + (slot_x + 0.5) * slot_width, 40 + depth * row_height)

        picked_ids = []  # the two lowest nodes chosen in this step
        if step["picked"] is not None:
            for node in step["picked"]:
                picked_ids.append(node["id"])
        merged_id = -1  # the new node created in this step
        if step["merged"] is not None:
            merged_id = step["merged"]["id"]

        for parent_id, child_id, bit in edges:  # edges first, so nodes are drawn on top
            px, py = pixel[parent_id]
            cx, cy = pixel[child_id]
            canvas.create_line(px, py, cx, cy, width=2, fill="#78909C")
            colour = BLUE
            offset = -9
            if bit == "1":
                colour = RED
                offset = 9
            canvas.create_text((px + cx) / 2 + offset, (py + cy) / 2, text=bit, fill=colour,
                               font=("Arial", 12, "bold"))  # 0 on left edges, 1 on right edges

        for node in nodes:
            x, y = pixel[node["id"]]
            fill = GREY
            if node["symbol"] is not None and step["kind"] == "done":
                fill = LIGHT_GREEN  # leaves with final codes
            if node["id"] in picked_ids:
                fill = ORANGE
            if node["id"] == merged_id:
                fill = YELLOW
            canvas.create_oval(x - radius, y - radius, x + radius, y + radius, fill=fill, outline="#37474F", width=2)
            if node["symbol"] is not None:  # leaf: symbol over frequency
                canvas.create_text(x, y, text=symbol_text(node["symbol"])[:5] + "\n" + str(node["freq"]),
                                   font=("Arial", font_size, "bold"), justify="center")
                if step["codes"] is not None:  # final code under the leaf
                    code_font = 9
                    if slot_width < 55:  # narrow slots: smaller digits so neighbours do not touch
                        code_font = 7
                    canvas.create_text(x, y + radius + 11, text=step["codes"][node["symbol"]],
                                       font=("Courier", code_font, "bold"), fill=DARK_GREEN)
            else:  # merged node: only the frequency
                canvas.create_text(x, y, text=str(node["freq"]), font=("Arial", font_size, "bold"))
        self.draw_legend([(ORANGE, "Two lowest picked"), (YELLOW, "New merged node"),
                          (LIGHT_GREEN, "Leaf with its final code"), (BLUE, "0 = left edge"), (RED, "1 = right edge")],
                         width, height)

    # ================================================================ drawing: Knapsack
    def draw_knapsack(self, step):
        """DP table as a grid of cells."""
        canvas = self.canvas
        canvas.delete("all")
        width, height = self.canvas_size()
        if self.knap is None:
            canvas.create_text(width / 2, height / 2, text="Fix the input above to see the table.",
                               font=("Arial", 14), fill=RED)
            return
        weights, values, capacity = self.knap
        n = len(weights)
        left = 130  # room for the row labels
        top = 62  # room for the header
        cell_w = min(64, (width - left - 15) / (capacity + 1))
        cell_h = min(42, (height - top - 70) / (n + 1))
        font_size = 11  # shrink the numbers when the cells are narrow
        if cell_w < 40:
            font_size = 9
        if cell_w < 26:
            font_size = 7
        table = []  # the DP table; None = not computed yet
        if step is None:
            for i in range(n + 1):
                table.append([None] * (capacity + 1))
        else:
            table = step["table"]
        path = []  # backtracking cells
        if step is not None:
            path = step["path"]

        canvas.create_text(10, 14, anchor="w", font=("Arial", 11, "bold"),
                           text="dp[i][w] = best value using the first i items with capacity w")
        canvas.create_text(left, 36, anchor="w", font=("Arial", 10), text="capacity w  ->")
        for w in range(capacity + 1):  # column headers
            canvas.create_text(left + w * cell_w + cell_w / 2, top - 11, text=str(w),
                               font=("Arial", max(font_size, 8), "bold"))
        for i in range(n + 1):  # row labels (always readable size, even when the cells are small)
            if i == 0:
                label = "i=0: no items"
            else:
                label = "i=" + str(i) + ": w=" + str(weights[i - 1]) + " v=" + str(values[i - 1])
            canvas.create_text(left - 8, top + i * cell_h + cell_h / 2, text=label, anchor="e",
                               font=("Arial", 10))
        for i in range(n + 1):  # the cells
            for w in range(capacity + 1):
                fill = "white"
                if table[i][w] is None:
                    fill = "#EEEEEE"  # not computed yet
                if (i, w) in path:
                    fill = LIGHT_GREEN
                if step is not None:
                    if step["skip_cell"] == (i, w):
                        fill = YELLOW  # 'skip' option: the cell above
                    if step["take_cell"] == (i, w):
                        fill = LIGHT_BLUE  # 'take' option: the cell up-left
                    if step["cell"] == (i, w):
                        fill = ORANGE  # the cell being computed
                x0 = left + w * cell_w
                y0 = top + i * cell_h
                canvas.create_rectangle(x0, y0, x0 + cell_w, y0 + cell_h, fill=fill, outline="#90A4AE")
        if len(path) >= 2:  # green line along the backtracking path (drawn under the numbers)
            points = []
            for i, w in path:
                points.append(left + w * cell_w + cell_w / 2)
                points.append(top + i * cell_h + cell_h / 2)
            canvas.create_line(*points, fill=GREEN, width=4, arrow="last")
        for i in range(n + 1):  # numbers last, so the line never hides them
            for w in range(capacity + 1):
                if table[i][w] is not None:
                    canvas.create_text(left + w * cell_w + cell_w / 2, top + i * cell_h + cell_h / 2,
                                       text=str(table[i][w]), font=("Arial", font_size, "bold"))
        self.draw_legend([(ORANGE, "Cell being computed"), (YELLOW, "Skip = value above"),
                          (LIGHT_BLUE, "Take = value + dp[i-1][w-weight]"), (GREEN, "Backtracking path")],
                         width, height)

    # ================================================================ Complexity Graph window
    def open_complexity_graph(self):
        """Open (or bring to the front) the window with the time + space chart of the chosen algorithm."""
        if self.graph_window is not None and self.graph_window.winfo_exists():
            self.graph_window.lift()  # already open: just show it
            self.draw_complexity()
            return
        window = tk.Toplevel(self.root)  # a second window
        window.title("Time and Space Complexity Graph")
        window.geometry("880x720")
        window.minsize(660, 560)
        self.graph_window = window
        self.graph_text = tk.Text(window, height=11, wrap="word", font=("Arial", 10), state="disabled",
                                  bg="#FAFAFA")  # explanation under the chart
        self.graph_text.pack(side="bottom", fill="x", padx=8, pady=(0, 8))
        self.graph_text.tag_configure("heading", font=("Arial", 10, "bold"), foreground=BLUE)
        self.graph_text.tag_configure("mono", font=("Courier", 10), background="#E3F2FD")
        self.graph_text.tag_configure("body", font=("Arial", 10))
        self.graph_canvas = tk.Canvas(window, bg="white", highlightthickness=1, highlightbackground="#90A4AE")
        self.graph_canvas.pack(side="top", fill="both", expand=True, padx=8, pady=8)
        self.graph_canvas.bind("<Configure>", self.on_graph_resize)  # redraw when the window is resized
        window.protocol("WM_DELETE_WINDOW", self.close_complexity_graph)
        self.draw_complexity()

    def close_complexity_graph(self):
        """Close the graph window and forget it."""
        if self.graph_window is not None:
            self.graph_window.destroy()
        self.graph_window = None
        self.graph_canvas = None
        self.graph_text = None

    def on_graph_resize(self, event=None):
        """The graph window was resized: draw again."""
        self.draw_complexity()

    def graph_x(self, n, left, plot_width, max_n):
        """Pixel x of input size n (linear scale)."""
        return left + plot_width * n / max_n

    def graph_y(self, value, top, plot_height, powers):
        """Pixel y of a count (logarithmic scale: every power of 10 is one equal step)."""
        if value < 1:  # log of 0 is undefined, so show 0 as 1
            value = 1
        return top + plot_height - plot_height * math.log10(value) / powers

    def draw_complexity(self):
        """Draw time and space of the chosen algorithm in ONE chart. Does nothing if the window is closed."""
        if self.graph_window is None:
            return
        if not self.graph_window.winfo_exists():  # the user closed it with the window button
            self.graph_window = None
            return
        canvas = self.graph_canvas
        canvas.delete("all")
        width = max(canvas.winfo_width(), 520)
        height = max(canvas.winfo_height(), 320)
        algo = self.algo
        info = complexity.INFO[algo]
        if algo not in self.measure_cache:  # measure each algorithm only once
            self.measure_cache[algo] = complexity.measure(algo)
        points = self.measure_cache[algo]  # list of (n, operations, memory cells)
        mine = complexity.current_point(algo, self.graph, self.src_var.get(), self.text_var.get(), self.knap)

        left = 80  # room for the y labels
        right = 30
        top = 78  # room for the title and the legend
        bottom = 80  # room for the x labels
        plot_width = width - left - right
        plot_height = height - top - bottom
        biggest = 10  # largest number on the chart
        for n, time_cost, space_cost in points:
            biggest = max(biggest, time_cost, space_cost)
        max_n = points[-1][0]
        if mine is not None:
            biggest = max(biggest, mine[1], mine[2])
            max_n = max(max_n, mine[0])
        powers = 1  # the y axis goes from 10^0 = 1 up to 10^powers
        while 10 ** powers < biggest:
            powers = powers + 1

        time_colour = "#D84315"  # time: deep orange, solid line, circles
        space_colour = "#1565C0"  # space: blue, dashed line, squares
        mine_colour = "#2E7D32"  # your input: green diamonds

        canvas.create_text(width / 2, 20, text=info["name"] + ": time and space growth (counted while the algorithm runs)",
                           font=("Arial", 13, "bold"))
        # legend (colour AND shape AND line style, so it can be read without colours)
        canvas.create_line(left, 48, left + 34, 48, fill=time_colour, width=3)
        canvas.create_oval(left + 13, 44, left + 21, 52, fill=time_colour, outline=time_colour)
        canvas.create_text(left + 42, 48, text="Time = basic operations", anchor="w", font=("Arial", 10))
        canvas.create_line(left + 210, 48, left + 244, 48, fill=space_colour, width=3, dash=(6, 4))
        canvas.create_rectangle(left + 223, 44, left + 231, 52, fill=space_colour, outline=space_colour)
        canvas.create_text(left + 252, 48, text="Space = memory cells", anchor="w", font=("Arial", 10))
        canvas.create_polygon(left + 400, 48, left + 406, 42, left + 412, 48, left + 406, 54, fill=mine_colour,
                              outline=mine_colour)
        canvas.create_text(left + 420, 48, text="Your input", anchor="w", font=("Arial", 10))

        # grid lines and y labels: 1, 10, 100, 1,000 ...
        for k in range(powers + 1):
            y = self.graph_y(10 ** k, top, plot_height, powers)
            canvas.create_line(left, y, left + plot_width, y, fill="#CFD8DC")
            canvas.create_text(left - 8, y, text=format(10 ** k, ","), anchor="e", font=("Arial", 9))
        # x labels
        for n in range(0, max_n + 1, 10):
            x = self.graph_x(n, left, plot_width, max_n)
            canvas.create_line(x, top, x, top + plot_height, fill="#ECEFF1")
            canvas.create_text(x, top + plot_height + 12, text=str(n), font=("Arial", 9))
        canvas.create_line(left, top, left, top + plot_height, fill="#37474F", width=2)  # y axis
        canvas.create_line(left, top + plot_height, left + plot_width, top + plot_height, fill="#37474F", width=2)  # x axis
        canvas.create_text(left + plot_width / 2, height - 28, text=info["x_label"], font=("Arial", 9),
                           width=plot_width, justify="center")
        canvas.create_text(20, top + plot_height / 2, text="count (log scale)", angle=90, font=("Arial", 10))

        # the two measured lines
        time_coords = []
        space_coords = []
        for n, time_cost, space_cost in points:
            x = self.graph_x(n, left, plot_width, max_n)
            time_coords.append(x)
            time_coords.append(self.graph_y(time_cost, top, plot_height, powers))
            space_coords.append(x)
            space_coords.append(self.graph_y(space_cost, top, plot_height, powers))
        canvas.create_line(*space_coords, fill=space_colour, width=3, dash=(6, 4))
        canvas.create_line(*time_coords, fill=time_colour, width=3)
        for k in range(0, len(time_coords), 2):  # markers on every measured point
            canvas.create_oval(time_coords[k] - 4, time_coords[k + 1] - 4, time_coords[k] + 4, time_coords[k + 1] + 4,
                               fill=time_colour, outline="white")
            canvas.create_rectangle(space_coords[k] - 4, space_coords[k + 1] - 4, space_coords[k] + 4,
                                    space_coords[k + 1] + 4, fill=space_colour, outline="white")
        last_n, last_time, last_space = points[-1]  # value labels at the right end of the lines
        canvas.create_text(time_coords[-2] - 8, time_coords[-1] - 10, text="time = " + format(last_time, ","),
                           anchor="se", fill=time_colour, font=("Arial", 10, "bold"))
        canvas.create_text(space_coords[-2] - 8, space_coords[-1] + 10, text="space = " + format(last_space, ","),
                           anchor="ne", fill=space_colour, font=("Arial", 10, "bold"))

        # the user's own input
        if mine is not None:
            my_n, my_time, my_space, my_text = mine
            x = self.graph_x(my_n, left, plot_width, max_n)
            canvas.create_line(x, top, x, top + plot_height, fill=mine_colour, dash=(3, 3), width=2)
            for value in (my_time, my_space):
                y = self.graph_y(value, top, plot_height, powers)
                canvas.create_polygon(x - 7, y, x, y - 7, x + 7, y, x, y + 7, fill=mine_colour, outline="white")
            label = canvas.create_text(x + 8, top + 10, anchor="nw", fill=mine_colour, font=("Arial", 10, "bold"),
                                       text="Your input: " + my_text + "\ntime = " + format(my_time, ",")
                                       + ", space = " + format(my_space, ","))
            box = canvas.bbox(label)
            if box[2] > left + plot_width:  # would stick out on the right: move it to the left side of the line
                canvas.coords(label, x - 8, top + 10)
                canvas.itemconfig(label, anchor="ne")
                box = canvas.bbox(label)
            backing = canvas.create_rectangle(box[0] - 3, box[1] - 2, box[2] + 3, box[3] + 2, fill="white", outline="")
            canvas.tag_lower(backing, label)
        else:
            canvas.create_text(left + plot_width / 2, top + 14, text="Enter a valid input to see your own point on the chart.",
                               fill="#546E7A", font=("Arial", 10, "italic"))

        # explanation under the chart
        data = {}
        for n, time_cost, space_cost in points:
            data[n] = (time_cost, space_cost)
        growth = ""
        if 20 in data and 40 in data:  # measured growth when n doubles
            growth = ("Measured: when n doubles from 20 to 40, time grows x" + str(round(data[40][0] / data[20][0], 1))
                      + " and space grows x" + str(round(data[40][1] / data[20][1], 1))
                      + " (about x2 means linear, about x4 means quadratic).\n")
        box = self.graph_text
        box.config(state="normal")
        box.delete("1.0", "end")
        box.insert("end", "Time: " + info["time_big_o"] + "\n", "heading")
        box.insert("end", info["time_formula"] + "\n", "mono")
        box.insert("end", "Space: " + info["space_big_o"] + "\n", "heading")
        box.insert("end", info["space_formula"] + "\n", "mono")
        box.insert("end", "How to read the chart\n", "heading")
        box.insert("end", "Time and space are drawn together in ONE chart. The vertical axis is logarithmic: each gridline is "
                          "10 times bigger than the one below it, so both small and large numbers fit. The numbers are not "
                          "taken from a textbook curve: the program really ran the algorithm on inputs of size 2, 4, 6 ... 40 "
                          "and counted the work. " + growth + info["note"] + "\n", "body")
        if mine is not None:
            box.insert("end", "Your input (" + mine[3] + ") needs " + format(mine[1], ",") + " operations and "
                              + format(mine[2], ",") + " memory cells (green diamonds).", "body")
        box.config(state="disabled")
