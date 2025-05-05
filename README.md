# Beluga Challenge Solver

A powerful A* search-based solver for the Beluga Challenge from the TUPLES project. This solver supports multiple heuristic strategies and incorporates domain-specific constraints.

---

## 🛠️ Project Overview

The **Beluga Challenge** simulates a complex planning problem involving the movement of aircraft parts between **Beluga aircraft**, **racks**, and **production lines**. The solver computes valid action plans using heuristic-guided search strategies.

---

## 📁 Folder Structure

Beluga-Challenge-Solver/
├── beluga_loader.py # Loads and parses input instance data
├── beluga_state.py # Defines state representation and transitions
├── beluga_actions.py # Action classes and valid operations
├── beluga_heuristic.py # Heuristic functions for planning
├── beluga_astar.py # A* search implementation
├── beluga_goal.py # Goal-checking mechanisms
├── beluga_utils.py # Visualization and utility helpers
├── beluga_verification.py # Plan verification logic
├── beluga_debug.py # Debugging utilities and trace tools
├── run_beluga_solver.py # Main script to run the solver
├── test_astar.py # Unit tests for A* search 
├── beluga_csp.py # CSP-based planning module
├── beluga_hybrid_solver.py # Hybrid approach combining CSP and search
├── run_hybrid_experiments.py # Script to run hybrid experiments
├── analyze_hybrid_results.py # Analyzer for hybrid experiment outputs
├── beluga_local_search.py # Local search strategy implementation
├── beluga_forward_checking.py # Forward-checking constraint solver
├── improved_analyze_results.py # Refined analysis scripts
├── improved_run_experiments.py # Improved experiment runner
├── problem_instances/ # Folder for JSON problem file(s)
├── prototypes/ # Folder for different prototypes
├── docs/ # Documentation and results (e.g., PDFs)
└── README.md # Project readme


## 🚀 How to Run

To execute the solver on a Beluga problem instance:

```bash
python run_beluga_solver.py <instance_file> [options]
```

## Options

```bash
--max-iterations: Maximum iterations for A* search (default: 10000)
--time-limit: Time limit in seconds (default: 60)
--debug: Run in debug mode for analysis
--output: Output file to save the plan
--heuristic: Heuristic variant to use (standard, weighted, production_focus)
```

## Example

Run original A* solver:
```bash
python run_beluga_solver.py problem_instances/problem_4_s46_j23_r2_oc51_f6.json --max-iterations 15000 --heuristic weighted
```

Run experiments:
```bash
python run_hybrid_experiments.py
```

Analyze results:
```bash
python analyze_hybrid_results.py
```

## Heuristic Variants

Standard: Baseline heuristic with equal weighting of components
Weighted: Prioritizes production requirements over flight processing
Production Focus: Strongly prioritizes completing the production schedule in the correct order

## Experiment Results
Benchmark comparisons for all heuristic variants can be found in the accompanying PDF in the /docs/ directory.

## 📌 Notes
All problem instances should be in .json format.

Ensure Python 3.7+ is installed with standard libraries (no third-party dependencies required).
