"""
Network node simulation representing individual devices.
"""

import threading
import time
import queue
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

from ..core.config_parser import NetworkDevice


@dataclass
class NodeStatistics:
    """Statistics for a network node."""
    packets_sent: int = 0
    packets_received: int = 0
    hello_packets_sent: int = 0
    arp_requests_sent: int = 0
    routing_updates: int = 0
    uptime: float = 0.0
    last_activity: float = 0.0


class NetworkNode:
    """Simulates a network device (router, switch, etc.)."""
    
    def __init__(self, device: NetworkDevice, config: Dict[str, Any], ipc_manager):
        """Initialize network node."""
        self.device = device
        self.config = config
        self.ipc_manager = ipc_manager
        
        # Node state
        self.operational = False
        self.powered_on = False
        self.paused = False
        
        # Threading
        self.thread = None
        self.stop_event = threading.Event()
        self.message_queue = queue.Queue()
        
        # Network tables
        self.arp_table = {}  # ip -> mac
        self.routing_table = {}  # network -> next_hop
        self.interface_states = {}  # interface -> up/down
        
        # Statistics
        self.statistics = NodeStatistics()
        self.start_time = None
        
        # Initialize interface states
        for interface in device.interfaces:
            self.interface_states[interface.name] = interface.enabled
    
    def start(self):
        """Start the network node thread."""
        if self.thread and self.thread.is_alive():
            return
        
        self.stop_event.clear()
        self.thread = threading.Thread(target=self._run_node_loop, daemon=True)
        self.thread.start()
        self.start_time = time.time()
    
    def stop(self):
        """Stop the network node."""
        self.stop_event.set()
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)
        self.operational = False
        self.powered_on = False
    
    def pause(self):
        """Pause node operations."""
        self.paused = True
    
    def resume(self):
        """Resume node operations."""
        self.paused = False
    
    def _run_node_loop(self):
        """Main node processing loop."""
        while not self.stop_event.is_set():
            if self.paused:
                time.sleep(0.1)
                continue
            
            try:
                # Process incoming messages
                self._process_messages()
                
                # Perform periodic tasks
                if self.operational:
                    self._perform_periodic_tasks()
                
                # Update statistics
                self._update_statistics()
                
                time.sleep(0.1)  # 100ms loop
                
            except Exception as e:
                # Log error but continue running
                pass
    
    def _process_messages(self):
        """Process incoming IPC messages."""
        try:
            while True:
                message = self.message_queue.get_nowait()
                self._handle_message(message)
                self.statistics.packets_received += 1
        except queue.Empty:
            pass
    
    def _handle_message(self, message: Dict[str, Any]):
        """Handle incoming network message."""
        msg_type = message.get('type')
        
        if msg_type == 'arp_request':
            self._handle_arp_request(message)
        elif msg_type == 'arp_reply':
            self._handle_arp_reply(message)
        elif msg_type == 'ospf_hello':
            self._handle_ospf_hello(message)
        elif msg_type == 'routing_update':
            self._handle_routing_update(message)
        elif msg_type == 'ping':
            self._handle_ping(message)
    
    def _perform_periodic_tasks(self):
        """Perform periodic network tasks."""
        current_time = time.time()
        
        # Send OSPF hello packets (every 10 seconds)
        if (current_time - self.statistics.last_activity) > 10:
            if self.device.device_type == 'router':
                self._send_ospf_hello_periodic()
            self.statistics.last_activity = current_time
    
    def _update_statistics(self):
        """Update node statistics."""
        if self.start_time:
            self.statistics.uptime = time.time() - self.start_time
    
    def power_on(self):
        """Simulate device power-on."""
        self.powered_on = True
        
        # Initialize interfaces
        for interface in self.device.interfaces:
            if interface.enabled:
                self.interface_states[interface.name] = True
        
        # Start basic services
        time.sleep(0.5)  # Boot time
        self.operational = True
    
    def perform_arp_discovery(self):
        """Perform ARP discovery for connected networks."""
        if not self.operational:
            return
        
        for interface in self.device.interfaces:
            if interface.ip_address and self.interface_states.get(interface.name, False):
                # Send ARP request for gateway
                arp_message = {
                    'type': 'arp_request',
                    'source': self.device.name,
                    'source_ip': interface.ip_address,
                    'target_ip': self._get_gateway_ip(interface),
                    'interface': interface.name
                }
                self._broadcast_message(arp_message)
                self.statistics.arp_requests_sent += 1
    
    def send_ospf_hello(self):
        """Send OSPF hello packets to neighbors."""
        if not self.operational or self.device.device_type != 'router':
            return
        
        # Check if OSPF is configured
        ospf_processes = [rp for rp in self.device.routing_protocols if rp.protocol == 'ospf']
        
        for ospf_process in ospf_processes:
            hello_message = {
                'type': 'ospf_hello',
                'source': self.device.name,
                'process_id': ospf_process.process_id,
                'area': ospf_process.area or '0',
                'router_id': self._get_router_id()
            }
            self._broadcast_message(hello_message)
            self.statistics.hello_packets_sent += 1
    
    def _send_ospf_hello_periodic(self):
        """Send periodic OSPF hello packets."""
        self.send_ospf_hello()
    
    def update_routing_table(self):
        """Update routing table based on learned routes."""
        if not self.operational or self.device.device_type != 'router':
            return
        
        # Simulate routing table updates
        for rp in self.device.routing_protocols:
            for network in rp.networks:
                # Add directly connected networks
                self.routing_table[network] = 'directly_connected'
        
        self.statistics.routing_updates += 1
    
    def handle_link_failure(self, neighbor: str):
        """Handle link failure to neighbor."""
        # Remove routes through failed neighbor
        routes_to_remove = []
        for network, next_hop in self.routing_table.items():
            if next_hop == neighbor:
                routes_to_remove.append(network)
        
        for network in routes_to_remove:
            del self.routing_table[network]
        
        # Trigger reconvergence if OSPF router
        if self.device.device_type == 'router':
            self._trigger_ospf_reconvergence()
    
    def reconverge_routing(self):
        """Reconverge routing protocols after network changes."""
        if self.device.device_type != 'router':
            return
        
        # Simulate routing reconvergence
        self.send_ospf_hello()
        time.sleep(1)
        self.update_routing_table()
    
    def simulate_interface_change(self):
        """Simulate interface configuration change."""
        if not self.device.interfaces:
            return
        
        # Toggle first interface state
        interface = self.device.interfaces[0]
        current_state = self.interface_states.get(interface.name, True)
        self.interface_states[interface.name] = not current_state
        
        if not current_state:  # Interface coming up
            self.perform_arp_discovery()
        else:  # Interface going down
            self._flush_interface_routes(interface.name)
    
    def simulate_device_failure(self):
        """Simulate complete device failure."""
        self.operational = False
        self.powered_on = False
        
        # Clear all tables
        self.arp_table.clear()
        self.routing_table.clear()
        
        # Set all interfaces down
        for interface_name in self.interface_states:
            self.interface_states[interface_name] = False
    
    def simulate_interface_down(self, interface_name: str):
        """Simulate specific interface going down."""
        if interface_name in self.interface_states:
            self.interface_states[interface_name] = False
            self._flush_interface_routes(interface_name)
    
    def _handle_arp_request(self, message: Dict[str, Any]):
        """Handle incoming ARP request."""
        target_ip = message.get('target_ip')
        source_ip = message.get('source_ip')
        source = message.get('source')
        
        # Check if we have this IP
        for interface in self.device.interfaces:
            if interface.ip_address == target_ip:
                # Send ARP reply
                reply = {
                    'type': 'arp_reply',
                    'source': self.device.name,
                    'target': source,
                    'ip': target_ip,
                    'mac': self._get_interface_mac(interface.name)
                }
                self._send_message_to(source, reply)
                break
    
    def _handle_arp_reply(self, message: Dict[str, Any]):
        """Handle incoming ARP reply."""
        ip = message.get('ip')
        mac = message.get('mac')
        
        if ip and mac:
            self.arp_table[ip] = mac
    
    def _handle_ospf_hello(self, message: Dict[str, Any]):
        """Handle incoming OSPF hello packet."""
        source = message.get('source')
        router_id = message.get('router_id')
        
        if source and router_id:
            # Update neighbor table (simplified)
            # In real OSPF, this would involve more complex neighbor state machine
            pass
    
    def _handle_routing_update(self, message: Dict[str, Any]):
        """Handle routing protocol update."""
        networks = message.get('networks', [])
        next_hop = message.get('source')
        
        for network in networks:
            self.routing_table[network] = next_hop
    
    def _handle_ping(self, message: Dict[str, Any]):
        """Handle ping request."""
        source = message.get('source')
        
        # Send ping reply
        reply = {
            'type': 'ping_reply',
            'source': self.device.name,
            'target': source
        }
        self._send_message_to(source, reply)
    
    def _broadcast_message(self, message: Dict[str, Any]):
        """Broadcast message to all connected neighbors."""
        self.ipc_manager.broadcast_from_node(self.device.name, message)
        self.statistics.packets_sent += 1
    
    def _send_message_to(self, target: str, message: Dict[str, Any]):
        """Send message to specific target."""
        self.ipc_manager.send_message(self.device.name, target, message)
        self.statistics.packets_sent += 1
    
    def _trigger_ospf_reconvergence(self):
        """Trigger OSPF reconvergence."""
        # Send LSA updates
        lsa_message = {
            'type': 'ospf_lsa',
            'source': self.device.name,
            'router_id': self._get_router_id(),
            'sequence': int(time.time())
        }
        self._broadcast_message(lsa_message)
    
    def _flush_interface_routes(self, interface_name: str):
        """Remove routes associated with specific interface."""
        # Simplified - in reality would check interface associations
        pass
    
    def _get_gateway_ip(self, interface) -> str:
        """Get gateway IP for interface subnet."""
        if interface.ip_address and interface.subnet_mask:
            # Simplified - assume .1 is gateway
            ip_parts = interface.ip_address.split('.')
            ip_parts[-1] = '1'
            return '.'.join(ip_parts)
        return '0.0.0.0'
    
    def _get_router_id(self) -> str:
        """Get router ID (simplified)."""
        # Use first interface IP or device name hash
        for interface in self.device.interfaces:
            if interface.ip_address:
                return interface.ip_address
        return f"192.168.1.{hash(self.device.name) % 254 + 1}"
    
    def _get_interface_mac(self, interface_name: str) -> str:
        """Get MAC address for interface (simulated)."""
        # Generate deterministic MAC based on device and interface
        device_hash = hash(f"{self.device.name}:{interface_name}")
        mac_suffix = f"{device_hash % 0xFFFFFF:06x}"
        return f"00:50:56:{mac_suffix[:2]}:{mac_suffix[2:4]}:{mac_suffix[4:6]}"
    
    # Public interface methods
    def is_operational(self) -> bool:
        """Check if node is operational."""
        return self.operational
    
    def get_interface_states(self) -> Dict[str, bool]:
        """Get current interface states."""
        return self.interface_states.copy()
    
    def get_routing_table(self) -> Dict[str, str]:
        """Get current routing table."""
        return self.routing_table.copy()
    
    def get_arp_table(self) -> Dict[str, str]:
        """Get current ARP table."""
        return self.arp_table.copy()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get node statistics."""
        return {
            'packets_sent': self.statistics.packets_sent,
            'packets_received': self.statistics.packets_received,
            'hello_packets_sent': self.statistics.hello_packets_sent,
            'arp_requests_sent': self.statistics.arp_requests_sent,
            'routing_updates': self.statistics.routing_updates,
            'uptime': self.statistics.uptime,
            'operational': self.operational,
            'interfaces_up': sum(1 for state in self.interface_states.values() if state)
        }
    
    def set_operational_state(self, operational: bool):
        """Set operational state."""
        self.operational = operational
    
    def receive_message(self, message: Dict[str, Any]):
        """Receive message from IPC manager."""
        try:
            self.message_queue.put_nowait(message)
        except queue.Full:
            # Drop message if queue is full
            pass