"""
Network-level validation module.
"""

from typing import List, Dict, Any
from loguru import logger

from ..core.topology_builder import NetworkTopology
from ..core.config_parser import NetworkDevice
from .config_validator import ValidationResult


class NetworkValidator:
    """Validates network-level configurations and topology."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize network validator."""
        self.config = config
        self.max_hops = config.get('validation', {}).get('max_hops', 15)
        self.min_bandwidth = config.get('validation', {}).get('min_bandwidth', '10Mbps')
    
    def validate_network_topology(self, topology: NetworkTopology) -> List[ValidationResult]:
        """
        Validate overall network topology.
        
        Args:
            topology: Network topology to validate
            
        Returns:
            List of validation results
        """
        results = []
        
        results.extend(self._validate_connectivity(topology))
        results.extend(self._validate_redundancy(topology))
        results.extend(self._validate_scalability(topology))
        results.extend(self._validate_performance(topology))
        
        return results
    
    def _validate_connectivity(self, topology: NetworkTopology) -> List[ValidationResult]:
        """Validate network connectivity."""
        results = []
        
        # Check if all devices are reachable
        if len(topology.devices) > 1 and len(topology.links) == 0:
            results.append(ValidationResult(
                check_name="no_connectivity",
                status="fail",
                message="No network links found - devices appear to be isolated",
                severity="critical"
            ))
        
        # Check for network partitions (simplified)
        connected_devices = set()
        if topology.links:
            # Start from first device and see how many we can reach
            start_device = topology.links[0].source_device
            to_visit = [start_device]
            visited = set()
            
            while to_visit:
                current = to_visit.pop()
                if current in visited:
                    continue
                visited.add(current)
                
                # Find connected devices
                for link in topology.links:
                    if link.source_device == current and link.target_device not in visited:
                        to_visit.append(link.target_device)
                    elif link.target_device == current and link.source_device not in visited:
                        to_visit.append(link.source_device)
            
            # Check if all devices are reachable
            all_devices = {device.name for device in topology.devices}
            unreachable = all_devices - visited
            
            if unreachable:
                results.append(ValidationResult(
                    check_name="network_partition",
                    status="fail",
                    message=f"Network partition detected - unreachable devices: {', '.join(unreachable)}",
                    severity="high"
                ))
        
        return results
    
    def _validate_redundancy(self, topology: NetworkTopology) -> List[ValidationResult]:
        """Validate network redundancy."""
        results = []
        
        # Check for single points of failure
        critical_devices = []
        
        for device in topology.devices:
            # Count connections for this device
            connections = sum(1 for link in topology.links 
                            if link.source_device == device.name or link.target_device == device.name)
            
            if connections == 1 and device.device_type in ['router', 'switch']:
                critical_devices.append(device.name)
        
        if critical_devices:
            results.append(ValidationResult(
                check_name="single_points_of_failure",
                status="warning",
                message=f"Single points of failure detected: {', '.join(critical_devices)}",
                severity="medium"
            ))
        
        # Check for adequate redundancy in core network
        router_count = sum(1 for d in topology.devices if d.device_type == 'router')
        if router_count > 2:
            # Calculate average connections per router
            router_connections = {}
            for link in topology.links:
                source_device = next((d for d in topology.devices if d.name == link.source_device), None)
                target_device = next((d for d in topology.devices if d.name == link.target_device), None)
                
                if source_device and source_device.device_type == 'router':
                    router_connections[link.source_device] = router_connections.get(link.source_device, 0) + 1
                if target_device and target_device.device_type == 'router':
                    router_connections[link.target_device] = router_connections.get(link.target_device, 0) + 1
            
            if router_connections:
                avg_connections = sum(router_connections.values()) / len(router_connections)
                if avg_connections < 2:
                    results.append(ValidationResult(
                        check_name="insufficient_redundancy",
                        status="warning",
                        message=f"Low redundancy in core network - average {avg_connections:.1f} connections per router",
                        severity="medium"
                    ))
        
        return results
    
    def _validate_scalability(self, topology: NetworkTopology) -> List[ValidationResult]:
        """Validate network scalability."""
        results = []
        
        # Check network diameter (maximum hops between any two devices)
        max_path_length = self._calculate_network_diameter(topology)
        
        if max_path_length > self.max_hops:
            results.append(ValidationResult(
                check_name="excessive_network_diameter",
                status="warning",
                message=f"Network diameter ({max_path_length} hops) exceeds recommended maximum ({self.max_hops})",
                severity="medium"
            ))
        
        # Check for hierarchical design
        device_types = {}
        for device in topology.devices:
            device_types[device.device_type] = device_types.get(device.device_type, 0) + 1
        
        total_devices = len(topology.devices)
        if total_devices > 10:
            # For larger networks, recommend hierarchical design
            if device_types.get('switch', 0) == 0 and device_types.get('router', 0) > 5:
                results.append(ValidationResult(
                    check_name="flat_network_design",
                    status="warning",
                    message="Large flat network detected - consider hierarchical design with switches",
                    severity="low"
                ))
        
        return results
    
    def _validate_performance(self, topology: NetworkTopology) -> List[ValidationResult]:
        """Validate network performance characteristics."""
        results = []
        
        # Check for bandwidth bottlenecks
        from ..utils.helpers import parse_bandwidth
        min_bandwidth_bps = parse_bandwidth(self.min_bandwidth)
        
        low_bandwidth_links = []
        for link in topology.links:
            if link.bandwidth:
                link_bw_bps = parse_bandwidth(link.bandwidth)
                if link_bw_bps < min_bandwidth_bps:
                    low_bandwidth_links.append(f"{link.source_device}-{link.target_device}")
        
        if low_bandwidth_links:
            results.append(ValidationResult(
                check_name="low_bandwidth_links",
                status="warning",
                message=f"Links with bandwidth below {self.min_bandwidth}: {', '.join(low_bandwidth_links)}",
                severity="medium"
            ))
        
        # Check for potential congestion points
        device_load = {}
        for link in topology.links:
            device_load[link.source_device] = device_load.get(link.source_device, 0) + 1
            device_load[link.target_device] = device_load.get(link.target_device, 0) + 1
        
        high_load_devices = [device for device, load in device_load.items() if load > 5]
        if high_load_devices:
            results.append(ValidationResult(
                check_name="high_connection_density",
                status="warning",
                message=f"Devices with high connection density (>5): {', '.join(high_load_devices)}",
                severity="low"
            ))
        
        return results
    
    def _calculate_network_diameter(self, topology: NetworkTopology) -> int:
        """Calculate network diameter using simple BFS."""
        if not topology.links:
            return 0
        
        # Build adjacency list
        graph = {}
        for device in topology.devices:
            graph[device.name] = []
        
        for link in topology.links:
            graph[link.source_device].append(link.target_device)
            graph[link.target_device].append(link.source_device)
        
        max_distance = 0
        
        # Calculate shortest paths from each device
        for start_device in graph:
            distances = self._bfs_distances(graph, start_device)
            if distances:
                max_distance = max(max_distance, max(distances.values()))
        
        return max_distance
    
    def _bfs_distances(self, graph: Dict[str, List[str]], start: str) -> Dict[str, int]:
        """Calculate distances from start node using BFS."""
        distances = {start: 0}
        queue = [start]
        
        while queue:
            current = queue.pop(0)
            current_distance = distances[current]
            
            for neighbor in graph.get(current, []):
                if neighbor not in distances:
                    distances[neighbor] = current_distance + 1
                    queue.append(neighbor)
        
        return distances