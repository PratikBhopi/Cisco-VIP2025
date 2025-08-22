"""
Cisco configuration file parser.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from loguru import logger

from ..utils.helpers import parse_bandwidth, validate_ip_address, normalize_interface_name


@dataclass
class Interface:
    """Network interface configuration."""
    name: str
    ip_address: Optional[str] = None
    subnet_mask: Optional[str] = None
    bandwidth: Optional[str] = None
    mtu: Optional[int] = None
    description: Optional[str] = None
    vlan: Optional[int] = None
    enabled: bool = True
    
    
@dataclass 
class RoutingProtocol:
    """Routing protocol configuration."""
    protocol: str  # ospf, bgp, eigrp, static
    process_id: Optional[str] = None
    networks: List[str] = field(default_factory=list)
    neighbors: List[str] = field(default_factory=list)
    area: Optional[str] = None
    

@dataclass
class NetworkDevice:
    """Network device configuration."""
    name: str
    device_type: str  # router, switch, firewall
    hostname: Optional[str] = None
    interfaces: List[Interface] = field(default_factory=list)
    routing_protocols: List[RoutingProtocol] = field(default_factory=list)
    vlans: Dict[int, str] = field(default_factory=dict)
    config_file: Optional[str] = None
    

class ConfigParser:
    """Parser for Cisco configuration files."""
    
    def __init__(self, config_file: str = "config/settings.yaml"):
        """Initialize parser with configuration."""
        self.config_file = config_file
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            with open(self.config_file, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logger.warning(f"Config file {self.config_file} not found, using defaults")
            return self._get_default_config()
        except yaml.YAMLError as e:
            logger.error(f"Error parsing config file: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            'device_defaults': {
                'router': {'default_bandwidth': '1000Mbps', 'default_mtu': 1500},
                'switch': {'default_bandwidth': '1000Mbps', 'default_mtu': 1500}
            },
            'analysis': {
                'bandwidth_threshold': 0.8,
                'mtu_check_enabled': True
            }
        }
    
    def parse_directory(self, config_dir: str) -> List[NetworkDevice]:
        """
        Parse all configuration files in directory.
        
        Args:
            config_dir: Directory containing config files
            
        Returns:
            List of parsed network devices
        """
        devices = []
        config_path = Path(config_dir)
        
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration directory not found: {config_dir}")
        
        # Look for device directories (R1, R2, SW1, etc.)
        for device_dir in config_path.iterdir():
            if device_dir.is_dir():
                config_file = device_dir / "config.dump"
                if config_file.exists():
                    logger.info(f"Parsing {device_dir.name} configuration")
                    device = self.parse_device_config(str(config_file), device_dir.name)
                    if device:
                        devices.append(device)
                else:
                    logger.warning(f"No config.dump found in {device_dir}")
        
        return devices
    
    def parse_device_config(self, config_file: str, device_name: str) -> Optional[NetworkDevice]:
        """
        Parse individual device configuration file.
        
        Args:
            config_file: Path to configuration file
            device_name: Name of the device
            
        Returns:
            Parsed NetworkDevice or None if parsing fails
        """
        try:
            with open(config_file, 'r') as f:
                config_lines = f.readlines()
            
            device = NetworkDevice(
                name=device_name,
                device_type=self._detect_device_type(device_name),
                config_file=config_file
            )
            
            self._parse_config_lines(config_lines, device)
            return device
            
        except Exception as e:
            logger.error(f"Error parsing {config_file}: {e}")
            return None
    
    def _detect_device_type(self, device_name: str) -> str:
        """Detect device type from name."""
        name_lower = device_name.lower()
        if name_lower.startswith('pc') or name_lower.startswith('host'):
            return 'pc'
        elif name_lower.startswith('sw') or name_lower.startswith('s'):
            return 'switch'
        elif name_lower.startswith('r'):
            return 'router'
        elif name_lower.startswith('fw') or name_lower.startswith('asa'):
            return 'firewall'
        else:
            return 'router'  # Default to router
    
    def _parse_config_lines(self, lines: List[str], device: NetworkDevice):
        """Parse configuration lines and populate device object."""
        current_interface = None
        current_router_process = None
        in_interface_config = False
        in_router_config = False
        
        for line_num, line in enumerate(lines):
            original_line = line
            line = line.strip()
            
            # Skip empty lines and comments
            if not line or line.startswith('!'):
                continue
            
            # Hostname
            if line.startswith('hostname '):
                device.hostname = line.split()[1]
            
            # Interface configuration
            elif line.startswith('interface '):
                in_interface_config = True
                in_router_config = False  # Exit router config when entering interface
                interface_name = ' '.join(line.split()[1:])
                current_interface = Interface(
                    name=normalize_interface_name(interface_name)
                )
                # Set default values based on device type
                self._set_interface_defaults(current_interface, device.device_type)
                device.interfaces.append(current_interface)
            
            # Router configuration
            elif line.startswith('router '):
                in_router_config = True
                in_interface_config = False  # Exit interface config when entering router
                parts = line.split()
                protocol = parts[1]
                process_id = parts[2] if len(parts) > 2 else None
                current_router_process = RoutingProtocol(
                    protocol=protocol,
                    process_id=process_id
                )
                device.routing_protocols.append(current_router_process)
            
            # Exit interface configuration - only exit if we hit a non-indented line that's not a comment
            elif in_interface_config and not original_line.startswith(' ') and not line.startswith('!') and line != '':
                in_interface_config = False
                current_interface = None
            
            # Exit router configuration - only exit if we hit a non-indented line that's not a comment
            elif in_router_config and not original_line.startswith(' ') and not line.startswith('!') and line != '':
                in_router_config = False
                current_router_process = None
            
            # Interface-specific commands (must be indented)
            elif in_interface_config and current_interface and original_line.startswith(' '):
                self._parse_interface_command(line, current_interface)
            
            # Router-specific commands (must be indented)
            elif in_router_config and current_router_process and original_line.startswith(' '):
                self._parse_router_command(line, current_router_process)
            
            # VLAN configuration
            elif line.startswith('vlan '):
                self._parse_vlan_command(line, device)
    
    def _parse_interface_command(self, line: str, interface: Interface):
        """Parse interface-specific configuration command."""
        line = line.strip()
        
        if line.startswith('ip address '):
            parts = line.split()
            if len(parts) >= 4:  # Need at least "ip address x.x.x.x y.y.y.y"
                interface.ip_address = parts[2]
                interface.subnet_mask = parts[3]
        
        elif line.startswith('bandwidth '):
            parts = line.split()
            if len(parts) >= 2:
                # Cisco bandwidth is in Kbps
                interface.bandwidth = f"{parts[1]}Kbps"
        
        elif line.startswith('mtu '):
            parts = line.split()
            if len(parts) >= 2:
                try:
                    interface.mtu = int(parts[1])
                except ValueError:
                    pass
        
        elif line.startswith('description '):
            interface.description = ' '.join(line.split()[1:])
        
        elif line.startswith('switchport access vlan '):
            parts = line.split()
            if len(parts) >= 4:
                try:
                    interface.vlan = int(parts[3])
                except ValueError:
                    pass
    
    def _set_interface_defaults(self, interface: Interface, device_type: str):
        """Set default values for interface based on device type."""
        if device_type == 'pc':
            # PC interfaces typically have these defaults
            interface.bandwidth = "100000Kbps"  # 100 Mbps default
            interface.mtu = 1500
            interface.description = interface.description or "PC Interface"
        elif device_type == 'switch':
            # Switch interfaces
            if interface.name.lower().startswith('gi') or 'gigabit' in interface.name.lower():
                interface.bandwidth = "1000000Kbps"  # 1 Gbps
            else:
                interface.bandwidth = "100000Kbps"  # 100 Mbps
            interface.mtu = 1500
            interface.description = interface.description or "Switch Port"
        elif device_type == 'router':
            # Router interfaces
            if interface.name.lower().startswith('gi') or 'gigabit' in interface.name.lower():
                interface.bandwidth = "1000000Kbps"  # 1 Gbps
            elif interface.name.lower().startswith('fa') or 'fastethernet' in interface.name.lower():
                interface.bandwidth = "100000Kbps"  # 100 Mbps
            else:
                interface.bandwidth = "10000Kbps"  # 10 Mbps default
            interface.mtu = 1500
            interface.description = interface.description or "Router Interface"
        
        elif line == 'shutdown':
            interface.enabled = False
        
        elif line == 'no shutdown':
            interface.enabled = True
    
    def _parse_router_command(self, line: str, routing_protocol: RoutingProtocol):
        """Parse routing protocol configuration command."""
        line = line.strip()
        
        if line.startswith('network '):
            parts = line.split()
            if len(parts) >= 2:
                network = parts[1]
                if len(parts) >= 3:
                    # Include wildcard mask if present
                    network += f" {parts[2]}"
                routing_protocol.networks.append(network)
        
        elif line.startswith('neighbor '):
            parts = line.split()
            if len(parts) >= 2:
                routing_protocol.neighbors.append(parts[1])
        
        elif line.startswith('area '):
            parts = line.split()
            if len(parts) >= 2:
                routing_protocol.area = parts[1]
    
    def _parse_vlan_command(self, line: str, device: NetworkDevice):
        """Parse VLAN configuration command."""
        parts = line.split()
        if len(parts) >= 2:
            try:
                vlan_id = int(parts[1])
                # Set default VLAN name
                device.vlans[vlan_id] = f"VLAN{vlan_id}"
            except ValueError:
                pass
        elif line.strip().startswith('name ') and len(device.vlans) > 0:
            # Parse VLAN name (assumes it follows vlan command)
            vlan_name = ' '.join(line.split()[1:])
            # Update the last VLAN added
            last_vlan_id = max(device.vlans.keys()) if device.vlans else None
            if last_vlan_id:
                device.vlans[last_vlan_id] = vlan_name