"""
Configuration validation module.
"""

from typing import List, Dict, Any
from dataclasses import dataclass
from loguru import logger

from ..core.config_parser import NetworkDevice
from ..core.topology_builder import NetworkTopology


@dataclass
class ValidationResult:
    """Validation result for a specific check."""
    check_name: str
    status: str  # 'pass', 'fail', 'warning'
    message: str
    device: str = None
    severity: str = 'medium'  # 'low', 'medium', 'high', 'critical'


class ConfigValidator:
    """Validates network device configurations."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize validator with configuration."""
        self.config = config
    
    def validate_all(self, devices: List[NetworkDevice], topology: NetworkTopology) -> List[ValidationResult]:
        """
        Run all validation checks.
        
        Args:
            devices: List of network devices
            topology: Network topology
            
        Returns:
            List of validation results
        """
        logger.info("Starting configuration validation")
        
        results = []
        
        # Run individual validation checks
        results.extend(self._validate_duplicate_ips(devices))
        results.extend(self._validate_vlan_consistency(devices))
        results.extend(self._validate_gateway_addresses(devices))
        results.extend(self._validate_mtu_consistency(devices, topology))
        results.extend(self._validate_routing_protocols(devices))
        results.extend(self._validate_network_loops(topology))
        results.extend(self._validate_missing_components(devices, topology))
        
        logger.info(f"Validation completed: {len(results)} issues found")
        return results
    
    def _validate_duplicate_ips(self, devices: List[NetworkDevice]) -> List[ValidationResult]:
        """Check for duplicate IP addresses within same VLAN/subnet."""
        results = []
        ip_map = {}  # ip -> (device, interface, vlan)
        
        for device in devices:
            for interface in device.interfaces:
                if interface.ip_address:
                    key = interface.ip_address
                    vlan = interface.vlan or 0
                    
                    if key in ip_map:
                        existing_device, existing_interface, existing_vlan = ip_map[key]
                        if vlan == existing_vlan:  # Same VLAN
                            results.append(ValidationResult(
                                check_name="duplicate_ip_address",
                                status="fail",
                                message=f"Duplicate IP {key} found on {device.name}:{interface.name} and {existing_device}:{existing_interface} in VLAN {vlan}",
                                device=device.name,
                                severity="high"
                            ))
                    else:
                        ip_map[key] = (device.name, interface.name, vlan)
        
        return results
    
    def _validate_vlan_consistency(self, devices: List[NetworkDevice]) -> List[ValidationResult]:
        """Validate VLAN configuration consistency."""
        results = []
        vlan_names = {}  # vlan_id -> set of names
        
        for device in devices:
            for vlan_id, vlan_name in device.vlans.items():
                if vlan_id not in vlan_names:
                    vlan_names[vlan_id] = set()
                vlan_names[vlan_id].add(vlan_name)
        
        # Check for inconsistent VLAN names
        for vlan_id, names in vlan_names.items():
            if len(names) > 1:
                results.append(ValidationResult(
                    check_name="vlan_name_inconsistency",
                    status="warning",
                    message=f"VLAN {vlan_id} has inconsistent names: {', '.join(names)}",
                    severity="medium"
                ))
        
        return results
    
    def _validate_gateway_addresses(self, devices: List[NetworkDevice]) -> List[ValidationResult]:
        """Validate gateway address configurations."""
        results = []
        
        for device in devices:
            if device.device_type == 'router':
                # Check if router has at least one interface with IP
                has_ip_interface = any(
                    interface.ip_address for interface in device.interfaces
                )
                
                if not has_ip_interface:
                    results.append(ValidationResult(
                        check_name="router_no_ip_interface",
                        status="fail",
                        message=f"Router {device.name} has no interfaces with IP addresses configured",
                        device=device.name,
                        severity="high"
                    ))
        
        return results
    
    def _validate_mtu_consistency(self, devices: List[NetworkDevice], topology: NetworkTopology) -> List[ValidationResult]:
        """Check for MTU mismatches on connected interfaces."""
        results = []
        
        for link in topology.links:
            source_device = next((d for d in devices if d.name == link.source_device), None)
            target_device = next((d for d in devices if d.name == link.target_device), None)
            
            if source_device and target_device:
                source_interface = next((i for i in source_device.interfaces if i.name == link.source_interface), None)
                target_interface = next((i for i in target_device.interfaces if i.name == link.target_interface), None)
                
                if source_interface and target_interface:
                    source_mtu = source_interface.mtu or 1500  # Default MTU
                    target_mtu = target_interface.mtu or 1500
                    
                    if source_mtu != target_mtu:
                        results.append(ValidationResult(
                            check_name="mtu_mismatch",
                            status="warning",
                            message=f"MTU mismatch between {link.source_device}:{link.source_interface} ({source_mtu}) and {link.target_device}:{link.target_interface} ({target_mtu})",
                            severity="medium"
                        ))
        
        return results
    
    def _validate_routing_protocols(self, devices: List[NetworkDevice]) -> List[ValidationResult]:
        """Validate routing protocol configurations."""
        results = []
        
        router_count = sum(1 for d in devices if d.device_type == 'router')
        
        if router_count > 1:
            # Check if routers have routing protocols configured
            routers_without_routing = []
            
            for device in devices:
                if device.device_type == 'router':
                    if not device.routing_protocols:
                        routers_without_routing.append(device.name)
            
            if routers_without_routing:
                results.append(ValidationResult(
                    check_name="missing_routing_protocol",
                    status="warning",
                    message=f"Routers without routing protocols: {', '.join(routers_without_routing)}",
                    severity="medium"
                ))
            
            # Suggest BGP for larger networks
            if router_count > 5:
                bgp_routers = sum(1 for d in devices if d.device_type == 'router' and 
                                any(rp.protocol == 'bgp' for rp in d.routing_protocols))
                
                if bgp_routers == 0:
                    results.append(ValidationResult(
                        check_name="bgp_recommendation",
                        status="warning",
                        message=f"Consider implementing BGP for better scalability with {router_count} routers",
                        severity="low"
                    ))
        
        return results
    
    def _validate_network_loops(self, topology: NetworkTopology) -> List[ValidationResult]:
        """Check for potential network loops."""
        results = []
        
        # Simple loop detection - check if there are redundant paths without STP
        switch_devices = [d for d in topology.devices if d.device_type == 'switch']
        
        if len(switch_devices) > 2:
            # If we have multiple switches, check for STP configuration
            # This is simplified - in reality you'd check actual STP config
            results.append(ValidationResult(
                check_name="potential_loop_risk",
                status="warning",
                message=f"Multiple switches detected ({len(switch_devices)}). Ensure Spanning Tree Protocol is properly configured",
                severity="medium"
            ))
        
        return results
    
    def _validate_missing_components(self, devices: List[NetworkDevice], topology: NetworkTopology) -> List[ValidationResult]:
        """Check for missing network components."""
        results = []
        
        # Check for single points of failure
        device_connections = {}
        for link in topology.links:
            device_connections[link.source_device] = device_connections.get(link.source_device, 0) + 1
            device_connections[link.target_device] = device_connections.get(link.target_device, 0) + 1
        
        for device_name, connections in device_connections.items():
            if connections == 1:
                device = next((d for d in devices if d.name == device_name), None)
                if device and device.device_type in ['router', 'switch']:
                    results.append(ValidationResult(
                        check_name="single_point_of_failure",
                        status="warning",
                        message=f"Device {device_name} has only one connection - potential single point of failure",
                        device=device_name,
                        severity="medium"
                    ))
        
        # Check for isolated devices
        connected_devices = set()
        for link in topology.links:
            connected_devices.add(link.source_device)
            connected_devices.add(link.target_device)
        
        for device in devices:
            if device.name not in connected_devices:
                results.append(ValidationResult(
                    check_name="isolated_device",
                    status="fail",
                    message=f"Device {device.name} appears to be isolated (no network connections found)",
                    device=device.name,
                    severity="high"
                ))
        
        return results
    
    def print_validation_results(self, results: List[ValidationResult]):
        """Print validation results to console."""
        if not results:
            print("\nAll validation checks passed!")
            return
        
        print(f"\nValidation Results ({len(results)} issues found)")
        print("=" * 60)
        
        # Group by severity
        by_severity = {'critical': [], 'high': [], 'medium': [], 'low': []}
        for result in results:
            by_severity[result.severity].append(result)
        
        # Print by severity
        severity_icons = {'critical': '[CRITICAL]', 'high': '[HIGH]', 'medium': '[MEDIUM]', 'low': '[LOW]'}
        
        for severity in ['critical', 'high', 'medium', 'low']:
            issues = by_severity[severity]
            if issues:
                print(f"\n{severity_icons[severity]} {severity.upper()} ({len(issues)} issues):")
                for issue in issues:
                    device_info = f" [{issue.device}]" if issue.device else ""
                    print(f"  - {issue.message}{device_info}")
        
        print("\n" + "=" * 60)