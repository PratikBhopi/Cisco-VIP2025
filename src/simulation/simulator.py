"""
Network simulation engine.
"""

import time
import threading
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from loguru import logger

from ..core.topology_builder import NetworkTopology
from ..core.config_parser import NetworkDevice
from .network_node import NetworkNode
from .ipc_manager import IPCManager


@dataclass
class SimulationResult:
    """Results from network simulation."""
    scenario: str
    duration: float
    events: List[Dict[str, Any]] = field(default_factory=list)
    statistics: Dict[str, Any] = field(default_factory=dict)
    node_states: Dict[str, Any] = field(default_factory=dict)


class NetworkSimulator:
    """Network behavior simulator."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize simulator with configuration."""
        self.config = config
        self.simulation_config = config.get('simulation', {})
        self.max_simulation_time = self.simulation_config.get('max_simulation_time', 300)
        self.thread_pool_size = self.simulation_config.get('thread_pool_size', 10)
        
        self.nodes = {}  # device_name -> NetworkNode
        self.ipc_manager = None
        self.simulation_running = False
        self.simulation_paused = False
        self.events = []
        
    def run_simulation(self, topology: NetworkTopology, devices: List[NetworkDevice], scenario: str) -> SimulationResult:
        """
        Run network simulation.
        
        Args:
            topology: Network topology
            devices: List of network devices
            scenario: Simulation scenario ('day1' or 'day2')
            
        Returns:
            Simulation results
        """
        logger.info(f"Starting {scenario} simulation")
        start_time = time.time()
        
        try:
            # Initialize simulation
            self._initialize_simulation(topology, devices)
            
            # Run scenario-specific simulation
            if scenario == 'day1':
                self._run_day1_scenario()
            elif scenario == 'day2':
                self._run_day2_scenario()
            else:
                raise ValueError(f"Unknown scenario: {scenario}")
            
            # Collect results
            end_time = time.time()
            duration = end_time - start_time
            
            result = SimulationResult(
                scenario=scenario,
                duration=duration,
                events=self.events.copy(),
                statistics=self._collect_statistics(),
                node_states=self._collect_node_states()
            )
            
            logger.info(f"Simulation completed in {duration:.2f} seconds")
            return result
            
        finally:
            self._cleanup_simulation()
    
    def _initialize_simulation(self, topology: NetworkTopology, devices: List[NetworkDevice]):
        """Initialize simulation environment."""
        logger.info("Initializing simulation environment")
        
        # Initialize IPC manager
        self.ipc_manager = IPCManager(self.simulation_config)
        
        # Create network nodes
        for device in devices:
            node = NetworkNode(device, self.simulation_config, self.ipc_manager)
            self.nodes[device.name] = node
        
        # Configure node connections based on topology
        for link in topology.links:
            source_node = self.nodes.get(link.source_device)
            target_node = self.nodes.get(link.target_device)
            
            if source_node and target_node:
                # Establish IPC connection between nodes
                self.ipc_manager.create_connection(
                    link.source_device, 
                    link.target_device,
                    link.source_interface,
                    link.target_interface
                )
        
        # Start all nodes
        for node in self.nodes.values():
            node.start()
        
        self.simulation_running = True
        self._log_event("simulation_started", "Simulation environment initialized")
    
    def _run_day1_scenario(self):
        """Run Day-1 simulation scenario (device startup and discovery)."""
        logger.info("Running Day-1 scenario: Device startup and network discovery")
        
        # Phase 1: Device power-on sequence
        self._log_event("phase_start", "Phase 1: Device power-on sequence")
        self._simulate_device_startup()
        
        # Phase 2: ARP and neighbor discovery
        self._log_event("phase_start", "Phase 2: ARP and neighbor discovery")
        self._simulate_arp_discovery()
        
        # Phase 3: Routing protocol convergence
        self._log_event("phase_start", "Phase 3: Routing protocol convergence")
        self._simulate_routing_convergence()
        
        # Phase 4: Network stabilization
        self._log_event("phase_start", "Phase 4: Network stabilization")
        self._simulate_network_stabilization()
    
    def _run_day2_scenario(self):
        """Run Day-2 simulation scenario (operational events and failures)."""
        logger.info("Running Day-2 scenario: Operational events and failure simulation")
        
        # Start with stable network
        self._simulate_network_stabilization()
        
        # Phase 1: Normal operation
        self._log_event("phase_start", "Phase 1: Normal network operation")
        time.sleep(2)
        
        # Phase 2: Link failure simulation
        self._log_event("phase_start", "Phase 2: Link failure simulation")
        self._simulate_link_failures()
        
        # Phase 3: Recovery and reconvergence
        self._log_event("phase_start", "Phase 3: Network recovery")
        self._simulate_network_recovery()
        
        # Phase 4: Configuration changes
        self._log_event("phase_start", "Phase 4: Configuration change impact")
        self._simulate_configuration_changes()
    
    def _simulate_device_startup(self):
        """Simulate device startup sequence."""
        startup_order = ['router', 'switch', 'firewall']  # Typical startup order
        
        for device_type in startup_order:
            devices_of_type = [node for node in self.nodes.values() 
                             if node.device.device_type == device_type]
            
            for node in devices_of_type:
                self._log_event("device_startup", f"Device {node.device.name} starting up", node.device.name)
                node.power_on()
                time.sleep(0.5)  # Stagger startup
    
    def _simulate_arp_discovery(self):
        """Simulate ARP table population."""
        for node in self.nodes.values():
            self._log_event("arp_discovery", f"Device {node.device.name} performing ARP discovery", node.device.name)
            node.perform_arp_discovery()
            time.sleep(0.2)
    
    def _simulate_routing_convergence(self):
        """Simulate routing protocol convergence."""
        # Simulate OSPF hello packets and LSA exchanges
        router_nodes = [node for node in self.nodes.values() 
                       if node.device.device_type == 'router']
        
        for node in router_nodes:
            if any(rp.protocol == 'ospf' for rp in node.device.routing_protocols):
                self._log_event("ospf_hello", f"Router {node.device.name} sending OSPF hello packets", node.device.name)
                node.send_ospf_hello()
        
        # Wait for convergence
        time.sleep(3)
        
        for node in router_nodes:
            self._log_event("routing_table_update", f"Router {node.device.name} updating routing table", node.device.name)
            node.update_routing_table()
    
    def _simulate_network_stabilization(self):
        """Simulate network reaching stable state."""
        self._log_event("network_stable", "Network reached stable state")
        
        # All nodes report ready
        for node in self.nodes.values():
            node.set_operational_state(True)
        
        time.sleep(1)
    
    def _simulate_link_failures(self):
        """Simulate random link failures."""
        import random
        
        # Select random links to fail
        available_nodes = list(self.nodes.keys())
        if len(available_nodes) >= 2:
            # Fail a random connection
            node1, node2 = random.sample(available_nodes, 2)
            
            self._log_event("link_failure", f"Link failure between {node1} and {node2}")
            
            # Simulate link down
            self.ipc_manager.disable_connection(node1, node2)
            
            # Nodes detect failure and reconverge
            if node1 in self.nodes:
                self.nodes[node1].handle_link_failure(node2)
            if node2 in self.nodes:
                self.nodes[node2].handle_link_failure(node1)
            
            time.sleep(2)
    
    def _simulate_network_recovery(self):
        """Simulate network recovery from failures."""
        self._log_event("recovery_start", "Starting network recovery")
        
        # Re-enable failed connections
        self.ipc_manager.enable_all_connections()
        
        # Nodes reconverge
        for node in self.nodes.values():
            if node.device.device_type == 'router':
                node.reconverge_routing()
        
        time.sleep(3)
        self._log_event("recovery_complete", "Network recovery completed")
    
    def _simulate_configuration_changes(self):
        """Simulate configuration changes and their impact."""
        import random
        
        # Select random router for configuration change
        routers = [node for node in self.nodes.values() 
                  if node.device.device_type == 'router']
        
        if routers:
            router = random.choice(routers)
            self._log_event("config_change", f"Configuration change on {router.device.name}", router.device.name)
            
            # Simulate interface shutdown/no shutdown
            router.simulate_interface_change()
            time.sleep(1)
    
    def _collect_statistics(self) -> Dict[str, Any]:
        """Collect simulation statistics."""
        stats = {
            'total_events': len(self.events),
            'nodes_simulated': len(self.nodes),
            'event_types': {},
            'node_statistics': {}
        }
        
        # Count event types
        for event in self.events:
            event_type = event.get('type', 'unknown')
            stats['event_types'][event_type] = stats['event_types'].get(event_type, 0) + 1
        
        # Collect node statistics
        for node_name, node in self.nodes.items():
            stats['node_statistics'][node_name] = node.get_statistics()
        
        return stats
    
    def _collect_node_states(self) -> Dict[str, Any]:
        """Collect current state of all nodes."""
        states = {}
        
        for node_name, node in self.nodes.items():
            states[node_name] = {
                'operational': node.is_operational(),
                'interfaces_up': node.get_interface_states(),
                'routing_table_size': len(node.get_routing_table()),
                'arp_table_size': len(node.get_arp_table())
            }
        
        return states
    
    def _log_event(self, event_type: str, message: str, device: str = None):
        """Log simulation event."""
        event = {
            'timestamp': time.time(),
            'type': event_type,
            'message': message,
            'device': device
        }
        self.events.append(event)
        logger.debug(f"Simulation event: {message}")
    
    def _cleanup_simulation(self):
        """Clean up simulation resources."""
        logger.info("Cleaning up simulation")
        
        self.simulation_running = False
        
        # Stop all nodes
        for node in self.nodes.values():
            node.stop()
        
        # Cleanup IPC manager
        if self.ipc_manager:
            self.ipc_manager.cleanup()
        
        self.nodes.clear()
        self.events.clear()
    
    def pause_simulation(self):
        """Pause the simulation."""
        self.simulation_paused = True
        for node in self.nodes.values():
            node.pause()
        logger.info("Simulation paused")
    
    def resume_simulation(self):
        """Resume the simulation."""
        self.simulation_paused = False
        for node in self.nodes.values():
            node.resume()
        logger.info("Simulation resumed")
    
    def inject_fault(self, fault_type: str, target: str, **kwargs):
        """Inject a fault for testing."""
        self._log_event("fault_injection", f"Injecting {fault_type} fault on {target}")
        
        if fault_type == "link_failure" and target in self.nodes:
            neighbor = kwargs.get('neighbor')
            if neighbor:
                self.ipc_manager.disable_connection(target, neighbor)
                self.nodes[target].handle_link_failure(neighbor)
        
        elif fault_type == "device_failure" and target in self.nodes:
            self.nodes[target].simulate_device_failure()
        
        elif fault_type == "interface_down" and target in self.nodes:
            interface = kwargs.get('interface')
            if interface:
                self.nodes[target].simulate_interface_down(interface)
    
    def print_simulation_results(self, results: SimulationResult):
        """Print simulation results to console."""
        print(f"\nSimulation Results - {results.scenario.upper()}")
        print("=" * 50)
        
        print(f"Duration: {results.duration:.2f} seconds")
        print(f"Total Events: {len(results.events)}")
        print(f"Nodes Simulated: {results.statistics.get('nodes_simulated', 0)}")
        
        # Event summary
        event_types = results.statistics.get('event_types', {})
        if event_types:
            print(f"\nEvent Summary:")
            for event_type, count in event_types.items():
                print(f"  {event_type.replace('_', ' ').title()}: {count}")
        
        # Node states
        node_states = results.node_states
        operational_nodes = sum(1 for state in node_states.values() if state.get('operational', False))
        print(f"\nFinal State:")
        print(f"  Operational Nodes: {operational_nodes}/{len(node_states)}")
        
        # Recent events
        recent_events = results.events[-5:] if len(results.events) > 5 else results.events
        if recent_events:
            print(f"\nRecent Events:")
            for event in recent_events:
                device_info = f" [{event['device']}]" if event.get('device') else ""
                print(f"  • {event['message']}{device_info}")
        
        print("=" * 50)