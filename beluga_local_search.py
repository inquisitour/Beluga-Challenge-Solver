"""
Local search implementation for the Beluga problem.
Implements randomized local search to escape local minima.
"""

import random
import time
import copy
from collections import deque

from beluga_goal import is_goal_state, check_goal_progress
from beluga_actions import MoveJigBetweenRacks, LoadJigToBeluga, UnloadJigFromBeluga, SendJigToProduction, ReturnEmptyJigFromFactory, ProcessNextFlight

class BelugaLocalSearch:
    """Implements a randomized local search for the Beluga problem."""
    
    def __init__(self, instance_data):
        """
        Initialize the local search.
        
        Args:
            instance_data: Problem instance data
        """
        self.instance_data = instance_data
        
    def solve(self, initial_state, best_progress, instance_data, time_limit=30, max_iterations=5000):
        """
        Attempt to find a solution using randomized local search.
        
        Args:
            initial_state: Initial state to start from
            best_progress: Dict with best progress made so far
            instance_data: Problem instance data
            time_limit: Time limit in seconds
            max_iterations: Maximum iterations
            
        Returns:
            List of actions forming the plan, or None if no plan found
        """
        print(f"Starting local search with time limit {time_limit}s and {max_iterations} iterations...")
        start_time = time.time()
        
        # Keep track of the best state found so far
        best_state = initial_state
        best_score = self._evaluate_state(best_state, instance_data)
        
        # Keep track of the path to the best state
        best_path = []
        
        # Create a queue of states to explore
        states_to_explore = deque([(initial_state, [])])  # (state, path)
        
        # Track visited states to avoid cycles
        visited_states = set()
        
        iterations = 0
        while states_to_explore and iterations < max_iterations:
            iterations += 1
            
            # Check time limit
            if time.time() - start_time > time_limit:
                print(f"Local search time limit reached after {iterations} iterations.")
                break
            
            # Get next state to explore
            current_state, path_so_far = states_to_explore.popleft()
            
            # Skip if already visited
            if current_state in visited_states:
                continue
                
            visited_states.add(current_state)
            
            # Check if this is a goal state
            if is_goal_state(current_state, instance_data):
                print(f"Local search found a solution after {iterations} iterations!")
                return path_so_far
            
            # Evaluate current state
            current_score = self._evaluate_state(current_state, instance_data)
            
            # Update best state if this is better
            if current_score > best_score:
                best_state = current_state
                best_score = current_score
                best_path = path_so_far
                
                print(f"Local search found better state with score {best_score}")
                progress = check_goal_progress(current_state, instance_data)
                print(f"Progress: Flights: {progress['flights_progress']}, Parts: {progress['parts_progress']}")
            
            # Generate possible moves
            possible_actions = self._get_random_actions(current_state, instance_data)
            
            # Add promising states to explore
            for action in possible_actions:
                next_state = current_state.get_next_state(action, instance_data)
                if next_state and next_state not in visited_states:
                    # Create a copy of the path and add this action
                    new_path = path_so_far.copy()
                    new_path.append(action)
                    
                    # Add to exploration queue
                    states_to_explore.append((next_state, new_path))
        
        print(f"Local search completed with best score {best_score} after {iterations} iterations.")
        if best_path:
            return best_path
        return None
    
    def _evaluate_state(self, state, instance_data):
        """
        Evaluate a state based on how close it is to the goal.
        
        Args:
            state: State to evaluate
            instance_data: Problem instance data
            
        Returns:
            Score value (higher is better)
        """
        score = 0
        
        # Get progress information
        progress = check_goal_progress(state, instance_data)
        
        # Extract progress values
        flights_processed = int(progress['flights_processed'])
        total_flights = int(progress['total_flights'])
        parts_produced = int(progress['parts_produced'])
        total_parts = int(progress['total_parts'])
        
        # Calculate score components
        flight_score = 100 * (flights_processed / total_flights if total_flights > 0 else 0)
        parts_score = 200 * (parts_produced / total_parts if total_parts > 0 else 0)
        
        # Combine scores
        score = flight_score + parts_score
        
        # Add bonus for completed flights and parts
        score += 50 * flights_processed + 100 * parts_produced
        
        return score
    
    def _get_random_actions(self, state, instance_data, num_actions=5):
        """
        Get a random sample of possible actions.
        
        Args:
            state: Current state
            instance_data: Problem instance data
            num_actions: Number of actions to return
            
        Returns:
            List of possible actions
        """
        all_actions = []
        
        # 1. Generate MoveJigBetweenRacks actions
        for from_rack_id, jigs in state.rack_jigs.items():
            if not jigs:
                continue
            
            # Check jigs at the edges
            for jig_id in [jigs[0], jigs[-1]] if len(jigs) > 0 else []:
                if jig_id not in jigs:
                    continue  # Skip if jig not found (shouldn't happen)
                
                # Try moving to each other rack
                for to_rack_id in state.rack_jigs.keys():
                    if from_rack_id != to_rack_id:
                        action = MoveJigBetweenRacks(jig_id, from_rack_id, to_rack_id)
                        if state.is_valid_action(action, instance_data):
                            all_actions.append(action)
        
        # 2. Generate SendJigToProduction actions
        production_schedule = []
        for line in instance_data.get('production_lines', []):
            production_schedule.extend(line.get('schedule', []))
        
        for rack_id, jigs in state.rack_jigs.items():
            if not jigs:
                continue
            
            # Check jigs at factory-side edge
            if len(jigs) > 0:
                jig_id = jigs[0]  # Factory-side jig
                
                # Check if jig is in production schedule and still loaded
                loaded, part_id = state.jig_status.get(jig_id, (False, ""))
                if jig_id in production_schedule and loaded:
                    action = SendJigToProduction(jig_id, rack_id)
                    if state.is_valid_action(action, instance_data):
                        all_actions.append(action)
        
        # 3. Generate ReturnEmptyJigFromFactory actions
        for jig_id in state.factory_jigs:
            # Check if jig is empty
            loaded, _ = state.jig_status.get(jig_id, (False, ""))
            if not loaded:
                # Try returning to each rack
                for rack_id in state.rack_jigs.keys():
                    action = ReturnEmptyJigFromFactory(jig_id, rack_id)
                    if state.is_valid_action(action, instance_data):
                        all_actions.append(action)
        
        # 4. Generate ProcessNextFlight action if not at the last flight
        if state.current_flight_idx < len(instance_data.get('flights', [])) - 1:
            action = ProcessNextFlight()
            if state.is_valid_action(action, instance_data):
                all_actions.append(action)
        
        # Randomly sample actions, ensuring at least one of each type if possible
        selected_actions = []
        
        # First, categorize actions by type
        actions_by_type = {
            "move": [a for a in all_actions if isinstance(a, MoveJigBetweenRacks)],
            "produce": [a for a in all_actions if isinstance(a, SendJigToProduction)],
            "return": [a for a in all_actions if isinstance(a, ReturnEmptyJigFromFactory)],
            "flight": [a for a in all_actions if isinstance(a, ProcessNextFlight)]
        }
        
        # Try to include one of each type
        for action_type in actions_by_type:
            if actions_by_type[action_type]:
                selected_actions.append(random.choice(actions_by_type[action_type]))
        
        # Fill remaining slots with random actions
        remaining_actions = [a for a in all_actions if a not in selected_actions]
        remaining_slots = num_actions - len(selected_actions)
        
        if remaining_actions and remaining_slots > 0:
            # Randomly select remaining actions
            selected_actions.extend(random.sample(
                remaining_actions, 
                min(remaining_slots, len(remaining_actions))
            ))
        
        return selected_actions