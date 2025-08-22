"""
Network topology builder from device configurations.
"""

import json
import networkx as nx
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass, asdict
from loguru import logger

from .config_parser import NetworkDevice, Interface
from ..utils.helpers import validate_ip_address, calculate_subnet


@dataclass
class NetworkLink:
    """Network link between devices."""
    source_device: str
    target_device: str
    source_interface: str
    target_interface: str
    bandwidth: Optional[str] = None
    utilization: float = 0.0
    link_type: str = "ethernet"


@dataclass
class NetworkTopology:
    """Complete network topology."""
    devices: List[NetworkDevice]
    links: List[NetworkLink]
    subnets: Dict[str, List[str]]  # subnet -> list of device names
    

class TopologyBuilder:
    """Builds network topology from device configurations."""
    
    def __init__(self, config_parser):
        """Initialize with config parser."""
        self.config_parser = config_parser
        self.graph = nx.Graph()
    
    def build_topology(self, devices: List[NetworkDevice]) -> NetworkTopology:
        """
        Build network topology from device configurations.
        
        Args:
            devices: List of network devices
            
        Returns:
            Complete network topology
        """
        logger.info("Building network topology")
        
        # Create graph nodes for devices
        for device in devices:
            self.graph.add_node(device.name, device_type=device.device_type)
        
        # Discover links between devices
        links = self._discover_links(devices)
        
        # Add links to graph
        for link in links:
            self.graph.add_edge(
                link.source_device,
                link.target_device,
                source_interface=link.source_interface,
                target_interface=link.target_interface,
                bandwidth=link.bandwidth
            )
        
        # Discover subnets
        subnets = self._discover_subnets(devices)
        
        topology = NetworkTopology(
            devices=devices,
            links=links,
            subnets=subnets
        )
        
        logger.info(f"Built topology with {len(devices)} devices, {len(links)} links, {len(subnets)} subnets")
        return topology
    
    def _discover_links(self, devices: List[NetworkDevice]) -> List[NetworkLink]:
        """
        Discover links between devices using hierarchical network topology rules.
        
        Args:
            devices: List of network devices
            
        Returns:
            List of discovered network links
        """
        links = []
        
        # First, discover subnet-based connections (routers)
        subnet_links = self._discover_subnet_links(devices)
        links.extend(subnet_links)
        
        # Then, discover hierarchical connections (switches to routers, PCs to switches)
        hierarchical_links = self._discover_hierarchical_links(devices)
        links.extend(hierarchical_links)
        
        return links
    
    def _discover_subnet_links(self, devices: List[NetworkDevice]) -> List[NetworkLink]:
        """Discover links based on IP subnets (mainly for routers)."""
        links = []
        device_interfaces = {}
        
        # Build mapping of subnets to device interfaces (only for routers)
        for device in devices:
            if device.device_type == 'router':
                for interface in device.interfaces:
                    if interface.ip_address and interface.subnet_mask:
                        subnet = calculate_subnet(interface.ip_address, interface.subnet_mask)
                        if subnet:
                            subnet_str = str(subnet)
                            if subnet_str not in device_interfaces:
                                device_interfaces[subnet_str] = []
                            device_interfaces[subnet_str].append((device, interface))
        
        # Find links (interfaces in same subnet)
        for subnet, interfaces in device_interfaces.items():
            if len(interfaces) >= 2:
                # Create links between all devices in same subnet
                for i in range(len(interfaces)):
                    for j in range(i + 1, len(interfaces)):
                        device1, interface1 = interfaces[i]
                        device2, interface2 = interfaces[j]
                        
                        # Determine bandwidth (use minimum of both interfaces)
                        bandwidth = self._determine_link_bandwidth(interface1, interface2)
                        
                        link = NetworkLink(
                            source_device=device1.name,
                            target_device=device2.name,
                            source_interface=interface1.name,
                            target_interface=interface2.name,
                            bandwidth=bandwidth
                        )
                        links.append(link)
        
        return links
    
    def _discover_hierarchical_links(self, devices: List[NetworkDevice]) -> List[NetworkLink]:
        """Discover hierarchical connections based on network design patterns."""
        links = []
        
        # Separate devices by type
        routers = [d for d in devices if d.device_type == 'router']
        switches = [d for d in devices if d.device_type == 'switch']
        pcs = [d for d in devices if d.device_type == 'pc']
        
        # Connect switches to routers based on interface descriptions and subnets
        for switch in switches:
            for router in routers:
                if self._should_connect_switch_to_router(switch, router):
                    # Find best interfaces to connect
                    switch_interface = self._find_uplink_interface(switch)
                    router_interface = self._find_switch_interface(router, switch)
                    
                    if switch_interface and router_interface:
                        bandwidth = self._determine_link_bandwidth(switch_interface, router_interface)
                        link = NetworkLink(
                            source_device=switch.name,
                            target_device=router.name,
                            source_interface=switch_interface.name,
                            target_interface=router_interface.name,
                            bandwidth=bandwidth
                        )
                        links.append(link)
        
        # Connect PCs to switches based on VLAN and subnet matching
        for pc in pcs:
            for switch in switches:
                if self._should_connect_pc_to_switch(pc, switch):
                    # Find matching interfaces
                    pc_interface = pc.interfaces[0] if pc.interfaces else None
                    switch_interface = self._find_pc_interface(switch, pc)
                    
                    if pc_interface and switch_interface:
                        bandwidth = self._determine_link_bandwidth(pc_interface, switch_interface)
                        link = NetworkLink(
                            source_device=pc.name,
                            target_device=switch.name,
                            source_interface=pc_interface.name,
                            target_interface=switch_interface.name,
                            bandwidth=bandwidth
                        )
                        links.append(link)
        
        # Connect switches to each other (trunk links)
        for i, switch1 in enumerate(switches):
            for switch2 in switches[i+1:]:
                if self._should_connect_switches(switch1, switch2):
                    # Find trunk interfaces
                    switch1_trunk = self._find_trunk_interface(switch1, switch2)
                    switch2_trunk = self._find_trunk_interface(switch2, switch1)
                    
                    if switch1_trunk and switch2_trunk:
                        bandwidth = self._determine_link_bandwidth(switch1_trunk, switch2_trunk)
                        link = NetworkLink(
                            source_device=switch1.name,
                            target_device=switch2.name,
                            source_interface=switch1_trunk.name,
                            target_interface=switch2_trunk.name,
                            bandwidth=bandwidth
                        )
                        links.append(link)
        
        return links
    
    def _should_connect_switch_to_router(self, switch, router) -> bool:
        """Determine if switch should connect to router."""
        # Check if router has interface descriptions mentioning the switch
        for interface in router.interfaces:
            if interface.description and switch.name.lower() in interface.description.lower():
                return True
        
        # Check if switch has uplink interface descriptions mentioning router
        for interface in switch.interfaces:
            if interface.description and ('uplink' in interface.description.lower() or 
                                        'router' in interface.description.lower()):
                return True
        
        return True  # Default: connect all switches to routers
    
    def _should_connect_pc_to_switch(self, pc, switch) -> bool:
        """Determine if PC should connect to switch based on subnet/VLAN."""
        if not pc.interfaces:
            return False
        
        pc_interface = pc.interfaces[0]
        if not pc_interface.ip_address:
            return False
        
        # Check if PC's subnet matches any VLAN subnet that the switch handles
        pc_subnet = calculate_subnet(pc_interface.ip_address, pc_interface.subnet_mask)
        if not pc_subnet:
            return False
        
        # Check switch interface descriptions for PC name
        for interface in switch.interfaces:
            if (interface.description and 
                pc.name.lower() in interface.description.lower()):
                return True
        
        # Default logic: connect PC to first available switch
        return True
    
    def _should_connect_switches(self, switch1, switch2) -> bool:
        """Determine if switches should be connected via trunk."""
        # Check for trunk interface descriptions
        for interface in switch1.interfaces:
            if (interface.description and 
                switch2.name.lower() in interface.description.lower() and
                'trunk' in interface.description.lower()):
                return True
        
        return False  # Only connect if explicitly configured
    
    def _find_uplink_interface(self, switch):
        """Find uplink interface on switch (typically Gigabit)."""
        # Look for Gigabit interfaces with uplink descriptions
        for interface in switch.interfaces:
            if (interface.name.lower().startswith('gi') and 
                interface.description and 
                ('uplink' in interface.description.lower() or 
                 'router' in interface.description.lower())):
                return interface
        
        # Fallback: any Gigabit interface
        for interface in switch.interfaces:
            if interface.name.lower().startswith('gi'):
                return interface
        
        return None
    
    def _find_switch_interface(self, router, switch):
        """Find router interface that connects to switch."""
        # Look for interface with switch name in description
        for interface in router.interfaces:
            if (interface.description and 
                switch.name.lower() in interface.description.lower()):
                return interface
        
        # Fallback: any available interface
        return router.interfaces[0] if router.interfaces else None
    
    def _find_pc_interface(self, switch, pc):
        """Find switch interface that connects to PC."""
        # Look for interface with PC name in description
        for interface in switch.interfaces:
            if (interface.description and 
                pc.name.lower() in interface.description.lower()):
                return interface
        
        # Fallback: first FastEthernet interface
        for interface in switch.interfaces:
            if interface.name.lower().startswith('fa'):
                return interface
        
        return None
    
    def _find_trunk_interface(self, switch, target_switch):
        """Find trunk interface connecting to target switch."""
        for interface in switch.interfaces:
            if (interface.description and 
                target_switch.name.lower() in interface.description.lower() and
                'trunk' in interface.description.lower()):
                return interface
        
        return None
    
    def _determine_link_bandwidth(self, interface1: Interface, interface2: Interface) -> str:
        """Determine link bandwidth from interface configurations."""
        # Get bandwidth from interfaces
        bw1 = interface1.bandwidth or self._get_default_bandwidth(interface1.name)
        bw2 = interface2.bandwidth or self._get_default_bandwidth(interface2.name)
        
        # Parse bandwidth values
        from ..utils.helpers import parse_bandwidth
        bw1_bps = parse_bandwidth(bw1)
        bw2_bps = parse_bandwidth(bw2)
        
        # Use minimum bandwidth
        min_bw_bps = min(bw1_bps, bw2_bps) if bw1_bps > 0 and bw2_bps > 0 else max(bw1_bps, bw2_bps)
        
        # Convert back to human readable format
        if min_bw_bps >= 1_000_000_000:
            return f"{min_bw_bps // 1_000_000_000}Gbps"
        elif min_bw_bps >= 1_000_000:
            return f"{min_bw_bps // 1_000_000}Mbps"
        elif min_bw_bps >= 1_000:
            return f"{min_bw_bps // 1_000}Kbps"
        else:
            return f"{min_bw_bps}bps"
    
    def _get_default_bandwidth(self, interface_name: str) -> str:
        """Get default bandwidth based on interface type."""
        interface_lower = interface_name.lower()
        
        if 'gi' in interface_lower or 'gigabit' in interface_lower:
            return "1000Mbps"
        elif 'fa' in interface_lower or 'fast' in interface_lower:
            return "100Mbps"
        elif 'et' in interface_lower or 'ethernet' in interface_lower:
            return "10Mbps"
        else:
            return self.config_parser.config.get('device_defaults', {}).get('router', {}).get('default_bandwidth', '1000Mbps')
    
    def _discover_subnets(self, devices: List[NetworkDevice]) -> Dict[str, List[str]]:
        """
        Discover network subnets and which devices are connected to them.
        
        Args:
            devices: List of network devices
            
        Returns:
            Dictionary mapping subnet to list of connected devices
        """
        subnets = {}
        
        for device in devices:
            for interface in device.interfaces:
                if interface.ip_address and interface.subnet_mask:
                    subnet = calculate_subnet(interface.ip_address, interface.subnet_mask)
                    if subnet:
                        subnet_str = str(subnet)
                        if subnet_str not in subnets:
                            subnets[subnet_str] = []
                        if device.name not in subnets[subnet_str]:
                            subnets[subnet_str].append(device.name)
        
        return subnets
    
    def save_topology(self, topology: NetworkTopology, output_file: str):
        """
        Save topology to JSON file.
        
        Args:
            topology: Network topology to save
            output_file: Output file path
        """
        # Convert to serializable format
        topology_dict = {
            'devices': [self._device_to_dict(device) for device in topology.devices],
            'links': [asdict(link) for link in topology.links],
            'subnets': topology.subnets,
            'statistics': {
                'total_devices': len(topology.devices),
                'total_links': len(topology.links),
                'total_subnets': len(topology.subnets),
                'device_types': self._get_device_type_counts(topology.devices)
            }
        }
        
        with open(output_file, 'w') as f:
            json.dump(topology_dict, f, indent=2)
        
        logger.info(f"Topology saved to {output_file}")
    
    def _device_to_dict(self, device: NetworkDevice) -> Dict[str, Any]:
        """Convert NetworkDevice to dictionary."""
        return {
            'name': device.name,
            'device_type': device.device_type,
            'hostname': device.hostname,
            'interfaces': [self._interface_to_dict(interface) for interface in device.interfaces],
            'routing_protocols': [asdict(rp) for rp in device.routing_protocols],
            'vlans': device.vlans,
            'config_file': device.config_file
        }
    
    def _interface_to_dict(self, interface: Interface) -> Dict[str, Any]:
        """Convert Interface to dictionary."""
        return asdict(interface)
    
    def _get_device_type_counts(self, devices: List[NetworkDevice]) -> Dict[str, int]:
        """Get count of each device type."""
        counts = {}
        for device in devices:
            device_type = device.device_type
            counts[device_type] = counts.get(device_type, 0) + 1
        return counts
    
    def get_network_graph(self) -> nx.Graph:
        """Get NetworkX graph representation."""
        return self.graph
    
    def find_shortest_path(self, source: str, target: str) -> Optional[List[str]]:
        """Find shortest path between two devices."""
        try:
            return nx.shortest_path(self.graph, source, target)
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return None
    
    def get_network_diameter(self) -> int:
        """Get network diameter (longest shortest path)."""
        if not self.graph.nodes():
            return 0
        try:
            return nx.diameter(self.graph)
        except nx.NetworkXError:
            # Graph is not connected
            return -1