"""
Forward checking implementation for the Beluga problem.
Implements the forward checking algorithm for constraint propagation.
"""

from beluga_csp import BelugaCSP
from typing import Dict, List, Optional, Tuple, Any

class BelugaForwardChecker:
    """Implements forward checking for the Beluga problem."""
    
    def __init__(self, state, instance_data):
        """
        Initialize the forward checker.
        
        Args:
            state: Current BelugaState
            instance_data: Problem instance data
        """
        self.state = state
        self.instance_data = instance_data
        self.csp = BelugaCSP(state, instance_data)
    
    def check_forward(self) -> Tuple[bool, Dict[str, Any]]:
        """
        Perform forward checking to reduce future domains.
        
        Returns:
            Tuple of (success, heuristic_info)
            - success: True if forward checking succeeds, False if inconsistency detected
            - heuristic_info: Information about domains for heuristic computation
        """
        # Apply domain reduction
        success = self.csp.reduce_domains()
        
        # Get domain information for heuristics
        heuristic_info = self.csp.get_domain_reduction_heuristics()
        
        return success, heuristic_info
    
    def get_most_constrained_rack(self) -> Optional[str]:
        """
        Find the most constrained rack based on available space.
        
        Returns:
            ID of the most constrained rack, or None if no racks
        """
        if not self.state.rack_jigs:
            return None
            
        rack_constraints = {}
        
        for rack_id, jigs in self.state.rack_jigs.items():
            # Find rack size
            rack_size = 0
            for rack in self.instance_data.get('racks', []):
                if rack.get('name') == rack_id:
                    rack_size = rack.get('size', 0)
                    break
            
            # Calculate current occupancy
            current_occupancy = 0
            for jig_id in jigs:
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
            
            # Calculate available space
            available_space = rack_size - current_occupancy
            rack_constraints[rack_id] = available_space
        
        # Return the rack with the least available space
        return min(rack_constraints.items(), key=lambda x: x[1])[0] if rack_constraints else None
    
    def get_production_bottlenecks(self) -> List[str]:
        """
        Identify jigs that may be bottlenecks in the production schedule.
        
        Returns:
            List of jig IDs that are likely bottlenecks
        """
        bottlenecks = []
        
        # Collect production schedule
        production_schedule = []
        for line in self.instance_data.get('production_lines', []):
            production_schedule.extend(line.get('schedule', []))
        
        # Find jigs that are in production schedule but blocked in racks
        for jig_id in production_schedule:
            # Skip if already produced
            if jig_id in self.state.produced_parts:
                continue
                
            # Check if jig is in a rack
            location = self.state.get_jig_location(jig_id)
            if location not in ["beluga", "factory", None] and location in self.state.rack_jigs:
                rack_jigs = self.state.rack_jigs[location]
                
                # Check if jig is in the middle (not at an edge)
                if jig_id in rack_jigs:
                    jig_index = rack_jigs.index(jig_id)
                    if 0 < jig_index < len(rack_jigs) - 1:
                        bottlenecks.append(jig_id)
        
        return bottlenecks
    
    def get_flight_processing_constraints(self) -> Dict[str, Any]:
        """
        Get constraints related to flight processing.
        
        Returns:
            Dict with flight processing constraint information
        """
        flight_info = {}
        
        # Get flights
        flights = self.instance_data.get('flights', [])
        current_flight_idx = self.state.current_flight_idx
        
        if current_flight_idx < len(flights):
            current_flight = flights[current_flight_idx]
            
            # Count incoming jigs still in Beluga
            incoming_jigs = current_flight.get('incoming', [])
            incoming_in_beluga = sum(1 for jig_id in incoming_jigs if jig_id in self.state.beluga_jigs)
            
            # Count outgoing jigs needed
            outgoing_types = current_flight.get('outgoing', [])
            outgoing_needed = len(outgoing_types)
            
            flight_info = {
                'current_flight': current_flight_idx,
                'total_flights': len(flights),
                'incoming_jigs_remaining': incoming_in_beluga,
                'outgoing_jigs_needed': outgoing_needed
            }
        
        return flight_info