#!/usr/bin/env python3
"""
Network Topology Visualizer
Generates interactive HTML visualization from topology JSON files.
"""

import json
import os
from typing import Dict, List, Any, Tuple
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class TopologyVisualizer:
    """Generate interactive HTML network topology visualization."""
    
    def __init__(self):
        """Initialize the visualizer."""
        self.devices = []
        self.links = []
        self.subnets = {}
        self.statistics = {}
        
    def load_topology(self, topology_file: str) -> bool:
        """
        Load topology data from JSON file.
        
        Args:
            topology_file: Path to topology JSON file
            
        Returns:
            bool: True if loaded successfully
        """
        try:
            with open(topology_file, 'r') as f:
                topology_data = json.load(f)
            
            self.devices = topology_data.get('devices', [])
            self.links = topology_data.get('links', [])
            self.subnets = topology_data.get('subnets', {})
            self.statistics = topology_data.get('statistics', {})
            
            logger.info(f"Loaded topology with {len(self.devices)} devices and {len(self.links)} links")
            return True
            
        except Exception as e:
            logger.error(f"Error loading topology file: {e}")
            return False
    
    def generate_html_visualization(self, output_file: str = "network_topology.html"):
        """
        Generate interactive HTML visualization.
        
        Args:
            output_file: Output HTML file path
        """
        html_content = self._generate_html_template()
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"Network topology visualization saved to: {output_file}")
    
    def _generate_html_template(self) -> str:
        """Generate the complete HTML template with embedded data."""
        
        # Prepare data for visualization
        nodes_data = self._prepare_nodes_data()
        edges_data = self._prepare_edges_data()
        device_details = self._prepare_device_details()
        
        html_template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Network Topology Visualization</title>
    <script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        
        .header h1 {{
            margin: 0;
            font-size: 2.5em;
        }}
        
        .header p {{
            margin: 10px 0 0 0;
            opacity: 0.9;
        }}
        
        .container {{
            display: flex;
            gap: 20px;
            height: 80vh;
        }}
        
        .topology-panel {{
            flex: 2;
            background: white;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        
        .info-panel {{
            flex: 1;
            background: white;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            padding: 20px;
            overflow-y: auto;
        }}
        
        #topology {{
            width: 100%;
            height: 100%;
            border: none;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 15px;
            margin-bottom: 20px;
        }}
        
        .stat-card {{
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
        }}
        
        .stat-number {{
            font-size: 2em;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        
        .stat-label {{
            font-size: 0.9em;
            opacity: 0.9;
        }}
        
        .device-list {{
            margin-top: 20px;
        }}
        
        .device-item {{
            background: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 10px;
            cursor: pointer;
            transition: all 0.3s ease;
        }}
        
        .device-item:hover {{
            background: #e3f2fd;
            border-color: #2196f3;
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }}
        
        .device-name {{
            font-weight: bold;
            color: #333;
            margin-bottom: 5px;
        }}
        
        .device-type {{
            display: inline-block;
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 0.8em;
            font-weight: bold;
            text-transform: uppercase;
        }}
        
        .device-type.router {{
            background: #ff9800;
            color: white;
        }}
        
        .device-type.switch {{
            background: #4caf50;
            color: white;
        }}
        
        .device-type.pc {{
            background: #2196f3;
            color: white;
        }}
        
        .device-type.firewall {{
            background: #f44336;
            color: white;
        }}
        
        .device-interfaces {{
            margin-top: 10px;
            font-size: 0.9em;
            color: #666;
        }}
        
        .interface-count {{
            background: #e0e0e0;
            padding: 2px 6px;
            border-radius: 10px;
            font-size: 0.8em;
        }}
        
        .subnet-list {{
            margin-top: 20px;
        }}
        
        .subnet-item {{
            background: #fff3e0;
            border-left: 4px solid #ff9800;
            padding: 10px;
            margin-bottom: 8px;
            border-radius: 0 8px 8px 0;
        }}
        
        .subnet-name {{
            font-weight: bold;
            color: #e65100;
        }}
        
        .subnet-devices {{
            font-size: 0.9em;
            color: #666;
            margin-top: 5px;
        }}
        
        .controls {{
            background: white;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        
        .control-group {{
            display: flex;
            gap: 10px;
            align-items: center;
            margin-bottom: 10px;
        }}
        
        .control-group label {{
            font-weight: bold;
            min-width: 100px;
        }}
        
        button {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            cursor: pointer;
            font-weight: bold;
            transition: all 0.3s ease;
        }}
        
        button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        }}
        
        select {{
            padding: 6px 12px;
            border: 1px solid #ddd;
            border-radius: 6px;
            background: white;
        }}
        
        .legend {{
            background: white;
            padding: 15px;
            border-radius: 10px;
            margin-top: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        
        .legend h3 {{
            margin-top: 0;
            color: #333;
        }}
        
        .legend-item {{
            display: flex;
            align-items: center;
            margin-bottom: 8px;
        }}
        
        .legend-color {{
            width: 20px;
            height: 20px;
            border-radius: 50%;
            margin-right: 10px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Network Topology Visualization</h1>
        <p>Interactive network diagram with {len(self.devices)} devices and {len(self.links)} connections</p>
    </div>
    
    <div class="controls">
        <div class="control-group">
            <label>View:</label>
            <button onclick="fitNetwork()">Fit to Screen</button>
            <button onclick="resetZoom()">Reset Zoom</button>
            <button onclick="exportImage()">Export PNG</button>
        </div>
    </div>
    
    <div class="container">
        <div class="topology-panel">
            <div id="topology"></div>
        </div>
        
        <div class="info-panel">
            <h2>Network Statistics</h2>
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-number">{self.statistics.get('total_devices', 0)}</div>
                    <div class="stat-label">Total Devices</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{self.statistics.get('total_links', 0)}</div>
                    <div class="stat-label">Network Links</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{self.statistics.get('total_subnets', 0)}</div>
                    <div class="stat-label">Subnets</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{len(set(d['device_type'] for d in self.devices))}</div>
                    <div class="stat-label">Device Types</div>
                </div>
            </div>
            
            <h3>Network Devices</h3>
            <div class="device-list" id="deviceList">
                {self._generate_device_list_html()}
            </div>
            
            <h3>Network Subnets</h3>
            <div class="subnet-list">
                {self._generate_subnet_list_html()}
            </div>
            
            <div class="legend">
                <h3>Device Types</h3>
                <div class="legend-item">
                    <div class="legend-color" style="background: #ff9800;"></div>
                    <span>Router</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background: #4caf50;"></div>
                    <span>Switch</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background: #2196f3;"></div>
                    <span>PC/Host</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background: #f44336;"></div>
                    <span>Firewall</span>
                </div>
                
                <h3 style="margin-top: 20px;">Connection Types</h3>
                <div class="legend-item">
                    <div style="width: 30px; height: 4px; background: #ff6b35; margin-right: 10px; border-radius: 2px;"></div>
                    <span>Core Links (Router-Router)</span>
                </div>
                <div class="legend-item">
                    <div style="width: 30px; height: 3px; background: #4ecdc4; margin-right: 10px; border-radius: 2px;"></div>
                    <span>Distribution (Router-Switch)</span>
                </div>
                <div class="legend-item">
                    <div style="width: 30px; height: 2px; background: #45b7d1; margin-right: 10px; border-radius: 2px;"></div>
                    <span>Access Links (Switch-PC)</span>
                </div>
            </div>
        </div>
    </div>

    <script>
        // Network data
        const nodes = new vis.DataSet({nodes_data});
        const edges = new vis.DataSet({edges_data});
        const deviceDetails = {json.dumps(device_details, indent=2)};
        
        // Network options - Simplified for clarity
        let options = {{
            layout: {{
                hierarchical: {{
                    enabled: true,
                    direction: 'UD',
                    sortMethod: 'directed',
                    levelSeparation: 150,
                    nodeSpacing: 200,
                    treeSpacing: 250,
                    blockShifting: true,
                    edgeMinimization: true,
                    parentCentralization: true
                }}
            }},
            physics: {{
                enabled: false
            }},
            nodes: {{
                shape: 'dot',
                size: 30,
                font: {{
                    size: 16,
                    color: '#333333',
                    face: 'Arial Bold'
                }},
                borderWidth: 2,
                shadow: false,
                chosen: {{
                    node: function(values, id, selected, hovering) {{
                        values.size = 35;
                        values.borderWidth = 3;
                    }}
                }}
            }},
            edges: {{
                width: 2,
                color: {{
                    color: '#666666',
                    highlight: '#ff4444',
                    hover: '#ff4444'
                }},
                smooth: {{
                    enabled: true,
                    type: 'straightCross',
                    roundness: 0.1
                }},
                font: {{
                    size: 0,  // Hide edge labels by default for cleaner look
                    color: '#666666'
                }},
                shadow: false,
                arrows: {{
                    to: {{
                        enabled: false
                    }}
                }}
            }},
            interaction: {{
                hover: true,
                selectConnectedEdges: true,
                tooltipDelay: 200,
                hideEdgesOnDrag: true,
                hideNodesOnDrag: false
            }}
        }};
        
        // Initialize network
        const container = document.getElementById('topology');
        const data = {{ nodes: nodes, edges: edges }};
        const network = new vis.Network(container, data, options);
        
        // Event handlers
        network.on('click', function(params) {{
            if (params.nodes.length > 0) {{
                const nodeId = params.nodes[0];
                showDeviceDetails(nodeId);
            }}
        }});
        
        network.on('hoverNode', function(params) {{
            const nodeId = params.node;
            highlightConnectedNodes(nodeId);
        }});
        
        network.on('blurNode', function(params) {{
            resetHighlight();
        }});
        
        // Functions
        function showDeviceDetails(nodeId) {{
            const device = deviceDetails[nodeId];
            if (device) {{
                alert(`Device: ${{device.name}}\\n` +
                      `Type: ${{device.device_type}}\\n` +
                      `Hostname: ${{device.hostname}}\\n` +
                      `Interfaces: ${{device.interfaces.length}}\\n` +
                      `VLANs: ${{Object.keys(device.vlans).length}}`);
            }}
        }}
        
        function highlightConnectedNodes(nodeId) {{
            const connectedNodes = network.getConnectedNodes(nodeId);
            const connectedEdges = network.getConnectedEdges(nodeId);
            
            // Highlight connected nodes
            const updateNodes = nodes.map(node => {{
                if (node.id === nodeId || connectedNodes.includes(node.id)) {{
                    return {{ ...node, color: {{ background: node.color.background, border: '#ff4444' }} }};
                }} else {{
                    return {{ ...node, color: {{ background: node.color.background, border: '#cccccc' }} }};
                }}
            }});
            
            nodes.update(updateNodes);
        }}
        
        function resetHighlight() {{
            const updateNodes = nodes.map(node => {{
                return {{ ...node, color: {{ background: node.color.background, border: getDeviceColor(node.group).border }} }};
            }});
            nodes.update(updateNodes);
        }}
        
        function focusDevice(deviceId) {{
            network.focus(deviceId, {{
                scale: 1.5,
                animation: {{
                    duration: 1000,
                    easingFunction: 'easeInOutQuad'
                }}
            }});
            
            // Highlight the device
            highlightConnectedNodes(deviceId);
            setTimeout(() => resetHighlight(), 3000);
        }}
        
        function fitNetwork() {{
            network.fit();
        }}
        
        function resetZoom() {{
            network.moveTo({{ scale: 1.0 }});
        }}
        
        function exportImage() {{
            const canvas = network.canvas.frame.canvas;
            const link = document.createElement('a');
            link.download = 'network_topology.png';
            link.href = canvas.toDataURL();
            link.click();
        }}
        
        function getDeviceColor(deviceType) {{
            const colors = {{
                'router': {{ background: '#ff9800', border: '#f57c00' }},
                'switch': {{ background: '#4caf50', border: '#388e3c' }},
                'pc': {{ background: '#2196f3', border: '#1976d2' }},
                'firewall': {{ background: '#f44336', border: '#d32f2f' }}
            }};
            return colors[deviceType] || {{ background: '#9e9e9e', border: '#757575' }};
        }}
        
        // Initialize with fit view
        setTimeout(() => {{
            network.fit();
        }}, 1000);
    </script>
</body>
</html>
        """
        
        return html_template
    
    def _prepare_nodes_data(self) -> str:
        """Prepare nodes data for vis.js network with hierarchical levels."""
        nodes = []
        
        for device in self.devices:
            device_type = device.get('device_type', 'router')
            
            # Determine node color and shape based on device type
            if device_type == 'router':
                color = {'background': '#ff9800', 'border': '#f57c00'}
                shape = 'box'
                size = 40
                level = 0  # Top level
            elif device_type == 'switch':
                color = {'background': '#4caf50', 'border': '#388e3c'}
                shape = 'ellipse'
                size = 35
                level = 1  # Middle level
            elif device_type == 'pc':
                color = {'background': '#2196f3', 'border': '#1976d2'}
                shape = 'dot'
                size = 25
                level = 2  # Bottom level
            elif device_type == 'firewall':
                color = {'background': '#f44336', 'border': '#d32f2f'}
                shape = 'diamond'
                size = 35
                level = 0  # Top level
            else:
                color = {'background': '#9e9e9e', 'border': '#757575'}
                shape = 'dot'
                size = 30
                level = 1
            
            node = {
                'id': device['name'],
                'label': device['name'],
                'group': device_type,
                'color': color,
                'shape': shape,
                'size': size,
                'level': level,
                'title': self._generate_node_tooltip(device),
                'font': {'size': 14, 'color': '#333333', 'face': 'Arial Bold'}
            }
            
            nodes.append(node)
        
        return json.dumps(nodes, indent=2)
    
    def _prepare_edges_data(self) -> str:
        """Prepare edges data for vis.js network - simplified for clarity."""
        edges = []
        
        # Group links by connection type for cleaner visualization
        processed_connections = set()
        
        for link in self.links:
            # Create unique connection identifier
            connection_key = tuple(sorted([link['source_device'], link['target_device']]))
            
            # Skip if we've already processed this connection
            if connection_key in processed_connections:
                continue
            
            processed_connections.add(connection_key)
            
            # Determine connection type and styling
            source_type = self._get_device_type(link['source_device'])
            target_type = self._get_device_type(link['target_device'])
            
            # Simplified color scheme based on connection hierarchy
            if source_type == 'router' and target_type == 'router':
                # Router-to-router (core links)
                color = '#ff6b35'  # Orange-red
                width = 4
                dashes = False
            elif (source_type == 'router' and target_type == 'switch') or (source_type == 'switch' and target_type == 'router'):
                # Router-to-switch (distribution links)
                color = '#4ecdc4'  # Teal
                width = 3
                dashes = False
            elif source_type == 'switch' and target_type == 'pc':
                # Switch-to-PC (access links)
                color = '#45b7d1'  # Blue
                width = 2
                dashes = False
            elif source_type == 'pc' and target_type == 'switch':
                # PC-to-switch (access links)
                color = '#45b7d1'  # Blue
                width = 2
                dashes = False
            else:
                # Other connections
                color = '#96ceb4'  # Light green
                width = 2
                dashes = [5, 5]
            
            edge = {
                'from': link['source_device'],
                'to': link['target_device'],
                'width': width,
                'color': {'color': color},
                'title': f"Connection: {link['source_device']} ↔ {link['target_device']}<br>Type: {source_type.title()} to {target_type.title()}",
                'smooth': {'type': 'straightCross', 'roundness': 0.1}
            }
            
            if 'dashes' in locals() and dashes:
                edge['dashes'] = dashes
            
            edges.append(edge)
        
        return json.dumps(edges, indent=2)
    
    def _get_device_type(self, device_name: str) -> str:
        """Get device type by name."""
        for device in self.devices:
            if device['name'] == device_name:
                return device.get('device_type', 'unknown')
        return 'unknown'
    
    def _prepare_device_details(self) -> Dict[str, Any]:
        """Prepare detailed device information."""
        details = {}
        
        for device in self.devices:
            details[device['name']] = {
                'name': device['name'],
                'device_type': device.get('device_type', 'unknown'),
                'hostname': device.get('hostname', 'N/A'),
                'interfaces': device.get('interfaces', []),
                'vlans': device.get('vlans', {}),
                'routing_protocols': device.get('routing_protocols', [])
            }
        
        return details
    
    def _generate_node_tooltip(self, device: Dict[str, Any]) -> str:
        """Generate tooltip text for a device node."""
        interfaces = device.get('interfaces', [])
        vlans = device.get('vlans', {})
        
        tooltip = f"<b>{device['name']}</b><br>"
        tooltip += f"Type: {device.get('device_type', 'Unknown')}<br>"
        tooltip += f"Hostname: {device.get('hostname', 'N/A')}<br>"
        tooltip += f"Interfaces: {len(interfaces)}<br>"
        
        if vlans:
            tooltip += f"VLANs: {', '.join(map(str, vlans.keys()))}<br>"
        
        # Add IP addresses
        ip_addresses = []
        for interface in interfaces:
            if interface.get('ip_address'):
                ip_addresses.append(interface['ip_address'])
        
        if ip_addresses:
            tooltip += f"IPs: {', '.join(ip_addresses[:3])}"
            if len(ip_addresses) > 3:
                tooltip += f" (+{len(ip_addresses) - 3} more)"
        
        return tooltip
    
    def _generate_device_list_html(self) -> str:
        """Generate HTML for device list in info panel."""
        html = ""
        
        # Group devices by type
        device_groups = {}
        for device in self.devices:
            device_type = device.get('device_type', 'unknown')
            if device_type not in device_groups:
                device_groups[device_type] = []
            device_groups[device_type].append(device)
        
        for device_type, devices in device_groups.items():
            for device in devices:
                interfaces = device.get('interfaces', [])
                vlans = device.get('vlans', {})
                
                html += f"""
                <div class="device-item" onclick="focusDevice('{device['name']}')">
                    <div class="device-name">{device['name']}</div>
                    <span class="device-type {device_type}">{device_type}</span>
                    <div class="device-interfaces">
                        <span class="interface-count">{len(interfaces)} interfaces</span>
                        {f'• {len(vlans)} VLANs' if vlans else ''}
                    </div>
                </div>
                """
        
        return html
    
    def _generate_subnet_list_html(self) -> str:
        """Generate HTML for subnet list in info panel."""
        html = ""
        
        for subnet, devices in self.subnets.items():
            html += f"""
            <div class="subnet-item">
                <div class="subnet-name">{subnet}</div>
                <div class="subnet-devices">Devices: {', '.join(devices)}</div>
            </div>
            """
        
        return html


def main():
    """Main function for standalone usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate network topology visualization')
    parser.add_argument('topology_file', help='Path to topology JSON file')
    parser.add_argument('--output', '-o', default='network_topology.html', 
                       help='Output HTML file (default: network_topology.html)')
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
    
    # Create visualizer and generate HTML
    visualizer = TopologyVisualizer()
    
    if visualizer.load_topology(args.topology_file):
        visualizer.generate_html_visualization(args.output)
        print(f"✅ Network topology visualization generated: {args.output}")
    else:
        print("❌ Failed to load topology file")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())