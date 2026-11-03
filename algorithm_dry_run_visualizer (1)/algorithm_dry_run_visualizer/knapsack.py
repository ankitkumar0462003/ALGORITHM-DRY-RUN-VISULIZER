# ======================================================================
# Algorithm  : 0/1 Knapsack
# Technique  : Dynamic programming (build a table of smaller sub-problems)
# Time       : O(n * W)   n = number of items, W = capacity
# Space      : O(n * W)   for the full table (needed to backtrack the chosen items)
# Use when   : You must pick whole items (take it or leave it) to get the
#              maximum total value without going over a weight limit.
# ======================================================================
# This file is PURE LOGIC: no Tkinter.
#
# dp[i][w] = best value using only the first i items with capacity w.
#   skip item i : dp[i-1][w]
#   take item i : values[i-1] + dp[i-1][w - weights[i-1]]   (only if weights[i-1] <= w)
#   dp[i][w] = the bigger of the two (on a tie we skip, so the answer is repeatable)


def check_input(weights, values, capacity):
    """Raise ValueError with a friendly message if the input is not usable."""
    if len(weights) == 0 or len(values) == 0:  # need at least one item
        raise ValueError("Please enter at least one item (weights and values).")
    if len(weights) != len(values):  # every item needs both a weight and a value
        raise ValueError("The number of weights and values must be the same.")
    for w in weights:
        if w <= 0:  # zero or negative weights make no sense here
            raise ValueError("Weights must be positive whole numbers.")
    for v in values:
        if v < 0:  # a negative value would never be picked
            raise ValueError("Values cannot be negative.")
    if capacity < 0:  # negative capacity is impossible
        raise ValueError("Capacity cannot be negative.")


def knapsack(weights, values, capacity):
    """Return the final answer as a dictionary (no steps)."""
    check_input(weights, values, capacity)
    n = len(weights)  # number of items
    dp = []  # the table: n+1 rows, capacity+1 columns, all zeros
    for i in range(n + 1):
        dp.append([0] * (capacity + 1))
    for i in range(1, n + 1):  # item number i (1-based)
        for w in range(capacity + 1):  # every capacity from 0 to W
            best = dp[i - 1][w]  # option 1: skip the item
            if weights[i - 1] <= w:  # option 2 is only possible if the item fits
                take = values[i - 1] + dp[i - 1][w - weights[i - 1]]
                if take > best:  # take only if strictly better
                    best = take
            dp[i][w] = best
    chosen = []  # backtrack to find which items were used
    w = capacity
    for i in range(n, 0, -1):  # from the last item to the first
        if dp[i][w] != dp[i - 1][w]:  # value changed, so item i was taken
            chosen.append(i)
            w = w - weights[i - 1]  # remove its weight
    chosen.reverse()  # smallest item number first
    total_weight = 0
    for i in chosen:
        total_weight = total_weight + weights[i - 1]
    return {"best_value": dp[n][capacity], "chosen": chosen, "total_weight": total_weight, "table": dp}


def first_items(k):
    """Words for 'the first k items' that read correctly for k = 0, 1 and more (used in explanations)."""
    if k == 0:
        return "no items"
    if k == 1:
        return "the first item"
    return "the first " + str(k) + " items"


def copy_table(table):
    """Copy a table row by row so old steps are not changed later."""
    result = []
    for row in table:
        result.append(list(row))
    return result


def knapsack_cost(weights, values, capacity):
    """Count the work of the DP for the complexity graph.
    Returns (operations, memory_cells). One operation = one table cell computed (one skip-vs-take
    comparison) or one backtracking move."""
    check_input(weights, values, capacity)
    n = len(weights)
    operations = 0
    dp = []
    for i in range(n + 1):
        dp.append([0] * (capacity + 1))
    for i in range(1, n + 1):
        for w in range(capacity + 1):
            operations = operations + 1  # computing dp[i][w] = one comparison of skip and take
            best = dp[i - 1][w]
            if weights[i - 1] <= w:
                take = values[i - 1] + dp[i - 1][w - weights[i - 1]]
                if take > best:
                    best = take
            dp[i][w] = best
    operations = operations + n  # backtracking looks at one cell per item
    memory_cells = (n + 1) * (capacity + 1)  # the whole table is kept so we can backtrack
    return operations, memory_cells


def make_step(kind, message, table, cell=None, skip_cell=None, take_cell=None, skip=None, take=None,
              choice=None, path=None, formula="", detail=""):
    """Build one step dictionary."""
    return {
        "kind": kind,  # "start", "cell", "backtrack" or "done"
        "message": message,  # short plain-English sentence
        "formula": formula,  # the formula of this step with the real numbers filled in
        "detail": detail,  # longer explanation of why and what it means
        "table": copy_table(table),  # DP table so far (None = not filled yet)
        "cell": cell,  # (i, w) cell being computed
        "skip_cell": skip_cell,  # (i-1, w) cell used for 'skip'
        "take_cell": take_cell,  # (i-1, w-weight) cell used for 'take' (None if the item does not fit)
        "skip": skip,  # value of the skip option
        "take": take,  # value of the take option (None if it does not fit)
        "choice": choice,  # "skip" or "take"
        "path": path if path is not None else [],  # backtracking cells so far
        "chosen": None, "best_value": None, "total_weight": None,  # final step only
    }


def knapsack_steps(weights, values, capacity):
    """Generator: yields one dictionary per step. The LAST one holds the final result."""
    check_input(weights, values, capacity)
    n = len(weights)
    table = []  # None means "not computed yet"
    for i in range(n + 1):
        table.append([None] * (capacity + 1))
    for w in range(capacity + 1):  # row 0: no items, so value is 0 for every capacity
        table[0][w] = 0

    yield make_step(
        "start", "Start: row 0 means 'no items', so the best value is 0 for every capacity. "
        "We now fill the table row by row: dp[i][w] = best value using the first i items "
        "with capacity w.", table,
        formula="dp[0][w] = 0 for every w\n"
                "if weight_i > w:   dp[i][w] = dp[i-1][w]\n"
                "if weight_i <= w:\n"
                "    dp[i][w] = max( dp[i-1][w] , value_i + dp[i-1][w - weight_i] )",
        detail="0/1 Knapsack: each item is taken completely or not at all, and the total weight must not exceed "
               "the capacity " + str(capacity) + ". We build a table where dp[i][w] is the best total value that "
               "can be reached using only the first i items and a bag of size w. Row 0 (no items) is all 0. "
               "Every other cell is computed from cells in the row above, by comparing two options: SKIP item i "
               "(keep the best value without it) or TAKE item i (gain its value, but lose its weight from the "
               "capacity). The answer is the bottom-right cell dp[" + str(n) + "][" + str(capacity) + "].")

    for i in range(1, n + 1):  # item i
        weight = weights[i - 1]
        value = values[i - 1]
        for w in range(capacity + 1):  # capacity w
            skip = table[i - 1][w]  # option 1: value from the row above
            if weight <= w:  # the item fits
                take = value + table[i - 1][w - weight]  # option 2: value + leftover capacity's best
                take_cell = (i - 1, w - weight)
            else:  # item too heavy
                take = None
                take_cell = None
            if take is not None and take > skip:  # take only if strictly better
                choice = "take"
                table[i][w] = take
            else:
                choice = "skip"
                table[i][w] = skip
            head = "item " + str(i) + ": weight_" + str(i) + " = " + str(weight) + ", value_" + str(i) + " = " + str(value) + "    capacity w = " + str(w)
            if take is None:
                message = ("Item " + str(i) + " (weight " + str(weight) + ", value " + str(value)
                           + "), capacity " + str(w) + ": the item is heavier than " + str(w)
                           + ", so we must skip it. dp[" + str(i) + "][" + str(w) + "] = dp["
                           + str(i - 1) + "][" + str(w) + "] = " + str(skip) + ".")
                formula = (head + "\n"
                           "weight_" + str(i) + " > w   (" + str(weight) + " > " + str(w) + ")  ->  item does not fit\n"
                           "dp[" + str(i) + "][" + str(w) + "] = dp[" + str(i - 1) + "][" + str(w) + "] = " + str(skip))
                detail = ("The bag has room for only " + str(w) + " but item " + str(i) + " weighs " + str(weight)
                          + ", so it can not be packed at all. There is just one possibility: skip it. The best value "
                          "is the same as with " + first_items(i - 1) + " and the same capacity, which is the "
                          "cell directly above: dp[" + str(i - 1) + "][" + str(w) + "] = " + str(skip) + ".")
            else:
                message = ("Item " + str(i) + " (weight " + str(weight) + ", value " + str(value)
                           + "), capacity " + str(w) + ": skip = " + str(skip) + " (value above), take = "
                           + str(value) + " + dp[" + str(i - 1) + "][" + str(w - weight) + "] = "
                           + str(value) + " + " + str(table[i - 1][w - weight]) + " = " + str(take)
                           + ". Choose " + choice + ", so dp[" + str(i) + "][" + str(w) + "] = "
                           + str(table[i][w]) + ".")
                formula = (head + "\n"
                           "skip = dp[" + str(i - 1) + "][" + str(w) + "] = " + str(skip) + "\n"
                           "take = value_" + str(i) + " + dp[" + str(i - 1) + "][" + str(w) + " - " + str(weight) + "] = "
                           + str(value) + " + dp[" + str(i - 1) + "][" + str(w - weight) + "] = " + str(value) + " + "
                           + str(table[i - 1][w - weight]) + " = " + str(take) + "\n"
                           "dp[" + str(i) + "][" + str(w) + "] = max(" + str(skip) + ", " + str(take) + ") = " + str(table[i][w]))
                if choice == "take":
                    reason = (str(take) + " is bigger than " + str(skip) + ", so taking item " + str(i) + " is better.")
                elif take == skip:
                    reason = ("both options give " + str(skip) + " (a tie), so we skip the item: it keeps the bag lighter "
                              "and gives the same value.")
                else:
                    reason = (str(skip) + " is bigger than " + str(take) + ", so skipping item " + str(i) + " is better.")
                detail = ("Two options for item " + str(i) + " with capacity " + str(w) + ". SKIP: do not pack it, "
                          "so the best value is the one already found for " + first_items(i - 1) + " with capacity "
                          + str(w) + ": dp[" + str(i - 1) + "][" + str(w) + "] = " + str(skip) + " (the cell above). "
                          "TAKE: pack it, gaining " + str(value) + ", but it uses " + str(weight) + " of the capacity, "
                          "so only " + str(w) + " - " + str(weight) + " = " + str(w - weight) + " is left for "
                          + first_items(i - 1) + "; the best value reachable with that capacity is dp[" + str(i - 1) + "]["
                          + str(w - weight) + "] = " + str(table[i - 1][w - weight]) + ". So take = " + str(value)
                          + " + " + str(table[i - 1][w - weight]) + " = " + str(take) + ". Result: " + reason)
            yield make_step("cell", message, table, (i, w), (i - 1, w), take_cell, skip, take, choice,
                            formula=formula, detail=detail)

    # ---- backtracking: find which items were taken ----
    chosen = []
    path = [(n, capacity)]  # start at the bottom-right cell
    w = capacity
    for i in range(n, 0, -1):
        here = (i, w)  # the cell we are looking at in this step
        if table[i][w] != table[i - 1][w]:  # value changed => item i was taken
            chosen.append(i)
            message = ("Backtrack at dp[" + str(i) + "][" + str(w) + "] = " + str(table[i][w])
                       + ": it differs from the cell above (" + str(table[i - 1][w])
                       + "), so item " + str(i) + " was TAKEN. Move to capacity " + str(w) + " - "
                       + str(weights[i - 1]) + " = " + str(w - weights[i - 1]) + ".")
            formula = ("dp[" + str(i) + "][" + str(w) + "] = " + str(table[i][w]) + "  !=  dp[" + str(i - 1) + "][" + str(w)
                       + "] = " + str(table[i - 1][w]) + "  ->  item " + str(i) + " TAKEN\n"
                       "w = w - weight_" + str(i) + " = " + str(w) + " - " + str(weights[i - 1]) + " = " + str(w - weights[i - 1]))
            detail = ("Backtracking reads the answer out of the finished table, starting at the bottom-right cell. "
                      "At dp[" + str(i) + "][" + str(w) + "] the value " + str(table[i][w]) + " is different from the value "
                      "above it (" + str(table[i - 1][w]) + "). That means the value only reached " + str(table[i][w])
                      + " because item " + str(i) + " was packed. So item " + str(i) + " is in the bag. We then remove "
                      "its weight (" + str(weights[i - 1]) + ") from the capacity and move up one row to continue "
                      "with capacity " + str(w - weights[i - 1]) + ".")
            w = w - weights[i - 1]
        else:  # same as above => item i was skipped
            message = ("Backtrack at dp[" + str(i) + "][" + str(w) + "] = " + str(table[i][w])
                       + ": it equals the cell above, so item " + str(i) + " was NOT taken.")
            formula = ("dp[" + str(i) + "][" + str(w) + "] = " + str(table[i][w]) + "  ==  dp[" + str(i - 1) + "][" + str(w)
                       + "] = " + str(table[i - 1][w]) + "  ->  item " + str(i) + " NOT taken\n"
                       "w stays " + str(w))
            detail = ("At dp[" + str(i) + "][" + str(w) + "] the value " + str(table[i][w]) + " is exactly the same as "
                      "the value above it. The best value did not need item " + str(i) + ", so it was not packed. "
                      "The capacity stays " + str(w) + " and we move up one row.")
        path.append((i - 1, w))  # the next cell on the backtracking path
        yield make_step("backtrack", message, table, here, path=list(path), formula=formula, detail=detail)
    chosen.reverse()
    total_weight = 0
    for i in chosen:
        total_weight = total_weight + weights[i - 1]
    total_value = table[n][capacity]

    if chosen:
        names = ""  # build text like "item 1, item 2"
        value_parts = []  # pieces such as "3"
        weight_parts = []  # pieces such as "2"
        for i in chosen:
            if names != "":
                names = names + ", "
            names = names + "item " + str(i)
            value_parts.append(str(values[i - 1]))
            weight_parts.append(str(weights[i - 1]))
        text = "Finished: take " + names + ". Total value = " + str(total_value) \
               + ", total weight = " + str(total_weight) + " (capacity " + str(capacity) + ")."
        formula = ("best value = dp[" + str(n) + "][" + str(capacity) + "] = " + str(total_value) + "\n"
                   "value  = " + " + ".join(value_parts) + " = " + str(total_value) + "\n"
                   "weight = " + " + ".join(weight_parts) + " = " + str(total_weight) + "  <=  capacity " + str(capacity))
        detail = ("The bottom-right cell dp[" + str(n) + "][" + str(capacity) + "] = " + str(total_value) + " is the "
                  "best possible total value. Backtracking showed which items give it: " + names + ". Their values add "
                  "up to " + " + ".join(value_parts) + " = " + str(total_value) + ", and their weights add up to "
                  + " + ".join(weight_parts) + " = " + str(total_weight) + ", which does not exceed the capacity "
                  + str(capacity) + ". No other choice of items can give a bigger value within this weight limit.")
    else:
        text = "Finished: no item can be taken. Total value = 0, total weight = 0."
        formula = "best value = dp[" + str(n) + "][" + str(capacity) + "] = 0\nno item was taken"
        detail = ("Every item is heavier than the capacity " + str(capacity) + " or has value 0, so packing anything "
                  "gains nothing. The bag stays empty: value 0, weight 0.")
    last = make_step("done", text, table, path=list(path), formula=formula, detail=detail)
    last["chosen"] = chosen
    last["best_value"] = total_value
    last["total_weight"] = total_weight
    yield last
