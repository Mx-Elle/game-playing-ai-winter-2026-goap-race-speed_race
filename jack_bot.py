from collections import defaultdict
import heapq
from game_world.racetrack import RaceTrack

Point = tuple[int, int]


def bot_action(location: Point, track: RaceTrack) -> Point:

    # if there is only one legal move
    legal_move = []
    max_x, max_y = track.active.shape
    for opt in [(1, 0), (0, 1), (-1, 0), (0, -1)]:
        possible_move = (location[0] + opt[0], location[1] + opt[1])
        if (
            possible_move[0] < 0
            or possible_move[1] < 0
            or possible_move[0] >= max_x
            or possible_move[1] >= max_y
            or (
                track.active[possible_move[0]][possible_move[1]] == 1
                and track.walls[possible_move[0]][possible_move[1]] != 0
            )
        ):
            continue
        legal_move.append(opt)

    if len(legal_move) == 1:
        return legal_move[0]
    path = astar(location, track)

    if path is None:
        print('bad')
        return (0, 0)
    next = path.pop(0)
    return (next[0] - location[0], next[1] - location[1])


def distance(point_a: Point, point_b: Point):
    return abs(point_b[0] - point_a[0]) + abs(point_b[1] - point_a[1])


def astar(start_point: Point, track: RaceTrack, end_point: Point | None = None) -> list[Point] | None:
    # input points, output list of moves
    if not end_point:
        end_point = track.target
    found_path: bool = False
    frontier = []
    tie_break: int = 0
    heapq.heappush(frontier, (distance(start_point, end_point), tie_break, start_point))
    g_scores = defaultdict(lambda: float("inf"))
    g_scores[start_point] = 0
    backtracking: dict[Point, Point | None] = {start_point: None}
    curr: Point = start_point
    max_x, max_y = track.active.shape

    while frontier != []:
        curr_f, _, curr = heapq.heappop(frontier)

        if curr == end_point:
            found_path = True
            break

        if curr_f > g_scores[curr] + distance(curr, end_point):
            continue

        for opt in [(1, 0), (0, 1), (-1, 0), (0, -1)]:
            neighbor = (curr[0] + opt[0], curr[1] + opt[1])
            if (
                neighbor[0] < 0
                or neighbor[1] < 0
                or neighbor[0] >= max_x
                or neighbor[1] >= max_y
                or (
                    track.active[neighbor[0]][neighbor[1]] == 1
                    and track.walls[neighbor[0]][neighbor[1]] != 0
                )
            ):
                continue
            tie_break += 1
            new_cost: float = g_scores[curr] + distance(curr, neighbor)

            if new_cost < g_scores[neighbor]:
                heapq.heappush(
                    frontier,
                    (new_cost + distance(neighbor, end_point), tie_break, neighbor),
                )
                backtracking[neighbor] = curr
                g_scores[neighbor] = new_cost

    if (
        not found_path
    ):  # if the while ends and we never found a path then there are no paths
        print('path not found')
        return None

    last: Point | None = curr
    moves: list[Point] = []
    while last is not None:
        moves.append(last)
        last = backtracking[last]

    return moves[::-1][1:]
