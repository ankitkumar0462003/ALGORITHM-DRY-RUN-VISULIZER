# ======================================================================
# Algorithm  : Dijkstra's shortest path
# Technique  : Greedy (always finish the closest unfinished city next)
# Time       : O(V^2) with the simple scan used in dijkstra_steps
#              O((V + E) log V) with the heap used in dijkstra()
# Space      : O(V) for distance / previous / finished tables
# Use when   : You need the cheapest route between cities and every road
#              weight is zero or positive (it fails with negative weights).
# ======================================================================
# This file is PURE LOGIC: no Tkinter, no printing.
#
# A graph is a dictionary of dictionaries:
#     {"A": {"B": 4, "C": 2}, "B": {"A": 4}, ...}
# meaning: city A has a road to B of weight 4 and a road to C of weight 2.
# (For two-way roads, the road must be listed under both cities.)

import heapq  # heapq gives a ready-made "smallest first" queue (used in dijkstra())

INF = float("inf")  # "infinity": the starting distance of every city except the source


def check_input(graph, source, target):
    """Raise ValueError with a friendly message if the input is not usable."""
    if not graph:  # an empty dictionary means there are no cities
        raise ValueError("The graph is empty. Add some cities first.")
    if source not in graph:  # the start city must exist
        raise ValueError("Source city '" + str(source) + "' is not in the graph.")
    if target not in graph:  # the destination city must exist
        raise ValueError("Destination city '" + str(target) + "' is not in the graph.")
    for city in graph:  # look at every city ...
        for neighbour, weight in graph[city].items():  # ... and every road leaving it
            if neighbour not in graph:  # a road must lead to a known city
                raise ValueError("Road " + city + "-" + str(neighbour) + " leads to an unknown city.")
            if weight < 0:  # Dijkstra cannot handle negative weights
                raise ValueError("Road " + city + "-" + neighbour + " has a negative weight. Weights must be 0 or more.")


def build_path(previous, source, target):
    """Walk backwards from target to source using the 'previous' table."""
    path = []  # we collect the cities here, last city first
    city = target  # start at the destination
    while city is not None:  # keep going until we run past the source
        path.append(city)  # remember this city
        city = previous[city]  # move one step back along the best route
    path.reverse()  # flip so it reads source -> target
    if path[0] != source:  # if we did not end at the source, there is no route
        return None
    return path


def dijkstra(graph, source, target):
    """Return (path, total). If target cannot be reached: (None, infinity)."""
    check_input(graph, source, target)  # stop early on bad input
    distance = {}  # best known distance to each city
    previous = {}  # which city we came from on the best route
    for city in graph:  # set up the tables
        distance[city] = INF  # nobody is reached yet
        previous[city] = None  # nobody has a parent yet
    distance[source] = 0  # the source is 0 away from itself
    queue = [(0, source)]  # heap of (distance, city) pairs, smallest first
    finished = set()  # cities whose distance can no longer improve
    while queue:  # while there are cities left to try
        dist_u, u = heapq.heappop(queue)  # take the closest city
        if u in finished:  # an older, worse entry for a finished city
            continue  # ignore it
        finished.add(u)  # u's distance is now final
        if u == target:  # we reached the destination, so we can stop
            break
        for v, weight in graph[u].items():  # look at every road leaving u
            if v in finished:  # v is already final, nothing to improve
                continue
            new_dist = dist_u + weight  # distance to v if we go through u
            if new_dist < distance[v]:  # is it better than what we know?
                distance[v] = new_dist  # yes: update the distance
                previous[v] = u  # and remember we came via u
                heapq.heappush(queue, (new_dist, v))  # queue v with its new distance
    if distance[target] == INF:  # target never got a real distance
        return None, INF
    return build_path(previous, source, target), distance[target]


def dijkstra_cost(graph, source):
    """Count the work of the simple O(V^2) version for the complexity graph.
    Returns (operations, memory_cells). It runs until every reachable city is finished,
    so the count does not depend on where the destination is."""
    check_input(graph, source, source)  # empty graph or unknown source -> friendly ValueError
    operations = 0  # one operation = one comparison of two distances
    distance = {}  # distance table
    for city in graph:
        distance[city] = INF
    distance[source] = 0
    finished = []  # cities that are final
    while True:
        best = None  # closest unfinished city
        for city in graph:  # scanning every city costs one comparison each
            operations = operations + 1
            if city in finished or distance[city] == INF:
                continue
            if best is None or distance[city] < distance[best]:
                best = city
        if best is None:  # nothing reachable is left
            break
        finished.append(best)
        for v in graph[best]:  # checking each road leaving the city costs one comparison
            operations = operations + 1
            if v not in finished and distance[best] + graph[best][v] < distance[v]:
                distance[v] = distance[best] + graph[best][v]
    memory_cells = 3 * len(graph)  # distance table + previous table + finished list
    return operations, memory_cells


def make_step(kind, message, current, distance, finished, previous, edge=None, updated=False,
              formula="", detail=""):
    """Build one step dictionary. Copies the tables so later changes do not alter old steps."""
    return {
        "kind": kind,  # "start", "visit", "check" or "done"
        "message": message,  # short plain-English sentence shown first in the Dry run box
        "formula": formula,  # the formula of this step with the real numbers filled in
        "detail": detail,  # longer explanation: why this step is done and what it means
        "current": current,  # city being processed (or None)
        "distance": dict(distance),  # snapshot of the distance table
        "finished": sorted(finished),  # snapshot of the finished cities
        "previous": dict(previous),  # snapshot of the parent table
        "edge": edge,  # (u, v) road being checked, or None
        "updated": updated,  # True if this check improved a distance
        "path": None,  # final path (only on the last step)
        "total": None,  # final total (only on the last step)
    }


def show(value):
    """Turn a distance into text: infinity becomes the word 'infinity'."""
    if value == INF:
        return "infinity"
    return str(value)


def table_text(graph, distance, finished):
    """One line such as 'A=0, B=4, C=2, D=inf' (used inside explanations)."""
    parts = []
    for city in sorted(graph):  # alphabetical order
        if city in finished:
            parts.append(city + "=" + show(distance[city]) + " (final)")
        else:
            parts.append(city + "=" + show(distance[city]))
    return ", ".join(parts)


def dijkstra_steps(graph, source, target):
    """Generator: yields one dictionary per step. The LAST one holds the final result."""
    check_input(graph, source, target)  # same input rules as dijkstra()
    distance = {}  # distance table
    previous = {}  # parent table
    for city in graph:  # set up the tables
        distance[city] = INF
        previous[city] = None
    distance[source] = 0  # the source costs 0
    finished = []  # list of finished cities, in the order they finish

    yield make_step(
        "start",
        "Start: distance to " + source + " is 0, every other city is infinity. "
        "Goal: find the shortest route from " + source + " to " + target + ".",
        None, distance, finished, previous,
        formula="dist[" + source + "] = 0\ndist[every other city] = infinity",
        detail="Dijkstra keeps a table with the best distance found so far from " + source + " to every city. "
               "At the start we know only one thing: " + source + " is 0 away from itself. Every other city "
               "has not been reached yet, so its distance is infinity. Then we repeat two actions: "
               "(1) VISIT the closest unfinished city, its distance is now final; "
               "(2) CHECK each road leaving it to see if it gives a shorter route to a neighbour.")

    while True:  # repeat until we are done
        best = None  # the closest unfinished city found so far
        candidates = []  # text pieces such as 'B=4', used in the explanation
        for city in sorted(graph):  # sorted() makes ties break alphabetically
            if city in finished:  # skip cities that are final
                continue
            if distance[city] == INF:  # skip cities we cannot reach yet
                continue
            candidates.append(city + "=" + show(distance[city]))
            if best is None or distance[city] < distance[best]:  # strictly closer wins
                best = city
        if best is None:  # nothing reachable is left
            break
        u = best  # u is the city we visit now
        finished.append(u)  # its distance is now final
        yield make_step(
            "visit",
            "Visiting " + u + " (distance " + show(distance[u]) + "). "
            "It is the closest unfinished city, so its distance is final.",
            u, distance, finished, previous,
            formula="u = the unfinished city with the smallest dist\n"
                    "candidates: " + ", ".join(candidates) + "\n"
                    "u = " + u + ", dist[" + u + "] = " + show(distance[u]) + "  ->  mark " + u + " as finished",
            detail="Among the cities that are not finished yet and already have a known distance (" +
                   ", ".join(candidates) + "), the smallest is " + u + " with " + show(distance[u]) + ". "
                   "Why is it final? Every road weight is 0 or more, so any other route to " + u +
                   " would have to pass through a city that is already at least " + show(distance[u]) +
                   " away, and it can never become shorter. That is the greedy choice of Dijkstra.")
        if u == target:  # we reached the destination: no need to go further
            break
        for v in sorted(graph[u]):  # check each neighbour in alphabetical order
            if v in finished:  # finished cities cannot improve
                continue
            weight = graph[u][v]  # weight of road u-v
            new_dist = distance[u] + weight  # cost of reaching v through u
            old_dist = distance[v]  # what we knew before
            sum_text = "new = dist[" + u + "] + weight(" + u + "," + v + ") = " + str(distance[u]) + " + " + str(weight) + " = " + str(new_dist)
            if new_dist < old_dist:  # better route found
                distance[v] = new_dist  # update the table
                previous[v] = u  # remember the parent
                message = ("Visiting " + u + " (distance " + show(distance[u]) + "). Checking neighbour "
                           + v + ": " + str(distance[u]) + " + " + str(weight) + " = " + str(new_dist)
                           + " is shorter than " + show(old_dist) + ", so update it.")
                formula = (sum_text + "\nis new < dist[" + v + "]?  " + str(new_dist) + " < " + show(old_dist)
                           + "  YES\ndist[" + v + "] = " + str(new_dist) + ",  previous[" + v + "] = " + u)
                detail = ("We stand on " + u + " (final distance " + str(distance[u]) + "). The road " + u + "-" + v
                          + " has weight " + str(weight) + ". Going from the source to " + u + " and then along this road "
                          "reaches " + v + " with total cost " + str(new_dist) + ". The best route to " + v
                          + " known until now costs " + show(old_dist) + ". " + str(new_dist) + " is smaller, so we have "
                          "found a shorter route: we store the new distance and remember that " + v + " is reached "
                          "through " + u + " (this is how the path can be rebuilt at the end). "
                          "This 'try to improve a neighbour' action is called RELAXING the edge.")
                yield make_step("check", message, u, distance, finished, previous, (u, v), True, formula, detail)
            else:  # no improvement
                message = ("Visiting " + u + " (distance " + show(distance[u]) + "). Checking neighbour "
                           + v + ": " + str(distance[u]) + " + " + str(weight) + " = " + str(new_dist)
                           + " is not shorter than " + show(old_dist) + ", so keep the old distance.")
                formula = (sum_text + "\nis new < dist[" + v + "]?  " + str(new_dist) + " < " + show(old_dist)
                           + "  NO\ndist[" + v + "] stays " + show(old_dist))
                detail = ("We stand on " + u + " (final distance " + str(distance[u]) + "). The road " + u + "-" + v
                          + " has weight " + str(weight) + ", so going through " + u + " would reach " + v
                          + " with cost " + str(new_dist) + ". But we already know a route to " + v + " that costs "
                          + show(old_dist) + ", which is not worse. So nothing changes: the table keeps "
                          + show(old_dist) + " for " + v + ".")
                yield make_step("check", message, u, distance, finished, previous, (u, v), False, formula, detail)

    # ---- final step ----
    if distance[target] == INF:  # target was never reached
        last = make_step(
            "done",
            "Finished: there is NO route from " + source + " to " + target + ".",
            None, distance, finished, previous,
            formula="dist[" + target + "] = infinity  ->  no route",
            detail="Every city that could be reached from " + source + " has been finished, and " + target +
                   " is not among them: its distance is still infinity. No chain of roads joins " + source +
                   " and " + target + ", so no route exists. Final table: " + table_text(graph, distance, finished) + ".")
        last["path"] = None
        last["total"] = INF
    else:
        path = build_path(previous, source, target)  # follow the parents back
        back_text = " <- ".join(reversed(path))  # E <- D <- B <- C <- A
        weights = []  # road weights along the path
        for k in range(len(path) - 1):
            weights.append(str(graph[path[k]][path[k + 1]]))
        sum_text = " + ".join(weights)  # for example "2 + 1 + 5 + 2"
        if sum_text == "":  # source and target are the same city: no roads used
            sum_text = "0"
        formula = ("path: follow previous[] back from " + target + ":  " + back_text + "\n"
                   "total = " + sum_text + " = " + str(distance[target]))
        detail = ("Starting at the destination " + target + ", we look at previous[" + target + "], then at its "
                  "previous, and so on until we reach " + source + ". Reading that chain backwards gives the shortest "
                  "path " + " -> ".join(path) + ". Adding the road weights along it gives " + sum_text + " = "
                  + str(distance[target]) + ", which equals dist[" + target + "] in the table. "
                  "No other route is shorter.")
        last = make_step(
            "done",
            "Finished: shortest path is " + " -> ".join(path)
            + " with total distance " + str(distance[target]) + ".",
            None, distance, finished, previous, formula=formula, detail=detail)
        last["path"] = path
        last["total"] = distance[target]
    yield last
