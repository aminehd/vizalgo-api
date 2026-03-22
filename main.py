"""
vizalgo backend — FastAPI

Local:
  uvicorn infra.backend.main:app --reload --port 8000

Endpoints:
  GET  /problems                    — list available problems
  GET  /problems/{id}/frames        — all snapshots as JSON (pre-generated)
"""

import sys
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, ROOT)

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="vizalgo API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_engine(problem, title, patterns):
    from vizalgo import VizEngine, RenderConfig, GridPanel, QueuePanel, Counter
    engine = VizEngine(problem, title)
    engine.line_speed = 0.6
    engine.snap_speed = 1.5
    engine.config = RenderConfig(panels=[
        GridPanel("grid"),
        QueuePanel("queue"),
        Counter("count"),
    ])
    return engine

def _run_examples(engine, fn, examples):
    runs = []
    for i, grid in enumerate(examples):
        engine.run(fn, grid)
        runs.append({
            "example":      i + 1,
            "snapshots":    _serialize_snapshots(engine.snapshots),
            "source_lines": engine.source_lines,
        })
    return runs

def _serialize_snapshots(snapshots) -> list:
    result = []
    for s in snapshots:
        data = {}
        for k, v in s.data.items():
            if isinstance(v, (list, tuple, dict, int, float, str, bool, type(None))):
                data[k] = v
            else:
                data[k] = str(v)
        result.append({
            "line":        s.line,
            "description": s.description,
            "duration":    s.duration,
            "data":        data,
        })
    return result

# ---------------------------------------------------------------------------
# LC 200 — Number of Islands
# ---------------------------------------------------------------------------

def _load_lc200():
    from vizalgo import VizEngine, RenderConfig, GridPanel, QueuePanel, Counter
    from vizalgo.core.state import VizGrid, VizQueue

    engine = _make_engine("LC 200", "Number of Islands", ["BFS", "Grid"])

    @engine.solution
    @engine.show
    def numIslands(raw_grid):
        grid  = VizGrid(raw_grid)
        rows, cols = grid.rows, grid.cols
        count = 0
        queue = VizQueue()
        engine.snap("Initial grid")

        def bfs(r, c):
            nonlocal count
            queue.push((r, c))
            grid[r][c] = 2
            grid.cursor    = (r, c)
            grid.neighbors = []
            engine.snap(f"BFS island {count} from ({r},{c})")
            while queue:
                cr, cc = queue.pop()
                grid[cr][cc]   = 2
                grid.cursor    = (cr, cc)
                grid.neighbors = []
                engine.snap(f"Marking ({cr},{cc})")
                for dr, dc in [(0,1),(0,-1),(1,0),(-1,0)]:
                    nr, nc = cr+dr, cc+dc
                    if grid.valid(nr, nc) and grid[nr][nc] == 1:
                        grid[nr][nc] = 2
                        queue.push((nr, nc))
                        grid.neighbors.append((nr, nc))
                        engine.snap(f"Enqueue ({nr},{nc})")

        for r in range(rows):
            for c in range(cols):
                grid.cursor    = (r, c)
                grid.neighbors = []
                if grid[r][c] == 1:
                    count += 1
                    engine.snap(f"Found island {count} at ({r},{c})")
                    bfs(r, c)

        engine.snap(f"Done — {count} island(s)")
        return count

    examples = [
        [["1","1","0","0","0"],
         ["1","1","0","0","0"],
         ["0","0","1","0","0"],
         ["0","0","0","1","1"]],
        [["1","1","1"],
         ["0","1","0"],
         ["1","1","1"]],
    ]

    return {
        "id":         "lc200",
        "problem":    "LC 200",
        "title":      "Number of Islands",
        "difficulty": "Medium",
        "pattern":    ["BFS", "Grid"],
        "runs":       _run_examples(engine, numIslands, examples),
    }

# ---------------------------------------------------------------------------
# LC 994 — Rotting Oranges
# ---------------------------------------------------------------------------

def _load_lc994():
    from vizalgo import VizEngine, RenderConfig, GridPanel, QueuePanel, Counter
    from vizalgo.core.state import VizGrid, VizQueue

    engine = VizEngine("LC 994", "Rotting Oranges")
    engine.line_speed = 0.6
    engine.snap_speed = 1.5
    engine.config = RenderConfig(panels=[
        GridPanel("grid"),
        QueuePanel("queue"),
        Counter("minutes"),
    ])

    @engine.solution
    @engine.show
    def orangesRotting(raw_grid):
        grid    = VizGrid(raw_grid)
        rows, cols = grid.rows, grid.cols
        queue   = VizQueue()
        fresh   = 0
        minutes = 0
        engine.snap("Initial grid")

        # Seed queue with all initially rotten oranges
        for r in range(rows):
            for c in range(cols):
                if grid[r][c] == 2:
                    queue.push((r, c, 0))
                elif grid[r][c] == 1:
                    fresh += 1

        engine.snap(f"{fresh} fresh oranges, {len(queue)} rotten seeds")

        while queue:
            r, c, t = queue.pop()
            grid.cursor    = (r, c)
            grid.neighbors = []
            minutes = max(minutes, t)
            engine.snap(f"Spread from ({r},{c}) t={t}")
            for dr, dc in [(0,1),(0,-1),(1,0),(-1,0)]:
                nr, nc = r+dr, c+dc
                if grid.valid(nr, nc) and grid[nr][nc] == 1:
                    grid[nr][nc] = 2
                    fresh -= 1
                    queue.push((nr, nc, t+1))
                    grid.neighbors.append((nr, nc))
                    engine.snap(f"Rot ({nr},{nc}) at t={t+1}")

        result = minutes if fresh == 0 else -1
        engine.snap(f"Done — {result}")
        return result

    examples = [
        [[2,1,1],[1,1,0],[0,1,1]],
        [[2,1,1],[0,1,1],[1,0,1]],
        [[0,2]],
    ]

    return {
        "id":         "lc994",
        "problem":    "LC 994",
        "title":      "Rotting Oranges",
        "difficulty": "Medium",
        "pattern":    ["BFS", "Grid"],
        "runs":       _run_examples(engine, orangesRotting, examples),
    }

# ---------------------------------------------------------------------------
# LC 560 — Subarray Sum Equals K
# ---------------------------------------------------------------------------

def _load_lc560():
    from collections import defaultdict
    from vizalgo import VizEngine

    engine = VizEngine("LC 560", "Subarray Sum Equals K")
    engine.line_speed = 0.6
    engine.snap_speed = 1.5

    @engine.solution
    @engine.show(mark=lambda locs: {
        "nums": {"cursor": locs.get("i")},
        "acc":  {"highlight": locs.get("prefix_sum", 0) - locs.get("k", 0)},
    })
    def subarray_sum(nums: list, k: int) -> int:
        acc = defaultdict(int)
        acc[0] = 1
        res = 0
        prefix_sum = 0

        for i, num in enumerate(nums):
            prefix_sum += num
            res += acc[prefix_sum - k]
            acc[prefix_sum] += 1

        return res

    examples = [
        {"nums": [1, 1, 1],         "k": 2},
        {"nums": [1, 2, 3],         "k": 3},
        {"nums": [1, -1, 1, -1, 1], "k": 0},
    ]

    runs = []
    for i, ex in enumerate(examples):
        engine.snapshots = []
        subarray_sum(ex["nums"], ex["k"])
        runs.append({
            "example":      i + 1,
            "snapshots":    _serialize_snapshots(engine.snapshots),
            "source_lines": engine.source_lines,
        })

    return {
        "id":         "lc560",
        "problem":    "LC 560",
        "title":      "Subarray Sum Equals K",
        "difficulty": "Medium",
        "pattern":    ["Prefix Sum", "Hashmap"],
        "runs":       runs,
    }

# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

PROBLEMS = {
    "lc200": _load_lc200,
    "lc994": _load_lc994,
    "lc560": _load_lc560,
}

PROBLEM_META = {
    "lc200": {"id": "lc200", "title": "Number of Islands",      "difficulty": "Medium", "pattern": ["BFS", "Grid"]},
    "lc994": {"id": "lc994", "title": "Rotting Oranges",        "difficulty": "Medium", "pattern": ["BFS", "Grid"]},
    "lc560": {"id": "lc560", "title": "Subarray Sum Equals K",  "difficulty": "Medium", "pattern": ["Prefix Sum", "Hashmap"]},
}

_cache: dict = {}

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/")
def root():
    return {"status": "ok", "service": "vizalgo API"}

@app.get("/problems")
def list_problems():
    return {"problems": list(PROBLEM_META.values())}

@app.get("/problems/{problem_id}/frames")
def get_frames(problem_id: str):
    if problem_id not in PROBLEMS:
        raise HTTPException(status_code=404, detail=f"Unknown problem: {problem_id}")
    if problem_id not in _cache:
        print(f"  Computing frames for {problem_id}...")
        _cache[problem_id] = PROBLEMS[problem_id]()
    return _cache[problem_id]

@app.post("/run")
def run_code(req: BaseModel):
    raise HTTPException(status_code=501, detail="Not yet implemented")
