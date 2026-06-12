import time
import math
import heapq
from collections import deque

# -------------------------------------------------------------------------------------
# GOAL STATE
GOAL_STATE = "012345678"

# -------------------------------------------------------------------------------------
def ConvertState_ToString(number: int) -> str:
    """Convert an integer into a 9-character puzzle string, adding leading zero if needed."""
    s = str(number) #convert the integer to string
    if len(s) == 8: #if the first state =0,concatenate zero
        s = '0' + s
    return s

# -------------------------------------------------------------------------------------
def validate_input(state_str):
    """Ensure the input has digits 0-8 exactly once."""
    if len(state_str) != 9:
        return False
    if set(state_str) != set("012345678"):
        return False
    return True

# -------------------------------------------------------------------------------------
def Print_Board(state: str):
    """Print a 3x3 puzzle board."""
    for i in range(0, 9, 3):
        print(state[i:i + 3])
    print("----")

# -------------------------------------------------------------------------------------
#get children by moving '0' up/down/left/right
def Generate_Children(state: str):
    """Return list of tuples (new_state, direction) for all valid moves."""
    children = []
    # to get position of zero in grid
    # row = zero_position // 3   #col = zero_position % 3
    # div mod shortcut to get div and mod together
    zero_index = state.index('0')
    row, col = divmod(zero_index, 3)
    # all possible moves
    moves = [(-1, 0, "Up"), (1, 0, "Down"), (0, -1, "Left"), (0, 1, "Right")]
    for dr, dc, direction in moves:
        new_row, new_col = row + dr, col + dc #calculate new position
        if 0 <= new_row < 3 and 0 <= new_col < 3: #check that position is valid  (between 0 w 3)
            new_index = new_row * 3 + new_col #get index in string array(multiply*3 + remainder) because of div and mod
            new_state = list(state)#change string to list to be able to swap (string is immutable in python)
            # swap the zero state with the state found to be possible
            new_state[zero_index], new_state[new_index] = new_state[new_index], new_state[zero_index]
            # change the state back to string and append it to successors
            children.append(("".join(new_state), direction))
    return children

# -------------------------------------------------------------------------------------
def Manhattan_Distance(state: str) -> int:
    distance = 0
    #enumerate(state) gives you both the position index i and the tile number.
    for i, tile in enumerate(state):
        if tile == '0':
            continue

        #This gives the index where this tile should be in the goal.
        goal_index = GOAL_STATE.index(tile)

        current_row, current_col = divmod(i, 3)
        goal_row, goal_col = divmod(goal_index, 3)

        distance += abs(current_row - goal_row) + abs(current_col - goal_col)
    return distance

# -------------------------------------------------------------------------------------
def Euclidean_Distance(state: str) -> float:
    #Computesthe “straight - line distance” for each tile from its current position to goal.
    distance = 0.0
    for i, tile in enumerate(state):
        if tile == '0':
            continue
        goal_index = GOAL_STATE.index(tile)
        current_row, current_col = divmod(i, 3)
        goal_row, goal_col = divmod(goal_index, 3)
        distance += math.sqrt((current_row - goal_row)**2 + (current_col - goal_col)**2)
    return distance


# -------------------------------------------------------------------------------------
def reconstruct_path(goal, parent, moves):
    path = []
    path_moves = []
    node = goal
    while node in parent and node is not None:
        path.append(node)
        if moves[node] is not None:
            path_moves.append(moves[node])
        node = parent[node]
    path.reverse()
    path_moves.reverse()
    return path, path_moves

# -------------------------------------------------------------------------------------
def print_result(name, initial, goal, path, moves, nodes, depth, cost, runtime):
    print(f"\n=== {name} SEARCH RESULT ===")
    print(f"Initial: {initial}")
    print(f"Goal: {goal}")
    print(f"Cost of path: {cost}")
    print(f"Nodes Expanded: {nodes}")
    print(f"Maximum Depth: {depth}")
    print(f"Running Time: {round(runtime, 6)} sec")
    print("\nPath to Goal:")
    for i, st in enumerate(path):
        Print_Board(st)
        if i < len(moves):
            print("Move:", moves[i])

# -------------------------------------------------------------------------------------
def bfs_search(initial: str, goal: str):
    startTime = time.time()
    frontier = deque([(initial, 0)])
    visited = set([initial])
    parent = {initial: None}
    moves = {initial: None}
    exploredNodes = 0
    max_depth = 0
    goal_depth = 0

    while frontier:
        current, depth = frontier.popleft()
        exploredNodes += 1
        max_depth = max(max_depth, depth)

        if current == goal:
            goal_depth = depth
            break

        for (neighbor, direction) in Generate_Children(current):
            if neighbor not in visited:
                visited.add(neighbor)
                parent[neighbor] = current
                moves[neighbor] = direction
                frontier.append((neighbor, depth + 1))

    endTime = time.time()
    path, path_moves = reconstruct_path(goal, parent, moves)


    print("\n=== BFS RESULTS ===")
    print("Path to goal:", " → ".join(path))
    print("Moves taken:", " → ".join(path_moves))
    print("Cost of path (depth of goal):", goal_depth)
    print("Nodes expanded (number of visited nodes):", exploredNodes)
    print("Search depth (max level reached):", max_depth)
    print(f"Running time: {endTime - startTime:.6f} seconds")
    print("====================\n")

# -------------------------------------------------------------------------------------
def dfs_search(initial: str, goal: str):
    startTime = time.time()
    stack = [(initial, 0)]
    visited = set()
    parent = {initial: None}
    moves = {initial: None}
    exploredNodes = 0
    max_depth = 0
    goal_depth = 0

    while stack:
        current, depth = stack.pop()

        #Mark visited when popping
        if current in visited:
            continue
        visited.add(current)

        exploredNodes += 1
        max_depth = max(max_depth, depth)

        if current == goal:
            goal_depth = depth
            break

        for (neighbor, direction) in Generate_Children(current):
            if isinstance(neighbor, list):
                neighbor = ''.join(neighbor)

            if neighbor not in visited:
                parent[neighbor] = current
                moves[neighbor] = direction
                stack.append((neighbor, depth + 1))

    endTime = time.time()
    path, path_moves = reconstruct_path(goal, parent, moves)

    print("\n=== DFS RESULTS ===")
    print("Path to goal:", " → ".join(path))
    print("Moves taken:", " → ".join(path_moves))
    print("Cost of path (depth of goal):", goal_depth)
    print("Nodes expanded (number of visited nodes):", exploredNodes)
    print("Search depth (max level reached):", max_depth)
    print(f"Running time: {endTime - startTime:.6f} seconds")
    print("====================\n")
# -------------------------------------------------------------------------------------
def depth_limited_search(start_state, goal_state, limit):
    stack = [(start_state, 0)]  # (state, depth)
    visited = set([start_state])
    parent = {start_state: None}
    moves = {start_state: None}
    explored_nodes = 0
    max_depth_reached = 0

    start_time = time.time()

    while stack:#loops as long as stack is not empty
        state, depth = stack.pop()
        explored_nodes += 1
        max_depth_reached = max(max_depth_reached, depth)


        if state == goal_state:
            goal_depth = depth  # Record depth at which goal is found
            end_time = time.time()
            path, path_moves = reconstruct_path(goal_state, parent, moves)
            return {
                "path": path,
                "path_moves": path_moves,
                "visited": visited,
                "explored_nodes": explored_nodes,
                "max_depth": max_depth_reached,
                "goal_depth": goal_depth,
                "runtime": end_time - start_time
            }

        #Limit check before expanding children
        if depth < limit:
            for (next_state, move) in Generate_Children(state):  # assumes returns [(child, move)]
                if next_state not in visited:
                    visited.add(next_state)  # Only add unvisited children
                    parent[next_state] = state  # Mark child as visited
                    moves[next_state] = move  # Track parent for path reconstruction
                    stack.append((next_state, depth + 1))  # Push child onto stack with incremented depth

    # If goal not found
    end_time = time.time()
    return {
        "path": None,
        "path_moves": None,
        "visited": visited,
        "explored_nodes": explored_nodes,
        "max_depth": max_depth_reached,
        "goal_depth": None,
        "runtime": end_time - start_time
    }


def iterative_deepening_search(start_state, goal_state):
    limit = 0
    total_nodes_expanded = 0
    max_depth_reached = 0
    start_time = time.time()

    while True: # Loop until a solution is found or safety limit exceeded
        print(f"\nTrying depth limit: {limit}")
        # Call depth-limited search (DLS) for current limit
        result = depth_limited_search(start_state, goal_state, limit)

        total_nodes_expanded += result["explored_nodes"]    # Add nodes explored in this iteration
        max_depth_reached = max(max_depth_reached, result["max_depth"])  # Update max depth
        #Check if solution was found
        if result["path"]:
            end_time = time.time()
            path = result["path"]
            path_moves = result["path_moves"]

            print("\n=== ITERATIVE DEEPENING SEARCH (IDS) RESULTS ===")
            print("Path to goal:", " → ".join(path))
            print("Moves taken:", " → ".join(path_moves))
            print("Cost of path (depth of goal):", result["goal_depth"])
            print("Nodes expanded (number of visited nodes):", total_nodes_expanded)
            print("Search depth (max level reached):", max_depth_reached)
            print(f"Running time: {end_time - start_time:.6f} seconds")
            print("===============================================")
            return path
        #Increase depth limit for next iteration
        limit += 1
        #Safety limit: stop if depth exceeds 40
        if limit > 40:
            print("\nGoal not found up to depth 40.")
            return None

# -------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------
class Node:
    def __init__(self, state, g, h, parent=None, move=None):
        self.state = state          # Current puzzle state as string
        self.g = g                  # Cost to reach this node (g(n))
        self.h = h                  # Heuristic value (h(n))
        self.f = g + h              # Total estimated cost (f(n) = g + h)
        self.parent = parent        # Parent node (for path reconstruction)
        self.move = move            # Move that led to this state

    def __lt__(self, other):
        # Required for heapq to compare nodes based on f(n)
        return self.f < other.f


# -------------------------------------------------------------------------------------
def a_star(initial_state: str, heuristic_func):
    #start time
    start_time = time.time()

    # Initialize start node
    start_node = Node(initial_state, g=0, h=heuristic_func(initial_state))
    frontier_pq = []
    heapq.heappush(frontier_pq, start_node)
    # automatically keeps the smallest f on top

    # Dictionary to track best f(n) for each state
    Fn = {initial_state: start_node.f}

    # Set of already expanded nodes
    expanded_set = set()
    nodes_expanded = 0  #number of expanded nodes
    max_search_depth = 0
    path = []
    moves_list = []
    cost = 0

    while frontier_pq:
        current_node = heapq.heappop(frontier_pq)
        current = current_node.state
        g = current_node.g
        f = current_node.f

        # Skip if already expanded with a worse f(n)
        if current in expanded_set and f > Fn[current]:
            continue
        expanded_set.add(current)
        nodes_expanded += 1
        max_search_depth = max(max_search_depth, g)
        # Track maximum depth reached (g is depth)

        # Goal check
        if current == GOAL_STATE:
            # Reconstruct path using parent links
            node = current_node
            while node is not None:
                path.append(node.state)
                if node.move is not None:
                    moves_list.append(node.move)
                node = node.parent
            path.reverse()
            moves_list.reverse()
            cost = g
            break

        # Expand neighbors
        for neighbor_state, move_direction in Generate_Children(current):
            new_g = g + 1  # cost to reach neighbor
            h = heuristic_func(neighbor_state)
            f_new = new_g + h

            # If we already reached neighbor with a better or equal f(n), skip it
            if neighbor_state in Fn and f_new >= Fn[neighbor_state]:
                continue

            Fn[neighbor_state] = f_new
            neighbor_node = Node(neighbor_state, new_g, h,
                                 parent=current_node, move=move_direction)
            heapq.heappush(frontier_pq, neighbor_node)


    runtime = round(time.time() - start_time, 6)


    print(f"\n=== A* SEARCH ({heuristic_name}) RESULTS ===")
    
    print(f"Initial: {initial_state}")
    print(f"Goal: {GOAL_STATE}")
    print(f"Cost of path: {cost}")
    print(f"Nodes Expanded: {nodes_expanded}")
    print(f"Maximum Depth: {max_search_depth}")
    print(f"Running Time: {runtime} sec")
    print("\nPath to Goal:")
    for i, st in enumerate(path):
        Print_Board(st)
    if i < len(moves_list):
        print("Move:", moves_list[i])
    
    print("====================\n")


# -------------------------------------------------------------------------------------
def menu():
    while True:
        initial_input = input("Enter the initial state (9 digits 0-8, e.g., 125340678): ")
        start_state = ConvertState_ToString(int(initial_input))
        if validate_input(start_state):
            break
        print("Invalid input! Make sure it has digits 0-8 exactly once.")

    while True:
        print("\n--- 8-Puzzle Search Menu ---")
        print("1. Breadth-First Search (BFS)")
        print("2. Depth-First Search (DFS)")
        print("3. Iterative Deepening (IDS)")
        print("4. A* Search (Manhattan)")
        print("5. A* Search (Euclidean)")
        print("6. Exit")

        choice = input("Enter your choice (1-6): ")
        if choice == '1':
            bfs_search(start_state, GOAL_STATE)
        elif choice == '2':
            dfs_search(start_state, GOAL_STATE)
        elif choice == "3":
            iterative_deepening_search(start_state, GOAL_STATE)
        elif choice == '4':
              a_star(start_state, Manhattan_Distance)
        elif choice == '5':
             a_star(start_state, Euclidean_Distance)
        elif choice == '6':
            print("Exiting program.")
            break
        else:
            print("Invalid choice. Please enter 1-6.")

# -------------------------------------------------------------------------------------
if __name__ == "__main__":
    menu()
