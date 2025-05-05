"""
Hybrid A* + CSP solver for the Beluga problem.
Combines A* search with CSP constraint propagation techniques.
"""

import heapq
import time
import random
from collections import defaultdict
from typing import Dict, List, Optional, Tuple, Any

from beluga_heuristic import heuristic
from beluga_goal import is_goal_state, check_goal_progress
from beluga_actions import MoveJigBetweenRacks, LoadJigToBeluga, UnloadJigFromBeluga, SendJigToProduction, ReturnEmptyJigFromFactory, ProcessNextFlight
from beluga_forward_checking import BelugaForwardChecker
from beluga_local_search import BelugaLocalSearch

class PriorityQueue:
    """A priority queue implementation for the A* search."""
    
    def __init__(self):
        self.elements = []
        self.entry_count = 0  # Used to break ties consistently
    
    def is_empty(self):
        return len(self.elements) == 0
    
    def put(self, item, priority):
        # Add entry_count to break ties and ensure FIFO behavior for equal priorities
        heapq.heappush(self.elements, (priority, self.entry_count, item))
        self.entry_count += 1
    
    def get(self):
        # Return the item, discarding priority and entry_count
        return heapq.heappop(self.elements)[2]

def get_all_possible_actions(state, instance_data, prioritize_goals=True, forward_checker=None):
    """
    Generate all possible actions from the current state, enhanced with forward checking.
    
    Args:
        state: Current BelugaState
        instance_data: Problem instance data
        prioritize_goals: Whether to prioritize actions that directly contribute to goal conditions
        forward_checker: Optional BelugaForwardChecker instance for constraint propagation
        
    Returns:
        List of possible actions, ordered by priority if prioritize_goals is True
    """
    # First, collect all possible actions
    all_actions = []
    
    # If we have a forward checker, use it to guide action generation
    bottleneck_jigs = []
    constrained_rack = None
    if forward_checker:
        # Perform forward checking
        success, _ = forward_checker.check_forward()
        
        # Get bottleneck jigs from production schedule
        bottleneck_jigs = forward_checker.get_production_bottlenecks()
        
        # Get most constrained rack
        constrained_rack = forward_checker.get_most_constrained_rack()
    
    # 1. Generate MoveJigBetweenRacks actions
    for from_rack_id, jigs in state.rack_jigs.items():
        if not jigs:
            continue
        
        # Check jigs at the edges
        for jig_id in [jigs[0], jigs[-1]] if len(jigs) > 0 else []:
            if jig_id not in jigs:
                continue  # Skip if jig not found (shouldn't happen)
            
            # Prioritize moving bottleneck jigs
            priority = "urgent" if jig_id in bottleneck_jigs else "move"
            
            # Try moving to each other rack
            for to_rack_id in state.rack_jigs.keys():
                if from_rack_id != to_rack_id:
                    # Lower priority if moving to constrained rack
                    if to_rack_id == constrained_rack:
                        temp_priority = "low"
                    else:
                        temp_priority = priority
                    
                    action = MoveJigBetweenRacks(jig_id, from_rack_id, to_rack_id)
                    if state.is_valid_action(action, instance_data):
                        all_actions.append((action, temp_priority))
    
    # 2. Generate SendJigToProduction actions
    production_schedule = []
    for line in instance_data.get('production_lines', []):
        production_schedule.extend(line.get('schedule', []))
    
    for rack_id, jigs in state.rack_jigs.items():
        if not jigs:
            continue
        
        # Check jigs at factory-side edge (here we assume the first jig is factory-side)
        if len(jigs) > 0:
            jig_id = jigs[0]  # Factory-side jig
            
            # Check if jig is in production schedule and still loaded
            loaded, part_id = state.jig_status.get(jig_id, (False, ""))
            if jig_id in production_schedule and loaded:
                action = SendJigToProduction(jig_id, rack_id)
                if state.is_valid_action(action, instance_data):
                    all_actions.append((action, "produce"))
    
    # 3. Generate ReturnEmptyJigFromFactory actions
    for jig_id in state.factory_jigs:
        # Check if jig is empty
        loaded, _ = state.jig_status.get(jig_id, (False, ""))
        if not loaded:
            # Try returning to each rack
            for rack_id in state.rack_jigs.keys():
                # Lower priority if returning to constrained rack
                priority = "low" if rack_id == constrained_rack else "return"
                
                action = ReturnEmptyJigFromFactory(jig_id, rack_id)
                if state.is_valid_action(action, instance_data):
                    all_actions.append((action, priority))
    
    # 4. Generate ProcessNextFlight action if not at the last flight
    if state.current_flight_idx < len(instance_data.get('flights', [])) - 1:
        action = ProcessNextFlight()
        if state.is_valid_action(action, instance_data):
            all_actions.append((action, "flight"))
    
    # 5. Generate LoadJigToBeluga and UnloadJigFromBeluga actions
    # For simplicity, we're not implementing these in this one-day version
    
    # If we're prioritizing goal-relevant actions, sort them
    if prioritize_goals:
        # Priority order: production > urgent > flight > return > move > low
        action_priority = {
            "produce": 0,    # Highest priority - directly contributes to production
            "urgent": 1,     # High priority - bottleneck jigs
            "flight": 2,     # Medium-high priority - needed for progress
            "return": 3,     # Medium priority - frees up factory
            "move": 4,       # Lower priority - general movement
            "low": 5         # Lowest priority - potentially problematic
        }
        
        # Sort by priority
        all_actions.sort(key=lambda x: action_priority[x[1]])
        
        # Extract just the actions
        return [action for action, _ in all_actions]
    else:
        # Return actions in original order
        return [action for action, _ in all_actions]

def hybrid_astar_search(initial_state, instance_data, max_iterations=10000, time_limit=60, 
                        heuristic_variant="standard", prioritize_actions=False,
                        use_forward_checking=True, use_random_restarts=False,
                        random_restart_threshold=3000):
    """
    Perform hybrid A* search with CSP techniques to find the optimal plan.
    
    Args:
        initial_state: The starting state
        instance_data: The problem instance data
        max_iterations: Maximum number of iterations (default: 10000)
        time_limit: Time limit in seconds (default: 60)
        heuristic_variant: Which heuristic to use (standard, weighted, production_focus)
        prioritize_actions: Whether to prioritize goal-relevant actions
        use_forward_checking: Whether to use forward checking for domain reduction
        use_random_restarts: Whether to use random restarts to escape local minima
        random_restart_threshold: Number of iterations before considering a random restart
        
    Returns:
        List of actions forming the plan, or None if no plan found
    """
    print(f"Starting hybrid A* search with '{heuristic_variant}' heuristic...")
    start_time = time.time()
    
    # Initialize data structures
    open_set = PriorityQueue()
    open_set.put(initial_state, 0)
    
    came_from = {}  # Maps state -> (previous_state, action)
    cost_so_far = {initial_state: 0}
    
    iterations = 0
    states_explored = 0
    best_progress = {'flights': 0, 'parts': 0}
    stagnation_counter = 0
    
    # For randomized restarts
    restart_states = []
    
    # Initialize forward checker if enabled
    forward_checker = None
    if use_forward_checking:
        forward_checker = BelugaForwardChecker(initial_state, instance_data)
    
    # Initialize local search if enabled
    local_search = None
    if use_random_restarts:
        local_search = BelugaLocalSearch(instance_data)
    
    # Main hybrid A* search loop
    while not open_set.is_empty() and iterations < max_iterations:
        iterations += 1
        
        # Check time limit
        if time.time() - start_time > time_limit:
            print(f"Time limit of {time_limit} seconds reached. Aborting search.")
            return None
        
        # Get the state with lowest estimated total cost
        current_state = open_set.get()
        states_explored += 1
        
        # Check for goal state
        if is_goal_state(current_state, instance_data):
            print(f"Goal reached after {iterations} iterations!")
            print(f"Total states explored: {states_explored}")
            print(f"Search time: {time.time() - start_time:.2f} seconds")
            
            # Reconstruct the plan
            return reconstruct_plan(came_from, current_state)
        
        # Check progress and print every 100 iterations
        if iterations % 100 == 0:
            progress = check_goal_progress(current_state, instance_data)
            flights_progress = int(progress['flights_progress'].split('/')[0])
            parts_progress = int(progress['parts_progress'].split('/')[0])
            
            print(f"Iteration {iterations}: Flights: {progress['flights_progress']}, Parts: {progress['parts_progress']}")
            
            # Check if we're making progress
            if flights_progress > best_progress['flights'] or parts_progress > best_progress['parts']:
                best_progress['flights'] = max(best_progress['flights'], flights_progress)
                best_progress['parts'] = max(best_progress['parts'], parts_progress)
                stagnation_counter = 0
                
                # Save this state as a potential restart point
                if use_random_restarts and current_state not in restart_states:
                    restart_states.append(current_state)
            else:
                stagnation_counter += 1
            
            # Check if we should do a random restart
            if use_random_restarts and stagnation_counter >= random_restart_threshold // 100:
                if restart_states:
                    print(f"Stagnation detected after {stagnation_counter * 100} iterations without progress.")
                    print("Performing random restart from a promising state...")
                    
                    # Pick a random state from promising states
                    restart_state = random.choice(restart_states)
                    
                    # Clear open set and start fresh from this state
                    open_set = PriorityQueue()
                    open_set.put(restart_state, 0)
                    
                    # Reset stagnation counter
                    stagnation_counter = 0
                    
                    # Continue search from new state
                    continue
        
        # Update forward checker with current state if enabled
        if use_forward_checking:
            forward_checker = BelugaForwardChecker(current_state, instance_data)
        
        # Generate all possible actions, possibly using forward checking
        actions = get_all_possible_actions(
            current_state, instance_data, prioritize_actions, forward_checker)
        
        # Explore each action
        for action in actions:
            # Get resulting state
            next_state = current_state.get_next_state(action, instance_data)
            if next_state is None:
                continue  # Invalid action/state
            
            # Calculate cost
            new_cost = cost_so_far[current_state] + 1  # Uniform cost
            
            # If state is new or we found a better path
            if next_state not in cost_so_far or new_cost < cost_so_far[next_state]:
                cost_so_far[next_state] = new_cost
                
                # Calculate heuristic - enhanced with forward checking
                h_value = heuristic(next_state, instance_data, variant=heuristic_variant)
                
                # Incorporate forward checking insights if enabled
                if use_forward_checking:
                    fc = BelugaForwardChecker(next_state, instance_data)
                    success, heuristic_info = fc.check_forward()
                    
                    # If forward checking reveals an inconsistency, increase heuristic
                    if not success:
                        h_value += 10  # Significant penalty for inconsistent states
                    
                    # Adjust heuristic based on domain sizes
                    if 'domain_sizes' in heuristic_info and heuristic_info['domain_sizes']:
                        # Add a small component based on domain restriction
                        h_value += 0.1 * (1.0 / min(heuristic_info['domain_sizes'].values()))

                    # Adjust heuristic based on domain sizes
                    if 'domain_sizes' in heuristic_info and heuristic_info['domain_sizes']:
                        # Add a safe check for empty domain_sizes dictionary
                        if heuristic_info['domain_sizes'] and min(heuristic_info['domain_sizes'].values(), default=1) > 0:
                            h_value += 0.1 * (1.0 / min(heuristic_info['domain_sizes'].values()))
                        else:
                            # Penalty for empty domains
                            h_value += 10  # Same penalty as for inconsistent states
                
                # Calculate priority
                priority = new_cost + h_value
                
                # Add to open set
                open_set.put(next_state, priority)
                came_from[next_state] = (current_state, action)
    
    # If we got here, search failed
    print(f"Search failed after {iterations} iterations.")
    print(f"Total states explored: {states_explored}")
    print(f"Search time: {time.time() - start_time:.2f} seconds")
    
    # If enabled, try local search as a last resort
    if use_random_restarts and local_search:
        print("Attempting local search as a final effort...")
        local_plan = local_search.solve(initial_state, best_progress, instance_data, time_limit=max(5, time_limit/10))
        if local_plan:
            print("Local search found a solution!")
            return local_plan
    
    return None

def reconstruct_plan(came_from, goal_state):
    """
    Reconstruct the plan by working backwards from the goal state.
    """
    actions = []
    current_state = goal_state
    
    while current_state in came_from:
        previous_state, action = came_from[current_state]
        actions.append(action)
        current_state = previous_state
    
    # Reverse the list since we worked backwards
    actions.reverse()
    return actions