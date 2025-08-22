"""
Helper utilities for network analysis.
"""

import re
import ipaddress
from typing import Union, Tuple, Optional


def parse_bandwidth(bandwidth_str: str) -> int:
    """
    Parse bandwidth string and return value in bps.
    
    Args:
        bandwidth_str: Bandwidth string like "1000Mbps", "1Gbps", etc.
        
    Returns:
        Bandwidth in bits per second
        
    Examples:
        >>> parse_bandwidth("1000Mbps")
        1000000000
        >>> parse_bandwidth("1Gbps") 
        1000000000
    """
    if not bandwidth_str:
        return 0
        
    # Remove spaces and convert to lowercase
    bw = bandwidth_str.strip().lower()
    
    # Extract number and unit
    match = re.match(r'(\d+(?:\.\d+)?)\s*([kmgt]?bps)', bw)
    if not match:
        # Try to extract just numbers (assume Mbps)
        match = re.match(r'(\d+(?:\.\d+)?)', bw)
        if match:
            return int(float(match.group(1)) * 1_000_000)  # Default to Mbps
        return 0
    
    value, unit = match.groups()
    value = float(value)
    
    # Convert to bps
    multipliers = {
        'bps': 1,
        'kbps': 1_000,
        'mbps': 1_000_000,
        'gbps': 1_000_000_000,
        'tbps': 1_000_000_000_000
    }
    
    return int(value * multipliers.get(unit, 1))


def validate_ip_address(ip_str: str) -> bool:
    """
    Validate IP address format.
    
    Args:
        ip_str: IP address string
        
    Returns:
        True if valid IP address
    """
    try:
        ipaddress.ip_address(ip_str)
        return True
    except ValueError:
        return False


def calculate_subnet(ip_str: str, netmask: str) -> Optional[ipaddress.IPv4Network]:
    """
    Calculate subnet from IP and netmask.
    
    Args:
        ip_str: IP address string
        netmask: Netmask string (e.g., "255.255.255.0" or "/24")
        
    Returns:
        IPv4Network object or None if invalid
    """
    try:
        if netmask.startswith('/'):
            # CIDR notation
            return ipaddress.IPv4Network(f"{ip_str}{netmask}", strict=False)
        else:
            # Subnet mask notation
            ip = ipaddress.IPv4Address(ip_str)
            mask = ipaddress.IPv4Address(netmask)
            # Convert mask to prefix length
            prefix_len = sum(bin(int(octet)).count('1') for octet in str(mask).split('.'))
            return ipaddress.IPv4Network(f"{ip}/{prefix_len}", strict=False)
    except (ValueError, ipaddress.AddressValueError):
        return None


def normalize_interface_name(interface: str) -> str:
    """
    Normalize interface name to standard format.
    
    Args:
        interface: Interface name (e.g., "Gi0/0/1", "GigabitEthernet0/0/1")
        
    Returns:
        Normalized interface name
    """
    # Common interface abbreviations
    replacements = {
        'GigabitEthernet': 'Gi',
        'FastEthernet': 'Fa', 
        'Ethernet': 'Et',
        'Serial': 'Se',
        'Loopback': 'Lo',
        'Vlan': 'Vl',
        'Port-channel': 'Po'
    }
    
    normalized = interface
    for full_name, abbrev in replacements.items():
        if normalized.startswith(full_name):
            normalized = normalized.replace(full_name, abbrev)
            break
    
    return normalized


def format_bytes(bytes_value: int) -> str:
    """
    Format bytes value to human readable string.
    
    Args:
        bytes_value: Number of bytes
        
    Returns:
        Formatted string (e.g., "1.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f} PB"


def parse_cisco_config_line(line: str) -> Tuple[str, list]:
    """
    Parse a Cisco configuration line into command and arguments.
    
    Args:
        line: Configuration line
        
    Returns:
        Tuple of (command, arguments_list)
    """
    line = line.strip()
    if not line or line.startswith('!'):
        return '', []
    
    parts = line.split()
    if not parts:
        return '', []
    
    command = parts[0]
    args = parts[1:] if len(parts) > 1 else []
    
    return command, args