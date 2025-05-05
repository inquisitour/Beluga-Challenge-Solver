"""
CSP components for the Beluga problem.
This file defines the constraint satisfaction problem representation
of the Beluga XL cargo management problem.
"""

from typing import Dict, List, Set, Tuple, FrozenSet, Any
from collections import defaultdict

class BelugaCSP:
    """Representation of the Beluga problem as a constraint satisfaction problem."""
    
    def __init__(self, state, instance_data):
        """
        Initialize a CSP representation based on the current state.
        
        Args:
            state: Current BelugaState
            instance_data: Problem instance data
        """
        self.state = state
        self.instance_data = instance_data
        
        # Extract the domains for each decision variable
        self.domains = self._extract_domains()
        
        # Extract constraints
        self.constraints = self._extract_constraints()
    
    def _extract_domains(self) -> Dict[str, List[Any]]:
        """
        Extract the domains for each decision variable in the problem.
        
        Returns:
            Dict mapping variable names to their domains
        """
        domains = {}
        
        # 1. Jig assignment domains - where each jig can go
        for jig_id in self.instance_data.get('jigs', {}):
            domains[f"jig_{jig_id}"] = self._get_jig_domain(jig_id)
        
        # 2. Flight processing domains - order of flight processing
        current_flight_idx = self.state.current_flight_idx
        total_flights = len(self.instance_data.get('flights', []))
        
        for i in range(current_flight_idx, total_flights):
            domains[f"flight_{i}"] = list(range(current_flight_idx, total_flights))
        
        # 3. Production sequence domains - order of part production
        production_schedule = []
        for line in self.instance_data.get('production_lines', []):
            production_schedule.extend(line.get('schedule', []))
        
        for i, jig_id in enumerate(production_schedule):
            if jig_id not in self.state.produced_parts:
                domains[f"prod_{jig_id}"] = list(range(len(production_schedule)))
                
        return domains
    
    def _get_jig_domain(self, jig_id: str) -> List[str]:
        """
        Get the domain of possible locations for a jig.
        
        Args:
            jig_id: ID of the jig
            
        Returns:
            List of possible locations for the jig
        """
        # Current location of the jig
        current_location = self.state.get_jig_location(jig_id)
        
        # Potential locations include racks, beluga, factory
        potential_locations = []
        
        # Can only be in one of the racks
        for rack_id in self.state.rack_jigs.keys():
            potential_locations.append(rack_id)
        
        # Can be in Beluga during flight loading/unloading
        potential_locations.append("beluga")
        
        # Can be in factory during production
        potential_locations.append("factory")
        
        return potential_locations
    
    def _extract_constraints(self) -> List[Tuple]:
        """
        Extract the constraints for the CSP.
        
        Returns:
            List of constraints as tuples (var1, var2, constraint_func)
        """
        constraints = []
        
        # 1. Rack capacity constraints
        for rack_id, jigs in self.state.rack_jigs.items():
            # Find rack size
            rack_size = 0
            for rack in self.instance_data.get('racks', []):
                if rack.get('name') == rack_id:
                    rack_size = rack.get('size', 0)
                    break
            
            # Add capacity constraint for each pair of jigs that might go to this rack
            jig_vars = [f"jig_{jig_id}" for jig_id in self.instance_data.get('jigs', {})]
            for i, var1 in enumerate(jig_vars):
                for var2 in jig_vars[i+1:]:
                    constraints.append((var1, var2, 
                        lambda v1, v2, r=rack_id, rs=rack_size: 
                            not (v1 == r and v2 == r) or self._check_rack_capacity(r, rs)))
        
        # 2. Flight precedence constraints
        flight_vars = [f"flight_{i}" for i in range(
            self.state.current_flight_idx, 
            len(self.instance_data.get('flights', [])))]
        
        for i, var1 in enumerate(flight_vars):
            for j, var2 in enumerate(flight_vars):
                if i < j:  # Flight i must be processed before flight j
                    constraints.append((var1, var2, lambda v1, v2: v1 < v2))
        
        # 3. Production precedence constraints
        production_lines = self.instance_data.get('production_lines', [])
        for line in production_lines:
            schedule = line.get('schedule', [])
            for i in range(len(schedule) - 1):
                var1 = f"prod_{schedule[i]}"
                var2 = f"prod_{schedule[i+1]}"
                if var1 in self.domains and var2 in self.domains:
                    constraints.append((var1, var2, lambda v1, v2: v1 < v2))
        
        return constraints
    
    def _check_rack_capacity(self, rack_id: str, rack_size: int) -> bool:
        """
        Check if adding another jig to the rack would exceed its capacity.
        
        Args:
            rack_id: ID of the rack
            rack_size: Size limit of the rack
            
        Returns:
            True if capacity constraint is satisfied, False otherwise
        """
        # Get current occupancy
        current_occupancy = 0
        for jig_id in self.state.rack_jigs.get(rack_id, ()):
            # Get the jig type
            jig_type = self.instance_data['jigs'][jig_id]['type']
            
            # Determine if jig is loaded or empty
            loaded, _ = self.state.jig_status.get(jig_id, (False, ""))
            
            # Get the size from jig_types
            if loaded:
                jig_size = self.instance_data['jig_types'][jig_type]['size_loaded']
            else:
                jig_size = self.instance_data['jig_types'][jig_type]['size_empty']
            
            current_occupancy += jig_size
        
        # There's room for at least one more jig
        return current_occupancy < rack_size
    
    def arc_consistent(self) -> bool:
        """
        Check if the CSP is arc consistent.
        
        Returns:
            True if arc consistent, False otherwise
        """
        # Simplified arc consistency check
        for var1, domain1 in self.domains.items():
            for var2, domain2 in self.domains.items():
                if var1 != var2:
                    # Find constraints between var1 and var2
                    for v1, v2, constraint_func in self.constraints:
                        if (v1 == var1 and v2 == var2) or (v1 == var2 and v2 == var1):
                            # Check if there's at least one value in domain1 that
                            # is consistent with at least one value in domain2
                            consistent = False
                            for val1 in domain1:
                                for val2 in domain2:
                                    if constraint_func(val1, val2):
                                        consistent = True
                                        break
                                if consistent:
                                    break
                            
                            if not consistent:
                                return False
        
        return True
    
    def reduce_domains(self) -> bool:
        """
        Apply constraint propagation to reduce domains.
        Similar to AC-3 algorithm for arc consistency.
        
        Returns:
            True if domains were successfully reduced, False if inconsistency detected
        """
        # Queue of arcs to process
        arcs = []
        for var1, var2, _ in self.constraints:
            arcs.append((var1, var2))
            arcs.append((var2, var1))  # Bidirectional
        
        while arcs:
            var1, var2 = arcs.pop(0)
            
            # Skip if variables not in domains
            if var1 not in self.domains or var2 not in self.domains:
                continue
                
            # Find the relevant constraint
            constraint = None
            for v1, v2, constraint_func in self.constraints:
                if (v1 == var1 and v2 == var2) or (v1 == var2 and v2 == var1):
                    constraint = constraint_func
                    break
            
            if constraint is None:
                continue
                
            # Check if we need to revise the domain of var1
            if self._revise_domain(var1, var2, constraint):
                # Check if domain is empty
                if not self.domains[var1]:
                    return False  # Inconsistency detected
                    
                # Add affected arcs back to the queue
                for v1, v2, _ in self.constraints:
                    if v2 == var1 and v1 != var2:
                        arcs.append((v1, var1))
        
        return True
    
    def _revise_domain(self, var1: str, var2: str, constraint) -> bool:
        """
        Revise the domain of var1 with respect to var2.

        Args:
            var1: First variable
            var2: Second variable
            constraint: Constraint function between var1 and var2
            
        Returns:
            True if domain was revised, False otherwise
        """
        revised = False

        domain1 = list(self.domains[var1])  # Copy to avoid modifying during iteration
        to_remove = []
        for val1 in domain1:
            # Check if there's at least one value in domain2 that satisfies the constraint
            satisfies = False
            for val2 in self.domains[var2]:
                if constraint(val1, val2):
                    satisfies = True
                    break
            
            # If no such value exists, mark for removal
            if not satisfies:
                to_remove.append(val1)
                revised = True

        # Remove values, but ensure we don't empty the domain completely
        if len(to_remove) < len(domain1):  # Don't remove everything
            for val in to_remove:
                self.domains[var1].remove(val)

        return revised

    def get_domain_reduction_heuristics(self):
        """
        Get information about domain sizes for heuristic computation.
        
        Returns:
            Dict with domain size information
        """
        return {
            'domain_sizes': {var: len(domain) for var, domain in self.domains.items()},
            'smallest_domain': min(self.domains.items(), key=lambda x: len(x[1])) if self.domains else None,
            'largest_domain': max(self.domains.items(), key=lambda x: len(x[1])) if self.domains else None,
        }