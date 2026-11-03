# Algorithm Dry Run Visualizer

A Tkinter program that shows **Dijkstra's shortest path**, **Huffman coding** and **0/1 Knapsack (dynamic programming)** one small step at a time, like a dry run on paper. Built for a DAA mini project and a live viva.

Every step shows three things: **what is happening**, the **formula with the real numbers filled in**, and a **detailed explanation of why**. A separate **Complexity Graph** window draws the **time and space** of the chosen algorithm together in one chart.

* Python 3.10+, **only Tkinter and the standard library** (no networkx, no matplotlib; everything, including the graph, is drawn on a Tkinter `Canvas`).
* Logic and GUI are strictly separate: the algorithm files contain no GUI code.

---

## 1. How to run

```
python main.py
```

Tkinter ships with Python on Windows and macOS. On Linux you may need to install it once:

```
sudo apt install python3-tk        # Debian / Ubuntu
```

Run the tests (no window needed):

```
python test_algorithms.py
```

Optional extra: `python test_gui.py` drives the real window by "pressing" its buttons from code. It needs a display (on a Linux machine without a screen: `xvfb-run -a python test_gui.py`).

### Files

| File | What it does |
|---|---|
| `dijkstra.py` | Pure logic: `dijkstra()` (final answer), `dijkstra_steps()` (step generator), `dijkstra_cost()` (counts work for the graph) |
| `huffman.py` | Pure logic: `huffman_coding()`, `huffman_steps()`, `huffman_cost()` |
| `knapsack.py` | Pure logic: `knapsack()`, `knapsack_steps()`, `knapsack_cost()` |
| `complexity.py` | Pure logic (new): builds sample inputs of size 2, 4, ... 40, runs the `*_cost()` functions and returns the numbers for the chart, plus the big-O text |
| `gui.py` | All Tkinter code: one `App` class |
| `main.py` | Entry point |
| `test_algorithms.py` | Tests with no GUI (39 tests) |
| `test_gui.py` | Optional: drives the real window (23 tests) |

### How the program works (good to say in the viva)

1. Each `*_steps` function is a **generator**: it runs the algorithm and `yield`s one dictionary per step. Every dictionary has a short `"message"`, a `"formula"` (numbers filled in), a longer `"detail"` explanation, plus the data needed to draw that moment (tables, current cell, and so on).
2. When you press **Start**, the GUI runs the generator to the end with `list(...)` and keeps all steps in `self.steps`.
3. **Next Step** / **Previous Step** just change `self.index` and draw `self.steps[self.index]`. That is why going backwards is easy.
4. **Play** uses `root.after(delay, self.tick)`: each tick moves one step forward and schedules the next tick. **Pause** cancels the scheduled call. No threads.
5. The normal functions (`dijkstra()`, `huffman_coding()`, `knapsack()`) are written separately from the generators, and the tests check that both give the same answer.
6. The **Complexity Graph** does not draw a textbook curve. `complexity.py` really runs the algorithm on inputs of growing size and counts basic operations (time) and memory cells (space); `gui.py` only draws those numbers.

---

## 2. How to use each dry run

### Controls (same for every algorithm)

| Button | Meaning |
|---|---|
| **Start** | Checks the input, builds all steps, shows step 1 |
| **Next Step** / **Previous Step** | Move one step forward / back |
| **Play** / **Pause** | Move forward automatically / stop |
| **Reset** | Back to "not started" (the input stays) |
| **Complexity Graph** | Opens the time + space chart of the chosen algorithm in its own window |
| **Delay slider** | 200 ms (fast) to 2000 ms (slow) between steps while playing |

The right side shows **Step k of N**, the **Dry run** box, a table, and the **Result** box (filled on the last step). Changing any input, or switching tab, resets the animation. Pressing **Next Step** after the last step shows the final result again. Mistakes in the input show a red message under the buttons (no popup windows).

### The Dry run box (three parts for every step)

| Part | What it contains |
|---|---|
| **WHAT IS HAPPENING** | One short plain-English sentence |
| **FORMULA** | The formula of this step with the real numbers filled in (light blue block) |
| **WHY / EXPLANATION** | A longer explanation of the idea behind the step and what the numbers mean |

The box has a scroll bar for long explanations.

### Dijkstra (tab 1)

1. A small graph (A to E) is preloaded: source A, destination E. Press **Start** to run it immediately.
2. To make your own graph: type a name in *City name* and press **Add city** (**Remove city** removes the name in the box). Choose two cities in *Road from / to*, type a weight, press **Add / update road** (roads are two-way). Pick *Source* and *Destination*. **Load default graph** and **Clear graph** are also there.
3. Colours: **orange** = city being visited, **light green** = finished city, **yellow** = road / neighbour being checked, **thick green** = final shortest path. Under each city is its current distance `d`. The table on the right shows *city, distance, status*.

### Huffman (tab 2)

1. Default text `ABRACADABRA`. Type any text (up to 16 different characters so the tree fits).
2. The picture shows every tree in the current list of nodes. Each step merges the two lowest-frequency nodes: they turn **orange**, the new parent is **yellow**. Left edges are labelled **0** (blue), right edges **1** (red).
3. On the last step the leaves show their final codes, the table on the right shows the code table, and the Result box shows the encoded bits, original vs compressed size, and the decoded text (to prove it is lossless).

### Knapsack (tab 3)

1. Defaults: weights `2, 3, 4, 5`, values `3, 4, 5, 6`, capacity `5`. Type numbers separated by commas or spaces (up to 10 items, capacity up to 25). The item table fills in as you type.
2. The grid is the DP table: rows = items `i` (0 to n), columns = capacity `w` (0 to W). Grey cells are not computed yet.
3. Colours: **orange** = cell being computed, **yellow** = "skip" cell (the value above), **blue** = "take" cell (`dp[i-1][w-weight]`), **green** = backtracking path. After the table is full, the backtracking steps decide each item, and the item table shows *taken / not taken*.

### The Complexity Graph window

Press **Complexity Graph** (any tab). It shows the algorithm of the current tab and follows you when you switch tab or change the input.

* **One chart, two lines:** **time** (red line, circles) = number of basic operations, **space** (blue dashed line, squares) = number of extra memory cells. The shapes and the dash style mean it can be read in black and white too.
* **Vertical axis is logarithmic:** each gridline is 10 times bigger than the one below, so small and large numbers fit in one picture.
* **Horizontal axis** is the input size `n`: 2, 4, 6, ... 40 (what `n` means for each algorithm is written under the chart).
* **Green diamonds** mark *your own input* (for example your graph with V = 5). They are measured the same way. For Knapsack the sample line uses capacity `W = n`, so the diamond can sit off the line when your `W` is different.
* The text under the chart gives the big-O, the formula that was counted, and the measured growth when `n` doubles from 20 to 40 (about x2 means linear, about x4 means quadratic).

What is counted:

| Algorithm | Time = operations counted | Space = cells counted |
|---|---|---|
| Dijkstra (simple scan version) | one per city looked at while searching for the closest city (`V` per round) + one per road checked (`2E`) | `3V`: distance table + previous table + finished list |
| Huffman | one per character counted + list size at every merge + tree walk + one per character encoded | `(2n - 1)` tree nodes + `n` frequencies + `n` codes |
| Knapsack | one per DP cell computed (`n x (W + 1)`) + `n` backtracking moves | `(n + 1) x (W + 1)` DP table cells |

Measured values from this program (sample inputs):

| n | Dijkstra time | Dijkstra space | Huffman time | Huffman space | Knapsack time | Knapsack space |
|---|---|---|---|---|---|---|
| 5 | 50 | 15 | 55 | 19 | 35 | 36 |
| 10 | 150 | 30 | 139 | 39 | 120 | 121 |
| 20 | 500 | 60 | 388 | 79 | 440 | 441 |
| 40 | 1,800 | 120 | 1,178 | 159 | 1,680 | 1,681 |

Dijkstra and Knapsack time grow about 4 times when `n` doubles (quadratic), while Dijkstra and Huffman space only double (linear). Knapsack time and space are both about `n x W`, so its two lines almost overlap. Huffman time here grows like `n^2` because the simple version re-scans a list at every merge; with a heap it is `O(n log n)`.

---

## 3. What each step means (with the formulas)

### Dijkstra

| Step type | Formula shown | Meaning |
|---|---|---|
| **Start** | `dist[source] = 0`, `dist[other] = infinity` | The source costs 0; every other city is "not reached yet". |
| **Visiting X** | `u = the unfinished city with the smallest dist` | Among unfinished cities, X is the closest. Nothing shorter can ever be found (weights are 0 or more), so X's distance is **final**. |
| **Checking neighbour Y** | `new = dist[u] + weight(u,v)`; `if new < dist[v]: dist[v] = new, previous[v] = u` | Would going through X give a shorter route to Y? If yes, update the distance and remember X as Y's parent (this is called *relaxing* the road); otherwise keep the old distance. |
| **Finished** | `total = w1 + w2 + ... = dist[target]` | The path is rebuilt by following `previous` from the destination back to the source. |

A detailed step (what the Dry run box shows):

**Formula**

```
new = dist[C] + weight(C,B) = 2 + 1 = 3
is new < dist[B]?  3 < 4  YES
dist[B] = 3,  previous[B] = C
```

**Explanation:** We stand on C (final distance 2). The road C-B has weight 1. Going from the source to C and then along this road reaches B with total cost 3. The best route to B known until now costs 4. 3 is smaller, so we have found a shorter route: we store the new distance and remember that B is reached through C (this is how the path can be rebuilt at the end). This 'try to improve a neighbour' action is called RELAXING the edge.

### Huffman

| Step type | Formula shown | Meaning |
|---|---|---|
| **Start** | `frequency[c]`, `merges needed = n - 1` | Count how often each character appears. Each character becomes a node `symbol:frequency`. |
| **Pick the two lowest and merge** | `new.freq = a.freq + b.freq`; `nodes left = n - merges` | Take the two smallest, make a parent whose frequency is their sum. Smaller goes left (edge 0), other goes right (edge 1). Rare symbols sink deep (long codes). The running "sum of all merged frequencies" ends equal to the compressed size in bits. |
| **Tree complete** | `original = 8 x length`; `compressed = sum(frequency x code length)`; `saved = (original - compressed) / original` | Read each code from the root (left = 0, right = 1). Decoding the bits with the same tree gives back the text, so it is lossless. |

A detailed step:

**Formula**

```
CD.freq = C.freq + D.freq = 1 + 1 = 2
merge 1 of 4   nodes left = n - merges = 5 - 1 = 4
sum of all merged frequencies so far = 2
```

**Explanation:** The list before this step, lowest first: C:1, D:1, B:2, R:2, A:5. The two smallest frequencies are 1 (C) and 1 (D), so these are the rarest parts. We join them under a new parent CD with frequency 2. The smaller node is placed on the left edge (bit 0) and the other on the right edge (bit 1). Because the rarest symbols are merged first, they sink deepest in the tree and get the longest codes. Useful fact: the compressed size in bits equals the sum of all merged frequencies, which is 2 so far.

### Knapsack

| Step type | Formula shown | Meaning |
|---|---|---|
| **Start** | `dp[0][w] = 0`; `if weight_i > w: dp[i][w] = dp[i-1][w]`; otherwise `dp[i][w] = max(dp[i-1][w], value_i + dp[i-1][w - weight_i])` | Row 0 means "no items", so the best value is 0. |
| **Item i, capacity w** | `skip = dp[i-1][w]`; `take = value_i + dp[i-1][w - weight_i]`; `dp[i][w] = max(skip, take)` | **Skip** = value above. **Take** = gain the item's value but lose its weight from the capacity, then use the best value for what is left. The bigger one is stored (on a tie we skip). |
| **Item too heavy** | `weight_i > w  ->  dp[i][w] = dp[i-1][w]` | Only "skip" is possible. |
| **Backtrack** | `dp[i][w] != dp[i-1][w]  ->  item i TAKEN, w = w - weight_i` | Start at the bottom-right cell. If the value differs from the cell above, item `i` was taken: subtract its weight and move up. Otherwise it was skipped. |
| **Finished** | `value = v1 + v2 + ...`; `weight = w1 + w2 + ... <= capacity` | The chosen items, their total value and total weight. |

A detailed step:

**Formula**

```
item 2: weight_2 = 3, value_2 = 4    capacity w = 5
skip = dp[1][5] = 3
take = value_2 + dp[1][5 - 3] = 4 + dp[1][2] = 4 + 3 = 7
dp[2][5] = max(3, 7) = 7
```

**Explanation:** Two options for item 2 with capacity 5. SKIP: do not pack it, so the best value is the one already found for the first item with capacity 5: dp[1][5] = 3 (the cell above). TAKE: pack it, gaining 4, but it uses 3 of the capacity, so only 5 - 3 = 2 is left for the first item; the best value reachable with that capacity is dp[1][2] = 3. So take = 4 + 3 = 7. Result: 7 is bigger than 3, so taking item 2 is better.

---

## 4. Complexity

| Algorithm | Technique | Time | Space |
|---|---|---|---|
| Dijkstra | Greedy | `O(V^2)` with the simple scan in `dijkstra_steps`; `O((V + E) log V)` with the heap in `dijkstra()` | `O(V)` |
| Huffman | Greedy | `O(n log n)` with a heap (`n` = distinct symbols); the counted list version re-scans a list each round, `O(n^2)`, fine for a demo | `O(n)` |
| 0/1 Knapsack | Dynamic programming | `O(n * W)` (`n` items, `W` capacity) | `O(n * W)` for the full table (`O(W)` is enough if you only need the value, but then you cannot backtrack) |

---

## 5. Sample dry run (first 6 steps on each default example)

These tables were produced by running the real step generators. (`<br>` marks a new line inside the formula.)

### Dijkstra: graph A-B 4, A-C 2, B-C 1, B-D 5, C-D 8, C-E 10, D-E 2; source A, destination E (14 steps in total, final answer `A -> C -> B -> D -> E`, distance 10)

| Step | What happens | Formula | A | B | C | D | E |
|---|---|---|---|---|---|---|---|
| 1 | Start: distance to A is 0, every other city is infinity. Goal: find the shortest route from A to E. | `dist[A] = 0<br>dist[every other city] = infinity` | 0 | inf | inf | inf | inf |
| 2 | Visiting A (distance 0). It is the closest unfinished city, so its distance is final. | `u = the unfinished city with the smallest dist<br>candidates: A=0<br>u = A, dist[A] = 0  ->  mark A as finished` | 0 | inf | inf | inf | inf |
| 3 | Visiting A (distance 0). Checking neighbour B: 0 + 4 = 4 is shorter than infinity, so update it. | `new = dist[A] + weight(A,B) = 0 + 4 = 4<br>is new < dist[B]?  4 < infinity  YES<br>dist[B] = 4,  previous[B] = A` | 0 | 4 | inf | inf | inf |
| 4 | Visiting A (distance 0). Checking neighbour C: 0 + 2 = 2 is shorter than infinity, so update it. | `new = dist[A] + weight(A,C) = 0 + 2 = 2<br>is new < dist[C]?  2 < infinity  YES<br>dist[C] = 2,  previous[C] = A` | 0 | 4 | 2 | inf | inf |
| 5 | Visiting C (distance 2). It is the closest unfinished city, so its distance is final. | `u = the unfinished city with the smallest dist<br>candidates: B=4, C=2<br>u = C, dist[C] = 2  ->  mark C as finished` | 0 | 4 | 2 | inf | inf |
| 6 | Visiting C (distance 2). Checking neighbour B: 2 + 1 = 3 is shorter than 4, so update it. | `new = dist[C] + weight(C,B) = 2 + 1 = 3<br>is new < dist[B]?  3 < 4  YES<br>dist[B] = 3,  previous[B] = C` | 0 | 3 | 2 | inf | inf |

### Huffman: `ABRACADABRA` (the whole run has only 6 steps; final codes A = 0, C = 100, D = 101, B = 110, R = 111)

| Step | What happens | Formula |
|---|---|---|
| 1 | Start: count each symbol. Nodes are (symbol:frequency) -> C:1, D:1, B:2, R:2, A:5. | `frequency[c] = how many times c appears in the text<br>length = 11 characters, distinct symbols n = 5<br>merges needed = n - 1 = 4` |
| 2 | Pick the two lowest: C(1) and D(1). Merge them into a new node CD(2) = 1 + 1. C goes on the left edge (0), D on the right edge (1). | `CD.freq = C.freq + D.freq = 1 + 1 = 2<br>merge 1 of 4   nodes left = n - merges = 5 - 1 = 4<br>sum of all merged frequencies so far = 2` |
| 3 | Pick the two lowest: B(2) and R(2). Merge them into a new node BR(4) = 2 + 2. B goes on the left edge (0), R on the right edge (1). | `BR.freq = B.freq + R.freq = 2 + 2 = 4<br>merge 2 of 4   nodes left = n - merges = 5 - 2 = 3<br>sum of all merged frequencies so far = 6` |
| 4 | Pick the two lowest: CD(2) and BR(4). Merge them into a new node CDBR(6) = 2 + 4. CD goes on the left edge (0), BR on the right edge (1). | `CDBR.freq = CD.freq + BR.freq = 2 + 4 = 6<br>merge 3 of 4   nodes left = n - merges = 5 - 3 = 2<br>sum of all merged frequencies so far = 12` |
| 5 | Pick the two lowest: A(5) and CDBR(6). Merge them into a new node ACDBR(11) = 5 + 6. A goes on the left edge (0), CDBR on the right edge (1). | `ACDBR.freq = A.freq + CDBR.freq = 5 + 6 = 11<br>merge 4 of 4   nodes left = n - merges = 5 - 4 = 1<br>sum of all merged frequencies so far = 23` |
| 6 | Tree complete. Read codes from the tree (left=0, right=1). Original size = 88 bits, compressed size = 23 bits. Decoding the bits gives back the text, so it is lossless: True. | `original = 8 x length = 8 x 11 = 88 bits<br>compressed = sum(frequency x code length) = 5x1 + 2x3 + 2x3 + 1x3 + 1x3 = 23 bits<br>saved = (original - compressed) / original = (88 - 23) / 88 = 73.9%` |

### Knapsack: weights 2, 3, 4, 5; values 3, 4, 5, 6; capacity 5 (30 steps in total, answer: items 1 and 2, value 7, weight 5)

| Step | What happens | Formula |
|---|---|---|
| 1 | Start: row 0 means 'no items', so the best value is 0 for every capacity. We now fill the table row by row: dp[i][w] = best value using the first i items with capacity w. | `dp[0][w] = 0 for every w<br>if weight_i > w:   dp[i][w] = dp[i-1][w]<br>if weight_i <= w:<br>    dp[i][w] = max( dp[i-1][w] , value_i + dp[i-1][w - weight_i] )` |
| 2 | Item 1 (weight 2, value 3), capacity 0: the item is heavier than 0, so we must skip it. dp[1][0] = dp[0][0] = 0. | `item 1: weight_1 = 2, value_1 = 3    capacity w = 0<br>weight_1 > w   (2 > 0)  ->  item does not fit<br>dp[1][0] = dp[0][0] = 0` |
| 3 | Item 1 (weight 2, value 3), capacity 1: the item is heavier than 1, so we must skip it. dp[1][1] = dp[0][1] = 0. | `item 1: weight_1 = 2, value_1 = 3    capacity w = 1<br>weight_1 > w   (2 > 1)  ->  item does not fit<br>dp[1][1] = dp[0][1] = 0` |
| 4 | Item 1 (weight 2, value 3), capacity 2: skip = 0 (value above), take = 3 + dp[0][0] = 3 + 0 = 3. Choose take, so dp[1][2] = 3. | `item 1: weight_1 = 2, value_1 = 3    capacity w = 2<br>skip = dp[0][2] = 0<br>take = value_1 + dp[0][2 - 2] = 3 + dp[0][0] = 3 + 0 = 3<br>dp[1][2] = max(0, 3) = 3` |
| 5 | Item 1 (weight 2, value 3), capacity 3: skip = 0 (value above), take = 3 + dp[0][1] = 3 + 0 = 3. Choose take, so dp[1][3] = 3. | `item 1: weight_1 = 2, value_1 = 3    capacity w = 3<br>skip = dp[0][3] = 0<br>take = value_1 + dp[0][3 - 2] = 3 + dp[0][1] = 3 + 0 = 3<br>dp[1][3] = max(0, 3) = 3` |
| 6 | Item 1 (weight 2, value 3), capacity 4: skip = 0 (value above), take = 3 + dp[0][2] = 3 + 0 = 3. Choose take, so dp[1][4] = 3. | `item 1: weight_1 = 2, value_1 = 3    capacity w = 4<br>skip = dp[0][4] = 0<br>take = value_1 + dp[0][4 - 2] = 3 + dp[0][2] = 3 + 0 = 3<br>dp[1][4] = max(0, 3) = 3` |

---

## 6. Viva questions with short answers

### Dijkstra

1. **Why does Dijkstra not work with negative weights?** It assumes that once a city is finished its distance can never improve. A negative road found later could make a finished city cheaper, so the answer would be wrong. Use Bellman-Ford instead.
2. **Why is it called greedy?** At every step it picks the closest unfinished city and never changes that decision. With non-negative weights, any other route to that city must pass through an unfinished city that is already at least as far, so it cannot be shorter.
3. **What is the time complexity?** `O(V^2)` when the closest city is found by scanning an array (as in this project). `O((V + E) log V)` with a binary heap.
4. **How do we get the path, not just the distance?** Whenever a distance is updated we store the city we came from (the "previous" table). At the end we walk back from the destination to the source and reverse the list.
5. **What happens if the destination cannot be reached?** Its distance stays infinity. The algorithm runs out of reachable cities and reports "no route".
6. **What is the formula used for a road, and what is it called?** `new = dist[u] + weight(u,v)`; if `new < dist[v]` we update. This is called relaxing the edge.

### Huffman coding

1. **Why do we always merge the two lowest-frequency nodes?** Rare symbols should get the longest codes. Merging the two lowest puts them deepest in the tree, and this greedy choice is proven to give the minimum total number of bits.
2. **What does "prefix-free" mean and why is it needed?** No code is the beginning of another code, because symbols sit only on leaves. So the bit string can be decoded from left to right without separators and without ambiguity.
3. **What is the time complexity?** `O(n log n)` with a heap, where `n` is the number of different symbols. Encoding the text then takes `O(length)`.
4. **Is Huffman coding lossless? How did you show it?** Yes. Decoding the bits with the same tree gives back the exact text; the program does this and shows `lossless: True`. For `ABRACADABRA` the size drops from 88 bits (8 per character) to 23 bits.
5. **What happens with a text that has only one different character?** There is nothing to merge, so the tree is a single leaf. We give it the code `0`, so each character costs 1 bit.
6. **How can you check the compressed size without encoding?** For two or more symbols it equals the sum of all merged frequencies. For `ABRACADABRA`: 2 + 4 + 6 + 11 = 23.

### 0/1 Knapsack

1. **What does `dp[i][w]` mean?** The best total value using only the first `i` items with capacity `w`.
2. **Why is it called 0/1?** Each item is taken completely or not at all. (The fractional knapsack, where you can take part of an item, is solved by a greedy method on value/weight.)
3. **What is the recurrence?** If the item fits: `dp[i][w] = max(dp[i-1][w], value + dp[i-1][w - weight])`. If it does not fit: `dp[i][w] = dp[i-1][w]`.
4. **What is the complexity? Is it really polynomial?** `O(n * W)` time and space. It is "pseudo-polynomial": it depends on the number `W` itself, not on how many bits are needed to write `W`. The general knapsack problem is NP-hard.
5. **How do you find which items were chosen?** Backtrack from `dp[n][W]`. If `dp[i][w]` is different from `dp[i-1][w]`, item `i` was taken: subtract its weight from `w`. Otherwise it was skipped. Then move to row `i-1`.
6. **How can the space be reduced, and what do you lose?** Keep only two rows (or one row filled right to left): `O(W)` space. You then cannot backtrack to list the chosen items.

### About the Complexity Graph

1. **Why is the vertical axis logarithmic?** Time and space differ a lot (for example 1,800 operations against 120 cells). On a log axis each gridline is 10 times bigger, so both lines are readable in one chart and a straight-looking climb means fast growth.
2. **How did you get the numbers for the graph?** By running the algorithm on inputs of size 2, 4, ... 40 and counting basic operations (time) and memory cells (space), not by drawing a formula.
3. **Which algorithm has space close to its time?** 0/1 Knapsack: the DP table has about as many cells as there are cells to compute, so the two lines almost overlap.
4. **What does it mean when `n` doubles and time grows about x4?** The time is quadratic, `O(n^2)`. About x2 means linear.

---

## 7. Friendly error messages

The program never crashes or opens a popup on bad input. A red message appears under the buttons for: empty text, empty graph, non-numeric values, negative values, mismatching number of weights and values, zero weights, **capacity 0**, source = destination, unknown or duplicate city, a road from a city to itself, and inputs that are too large for the picture (more than 16 different Huffman characters, more than 10 knapsack items, capacity above 25). An **unreachable** destination still runs the dry run and ends with a red "No route exists" result. Pressing **Next Step** after the end shows the final result again. If your input is not valid, the Complexity Graph simply shows "Enter a valid input to see your own point on the chart."

---

## 8. Testing (what was and was not checked)

`test_algorithms.py` (39 tests, no GUI):

* Each generator's final result equals the normal function, on several examples.
* Edge cases: unreachable city, source = destination, zero-weight road, negative weight, unknown city, single-character Huffman text, empty text, two-symbol text, spaces / digits / non-English characters, an item heavier than the capacity, every item too heavy, capacity 0, ties, invalid input.
* 300 random graphs: Dijkstra's total equals a brute-force search over all paths, and the returned path really exists and costs that total.
* 200 random Huffman texts: decoded text equals the original, the compressed size equals the sum of all merge frequencies, codes are prefix-free.
* 400 random knapsacks: the best value equals a brute-force check over every subset, the chosen items fit and add up to the answer.
* **Formulas and explanations:** every step of every algorithm (including the edge cases) has a formula and a detailed explanation; the numbers inside the formulas are checked against the real values (for example `dp[2][5] = max(3, 7) = 7`, `new = dist[C] + weight(C,B) = 2 + 1 = 3`, `CD.freq = C.freq + D.freq = 1 + 1 = 2`); 60 random knapsacks check that the formula's result equals the stored table cell.
* **Complexity data:** the counted operations match the hand-derived formulas (for example Knapsack `4 x 6 + 4 = 28`), time and space grow with `n`, and doubling `n` gives about x4 for quadratic and about x2 for linear counts.

`test_gui.py` (23 tests) drove the **real Tkinter window** under a virtual display (Xvfb): every button, Previous Step showing the earlier step, Play / Pause with the root.after timer, Reset, input changes resetting the animation, tab switching, window resizing, every error message listed above, all three parts (what / formula / why) shown for every step of every algorithm, and the Complexity Graph window (opening only once, drawing both lines and the markers, following the tab and the input, invalid input, resizing, closing and reopening, closing with the window's X button). Screenshots of every algorithm and of the three graphs were looked at on 1366x768, 1300x860 and 1920x1080 screens.

**Not tested:**

* Every GUI run used **Tk 9.0** (the only Tk available in the test environment), on Python 3.10 and 3.12. **Tk 8.6**, which many Windows / macOS Python installs ship, was not tried. The rotated "count (log scale)" label on the graph needs Tk 8.6 or newer.
* It was **never run on Windows or macOS**, so fonts and colours may look slightly different. Treeview row colours are expected to work, but one old Tk release (8.6.9) is known to have a bug with them; this could not be checked.
* No human clicked with a real mouse. Buttons were pressed from code (`button.invoke()`), drop-down choices with a generated event, and text boxes by setting their variables.
* Play was timed only at the fastest speed (200 ms); slower speeds use the same code path but were not timed.
* On a small screen (1366x768) the Dry run box shows only part of a long explanation at once; you scroll it. Nothing is cut off, but it is less comfortable than on a bigger screen.
* The graph counts are operation counts of *this* program's simple versions, not wall-clock times, so they show growth rate, not speed.
