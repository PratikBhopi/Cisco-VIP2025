"""
Inter-Process Communication manager for network simulation.
"""

import threading
import time
import queue
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass
from loguru import logger


@dataclass
class Connection:
    """Represents a connection between two network nodes."""
    node1: str
    node2: str
    interface1: str
    interface2: str
    enabled: bool = True
    bandwidth: Optional[str] = None
    latency: float = 0.001  # 1ms default latency
    packet_loss: float = 0.0  # No packet loss by default


class IPCManager:
    """Manages inter-process communication between network nodes."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize IPC manager."""
        self.config = config
        self.timeout = config.get('ipc_timeout', 5000) / 1000.0  # Convert to seconds
        
        # Connection management
        self.connections: Dict[Tuple[str, str], Connection] = {}
        self.node_queues: Dict[str, queue.Queue] = {}
        self.message_stats = {
            'sent': 0,
            'delivered': 0,
            'dropped': 0,
            'queued': 0
        }
        
        # Threading
        self.running = False
        self.worker_thread = None
        self.lock = threading.RLock()
        
        # Message processing
        self.message_queue = queue.Queue()
        
        self.start()
    
    def start(self):
        """Start the IPC manager."""
        if self.running:
            return
        
        self.running = True
        self.worker_thread = threading.Thread(target=self._message_processor, daemon=True)
        self.worker_thread.start()
        logger.debug("IPC Manager started")
    
    def stop(self):
        """Stop the IPC manager."""
        self.running = False
        if self.worker_thread and self.worker_thread.is_alive():
            self.worker_thread.join(timeout=1.0)
    
    def cleanup(self):
        """Clean up IPC resources."""
        self.stop()
        
        with self.lock:
            self.connections.clear()
            self.node_queues.clear()
            
            # Clear all queues
            while not self.message_queue.empty():
                try:
                    self.message_queue.get_nowait()
                except queue.Empty:
                    break
    
    def create_connection(self, node1: str, node2: str, interface1: str, interface2: str, **kwargs):
        """
        Create a connection between two nodes.
        
        Args:
            node1: First node name
            node2: Second node name  
            interface1: Interface on first node
            interface2: Interface on second node
            **kwargs: Additional connection parameters
        """
        with self.lock:
            # Create bidirectional connection entries
            conn_key1 = (node1, node2)
            conn_key2 = (node2, node1)
            
            connection = Connection(
                node1=node1,
                node2=node2,
                interface1=interface1,
                interface2=interface2,
                bandwidth=kwargs.get('bandwidth'),
                latency=kwargs.get('latency', 0.001),
                packet_loss=kwargs.get('packet_loss', 0.0)
            )
            
            self.connections[conn_key1] = connection
            self.connections[conn_key2] = connection
            
            # Ensure node queues exist
            self._ensure_node_queue(node1)
            self._ensure_node_queue(node2)
            
            logger.debug(f"Created connection: {node1}:{interface1} <-> {node2}:{interface2}")
    
    def _ensure_node_queue(self, node_name: str):
        """Ensure message queue exists for node."""
        if node_name not in self.node_queues:
            self.node_queues[node_name] = queue.Queue(maxsize=100)
    
    def send_message(self, source: str, target: str, message: Dict[str, Any]):
        """
        Send message from source to target node.
        
        Args:
            source: Source node name
            target: Target node name
            message: Message to send
        """
        if not self.running:
            return False
        
        # Check if connection exists and is enabled
        conn_key = (source, target)
        connection = self.connections.get(conn_key)
        
        if not connection or not connection.enabled:
            self.message_stats['dropped'] += 1
            return False
        
        # Add message to processing queue
        ipc_message = {
            'source': source,
            'target': target,
            'message': message,
            'timestamp': time.time(),
            'connection': connection
        }
        
        try:
            self.message_queue.put_nowait(ipc_message)
            self.message_stats['sent'] += 1
            return True
        except queue.Full:
            self.message_stats['dropped'] += 1
            return False
    
    def broadcast_from_node(self, source: str, message: Dict[str, Any]):
        """
        Broadcast message from source to all connected neighbors.
        
        Args:
            source: Source node name
            message: Message to broadcast
        """
        neighbors = self.get_neighbors(source)
        
        for neighbor in neighbors:
            self.send_message(source, neighbor, message)
    
    def get_neighbors(self, node: str) -> List[str]:
        """
        Get list of neighbors for a node.
        
        Args:
            node: Node name
            
        Returns:
            List of neighbor node names
        """
        neighbors = []
        
        with self.lock:
            for (source, target), connection in self.connections.items():
                if source == node and connection.enabled:
                    neighbors.append(target)
        
        return neighbors
    
    def disable_connection(self, node1: str, node2: str):
        """
        Disable connection between two nodes.
        
        Args:
            node1: First node
            node2: Second node
        """
        with self.lock:
            conn_key1 = (node1, node2)
            conn_key2 = (node2, node1)
            
            if conn_key1 in self.connections:
                self.connections[conn_key1].enabled = False
            if conn_key2 in self.connections:
                self.connections[conn_key2].enabled = False
            
            logger.debug(f"Disabled connection: {node1} <-> {node2}")
    
    def enable_connection(self, node1: str, node2: str):
        """
        Enable connection between two nodes.
        
        Args:
            node1: First node
            node2: Second node
        """
        with self.lock:
            conn_key1 = (node1, node2)
            conn_key2 = (node2, node1)
            
            if conn_key1 in self.connections:
                self.connections[conn_key1].enabled = True
            if conn_key2 in self.connections:
                self.connections[conn_key2].enabled = True
            
            logger.debug(f"Enabled connection: {node1} <-> {node2}")
    
    def enable_all_connections(self):
        """Enable all connections."""
        with self.lock:
            for connection in self.connections.values():
                connection.enabled = True
            logger.debug("Enabled all connections")
    
    def _message_processor(self):
        """Process messages in background thread."""
        while self.running:
            try:
                # Get message with timeout
                ipc_message = self.message_queue.get(timeout=0.1)
                self._process_message(ipc_message)
                self.message_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error processing message: {e}")
    
    def _process_message(self, ipc_message: Dict[str, Any]):
        """Process individual message."""
        source = ipc_message['source']
        target = ipc_message['target']
        message = ipc_message['message']
        connection = ipc_message['connection']
        
        # Simulate network latency
        if connection.latency > 0:
            time.sleep(connection.latency)
        
        # Simulate packet loss
        if connection.packet_loss > 0:
            import random
            if random.random() < connection.packet_loss:
                self.message_stats['dropped'] += 1
                return
        
        # Deliver message to target node
        self._deliver_message(target, message)
    
    def _deliver_message(self, target: str, message: Dict[str, Any]):
        """Deliver message to target node."""
        with self.lock:
            if target not in self.node_queues:
                self.message_stats['dropped'] += 1
                return
            
            target_queue = self.node_queues[target]
        
        try:
            target_queue.put_nowait(message)
            self.message_stats['delivered'] += 1
        except queue.Full:
            self.message_stats['dropped'] += 1
    
    def register_node(self, node_name: str, node_instance):
        """
        Register a node instance for message delivery.
        
        Args:
            node_name: Node name
            node_instance: Node instance with receive_message method
        """
        with self.lock:
            self._ensure_node_queue(node_name)
            
            # Start message delivery thread for this node
            delivery_thread = threading.Thread(
                target=self._node_message_delivery,
                args=(node_name, node_instance),
                daemon=True
            )
            delivery_thread.start()
    
    def _node_message_delivery(self, node_name: str, node_instance):
        """Deliver messages to specific node."""
        node_queue = self.node_queues[node_name]
        
        while self.running:
            try:
                message = node_queue.get(timeout=0.1)
                
                # Deliver to node instance
                if hasattr(node_instance, 'receive_message'):
                    node_instance.receive_message(message)
                
                node_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error delivering message to {node_name}: {e}")
    
    def get_connection_info(self, node1: str, node2: str) -> Optional[Connection]:
        """Get connection information between two nodes."""
        with self.lock:
            return self.connections.get((node1, node2))
    
    def get_all_connections(self) -> List[Connection]:
        """Get all connections."""
        with self.lock:
            # Return unique connections (avoid duplicates from bidirectional entries)
            unique_connections = {}
            for connection in self.connections.values():
                key = tuple(sorted([connection.node1, connection.node2]))
                unique_connections[key] = connection
            
            return list(unique_connections.values())
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get IPC statistics."""
        with self.lock:
            stats = self.message_stats.copy()
            stats.update({
                'active_connections': len(self.get_all_connections()),
                'enabled_connections': len([c for c in self.connections.values() if c.enabled]) // 2,
                'registered_nodes': len(self.node_queues),
                'queued_messages': sum(q.qsize() for q in self.node_queues.values())
            })
            
            return stats
    
    def set_connection_properties(self, node1: str, node2: str, **properties):
        """
        Set connection properties like latency, packet loss, etc.
        
        Args:
            node1: First node
            node2: Second node
            **properties: Properties to set (latency, packet_loss, bandwidth)
        """
        with self.lock:
            conn_key1 = (node1, node2)
            conn_key2 = (node2, node1)
            
            for conn_key in [conn_key1, conn_key2]:
                if conn_key in self.connections:
                    connection = self.connections[conn_key]
                    
                    if 'latency' in properties:
                        connection.latency = properties['latency']
                    if 'packet_loss' in properties:
                        connection.packet_loss = properties['packet_loss']
                    if 'bandwidth' in properties:
                        connection.bandwidth = properties['bandwidth']
    
    def simulate_congestion(self, node1: str, node2: str, congestion_level: float):
        """
        Simulate network congestion on a link.
        
        Args:
            node1: First node
            node2: Second node
            congestion_level: Congestion level (0.0 to 1.0)
        """
        # Increase latency and packet loss based on congestion
        base_latency = 0.001
        base_packet_loss = 0.0
        
        new_latency = base_latency * (1 + congestion_level * 10)
        new_packet_loss = base_packet_loss + (congestion_level * 0.1)
        
        self.set_connection_properties(
            node1, node2,
            latency=new_latency,
            packet_loss=min(new_packet_loss, 0.5)  # Cap at 50% loss
        )
        
        logger.debug(f"Applied congestion to {node1}<->{node2}: latency={new_latency:.3f}s, loss={new_packet_loss:.1%}")
    
    def clear_congestion(self):
        """Clear all congestion simulation."""
        with self.lock:
            for connection in self.connections.values():
                connection.latency = 0.001
                connection.packet_loss = 0.0
        
        logger.debug("Cleared all congestion simulation")