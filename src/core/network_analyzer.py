"""
Network analysis and optimization recommendations.
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from loguru import logger

from .topology_builder import NetworkTopology, NetworkLink
from .config_parser import NetworkDevice
from ..utils.helpers import parse_bandwidth


@dataclass
class AnalysisResult:
    """Network analysis results."""
    bandwidth_analysis: Dict[str, Any] = field(default_factory=dict)
    configuration_issues: List[Dict[str, Any]] = field(default_factory=list)
    optimization_recommendations: List[str] = field(default_factory=list)
    network_statistics: Dict[str, Any] = field(default_factory=dict)
    load_balancing_suggestions: List[Dict[str, Any]] = field(default_factory=list)


class NetworkAnalyzer:
    """Analyzes network topology and configurations."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize analyzer with configuration."""
        self.config = config
        self.bandwidth_threshold = config.get('analysis', {}).get('bandwidth_threshold', 0.8)
    
    def analyze_network(self, topology: NetworkTopology, devices: List[NetworkDevice]) -> AnalysisResult:
        """
        Perform comprehensive network analysis.
        
        Args:
            topology: Network topology
            devices: List of network devices
            
        Returns:
            Analysis results
        """
        logger.info("Starting network analysis")
        
        result = AnalysisResult()
        
        # Analyze bandwidth utilization
        result.bandwidth_analysis = self._analyze_bandwidth(topology)
        
        # Check for configuration issues
        result.configuration_issues = self._check_configuration_issues(devices, topology)
        
        # Generate optimization recommendations
        result.optimization_recommendations = self._generate_optimization_recommendations(topology, devices)
        
        # Calculate network statistics
        result.network_statistics = self._calculate_network_statistics(topology)
        
        # Generate load balancing suggestions
        result.load_balancing_suggestions = self._generate_load_balancing_suggestions(topology)
        
        logger.info("Network analysis completed")
        return result
    
    def _analyze_bandwidth(self, topology: NetworkTopology) -> Dict[str, Any]:
        """Analyze bandwidth utilization across the network."""
        analysis = {
            'total_links': len(topology.links),
            'overutilized_links': [],
            'underutilized_links': [],
            'average_utilization': 0.0,
            'bottlenecks': []
        }
        
        total_utilization = 0.0
        
        for link in topology.links:
            # Simulate utilization (in real implementation, this would come from monitoring data)
            utilization = self._estimate_link_utilization(link, topology)
            link.utilization = utilization
            total_utilization += utilization
            
            if utilization > self.bandwidth_threshold:
                analysis['overutilized_links'].append({
                    'source': link.source_device,
                    'target': link.target_device,
                    'utilization': utilization,
                    'bandwidth': link.bandwidth,
                    'severity': 'high' if utilization > 0.9 else 'medium'
                })
            elif utilization < 0.1:
                analysis['underutilized_links'].append({
                    'source': link.source_device,
                    'target': link.target_device,
                    'utilization': utilization,
                    'bandwidth': link.bandwidth
                })
        
        if topology.links:
            analysis['average_utilization'] = total_utilization / len(topology.links)
        
        # Identify bottlenecks
        analysis['bottlenecks'] = self._identify_bottlenecks(topology)
        
        return analysis
    
    def _estimate_link_utilization(self, link: NetworkLink, topology: NetworkTopology) -> float:
        """Estimate link utilization based on network characteristics."""
        # This is a simplified estimation - in reality, you'd use SNMP or other monitoring
        
        # Base utilization on device types
        source_device = next((d for d in topology.devices if d.name == link.source_device), None)
        target_device = next((d for d in topology.devices if d.name == link.target_device), None)
        
        base_utilization = 0.3  # Default 30%
        
        # Adjust based on device types
        if source_device and target_device:
            if source_device.device_type == 'router' and target_device.device_type == 'router':
                base_utilization = 0.4  # Inter-router links typically higher
            elif 'switch' in [source_device.device_type, target_device.device_type]:
                base_utilization = 0.2  # Switch links typically lower
        
        # Add some randomness for simulation
        import random
        random.seed(hash(f"{link.source_device}-{link.target_device}"))
        variation = random.uniform(-0.1, 0.3)
        
        return max(0.0, min(1.0, base_utilization + variation))
    
    def _identify_bottlenecks(self, topology: NetworkTopology) -> List[Dict[str, Any]]:
        """Identify potential network bottlenecks."""
        bottlenecks = []
        
        # Find links with high utilization
        for link in topology.links:
            if link.utilization > 0.8:
                bottlenecks.append({
                    'type': 'bandwidth_bottleneck',
                    'location': f"{link.source_device} <-> {link.target_device}",
                    'utilization': link.utilization,
                    'bandwidth': link.bandwidth,
                    'recommendation': 'Consider upgrading link bandwidth or implementing load balancing'
                })
        
        # Find single points of failure
        device_connections = {}
        for link in topology.links:
            device_connections[link.source_device] = device_connections.get(link.source_device, 0) + 1
            device_connections[link.target_device] = device_connections.get(link.target_device, 0) + 1
        
        for device, connections in device_connections.items():
            if connections == 1:
                bottlenecks.append({
                    'type': 'single_point_of_failure',
                    'location': device,
                    'connections': connections,
                    'recommendation': 'Add redundant connections to improve network resilience'
                })
        
        return bottlenecks
    
    def _check_configuration_issues(self, devices: List[NetworkDevice], topology: NetworkTopology) -> List[Dict[str, Any]]:
        """Check for common configuration issues."""
        issues = []
        
        # Check for duplicate IP addresses
        ip_addresses = {}
        for device in devices:
            for interface in device.interfaces:
                if interface.ip_address:
                    if interface.ip_address in ip_addresses:
                        issues.append({
                            'type': 'duplicate_ip',
                            'severity': 'high',
                            'description': f"Duplicate IP address {interface.ip_address}",
                            'devices': [ip_addresses[interface.ip_address], device.name],
                            'recommendation': 'Assign unique IP addresses to avoid conflicts'
                        })
                    else:
                        ip_addresses[interface.ip_address] = device.name
        
        # Check for MTU mismatches
        for link in topology.links:
            source_device = next((d for d in devices if d.name == link.source_device), None)
            target_device = next((d for d in devices if d.name == link.target_device), None)
            
            if source_device and target_device:
                source_interface = next((i for i in source_device.interfaces if i.name == link.source_interface), None)
                target_interface = next((i for i in target_device.interfaces if i.name == link.target_interface), None)
                
                if source_interface and target_interface:
                    if source_interface.mtu and target_interface.mtu:
                        if source_interface.mtu != target_interface.mtu:
                            issues.append({
                                'type': 'mtu_mismatch',
                                'severity': 'medium',
                                'description': f"MTU mismatch between {link.source_device} ({source_interface.mtu}) and {link.target_device} ({target_interface.mtu})",
                                'recommendation': 'Configure matching MTU sizes on both ends of the link'
                            })
        
        # Check for missing default gateways (simplified check)
        for device in devices:
            if device.device_type == 'router':
                has_default_route = any(
                    '0.0.0.0' in network for rp in device.routing_protocols for network in rp.networks
                )
                if not has_default_route and len(device.routing_protocols) == 0:
                    issues.append({
                        'type': 'missing_default_route',
                        'severity': 'medium',
                        'description': f"Router {device.name} may be missing default route configuration",
                        'recommendation': 'Configure default route or routing protocol'
                    })
        
        return issues
    
    def _generate_optimization_recommendations(self, topology: NetworkTopology, devices: List[NetworkDevice]) -> List[str]:
        """Generate network optimization recommendations."""
        recommendations = []
        
        # Analyze network redundancy
        if len(topology.links) < len(topology.devices):
            recommendations.append("Consider adding redundant links to improve network resilience")
        
        # Check for routing protocol optimization
        router_count = sum(1 for d in devices if d.device_type == 'router')
        if router_count > 3:
            ospf_routers = sum(1 for d in devices if any(rp.protocol == 'ospf' for rp in d.routing_protocols))
            if ospf_routers < router_count * 0.5:
                recommendations.append("Consider implementing OSPF for better scalability in larger networks")
        
        # Bandwidth optimization
        high_util_links = sum(1 for link in topology.links if link.utilization > 0.8)
        if high_util_links > 0:
            recommendations.append(f"Upgrade bandwidth on {high_util_links} overutilized links")
        
        # VLAN optimization
        total_vlans = sum(len(device.vlans) for device in devices)
        if total_vlans == 0 and any(d.device_type == 'switch' for d in devices):
            recommendations.append("Consider implementing VLANs for better network segmentation")
        
        return recommendations
    
    def _generate_load_balancing_suggestions(self, topology: NetworkTopology) -> List[Dict[str, Any]]:
        """Generate load balancing suggestions."""
        suggestions = []
        
        # Find overutilized links that could benefit from load balancing
        for link in topology.links:
            if link.utilization > self.bandwidth_threshold:
                # Look for alternative paths
                # This is simplified - in reality you'd use graph algorithms
                suggestions.append({
                    'link': f"{link.source_device} <-> {link.target_device}",
                    'current_utilization': link.utilization,
                    'suggestion': 'Implement ECMP or configure secondary paths for load distribution',
                    'priority': 'high' if link.utilization > 0.9 else 'medium'
                })
        
        return suggestions
    
    def _calculate_network_statistics(self, topology: NetworkTopology) -> Dict[str, Any]:
        """Calculate various network statistics."""
        stats = {
            'total_devices': len(topology.devices),
            'total_links': len(topology.links),
            'total_subnets': len(topology.subnets),
            'device_types': {},
            'average_degree': 0.0,
            'network_density': 0.0
        }
        
        # Device type distribution
        for device in topology.devices:
            device_type = device.device_type
            stats['device_types'][device_type] = stats['device_types'].get(device_type, 0) + 1
        
        # Network connectivity metrics
        if topology.devices:
            total_possible_links = len(topology.devices) * (len(topology.devices) - 1) / 2
            stats['network_density'] = len(topology.links) / total_possible_links if total_possible_links > 0 else 0
            
            # Average degree (connections per device)
            stats['average_degree'] = (2 * len(topology.links)) / len(topology.devices)
        
        return stats
    
    def generate_report(self, analysis: AnalysisResult, output_file: str):
        """Generate HTML analysis report."""
        html_content = self._generate_html_report(analysis)
        
        with open(output_file, 'w') as f:
            f.write(html_content)
        
        logger.info(f"Analysis report generated: {output_file}")
    
    def _generate_html_report(self, analysis: AnalysisResult) -> str:
        """Generate HTML report content."""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Network Analysis Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
                .section {{ margin: 20px 0; }}
                .issue {{ background-color: #ffe6e6; padding: 10px; margin: 5px 0; border-radius: 3px; }}
                .recommendation {{ background-color: #e6f3ff; padding: 10px; margin: 5px 0; border-radius: 3px; }}
                .stats {{ background-color: #f0f8f0; padding: 15px; border-radius: 5px; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Network Analysis Report</h1>
                <p>Generated on: {self._get_current_timestamp()}</p>
            </div>
            
            <div class="section">
                <h2>Network Statistics</h2>
                <div class="stats">
                    <p><strong>Total Devices:</strong> {analysis.network_statistics.get('total_devices', 0)}</p>
                    <p><strong>Total Links:</strong> {analysis.network_statistics.get('total_links', 0)}</p>
                    <p><strong>Total Subnets:</strong> {analysis.network_statistics.get('total_subnets', 0)}</p>
                    <p><strong>Average Utilization:</strong> {analysis.bandwidth_analysis.get('average_utilization', 0):.1%}</p>
                </div>
            </div>
            
            <div class="section">
                <h2>Configuration Issues</h2>
                {self._format_issues_html(analysis.configuration_issues)}
            </div>
            
            <div class="section">
                <h2>Optimization Recommendations</h2>
                {self._format_recommendations_html(analysis.optimization_recommendations)}
            </div>
            
            <div class="section">
                <h2>Bandwidth Analysis</h2>
                {self._format_bandwidth_analysis_html(analysis.bandwidth_analysis)}
            </div>
        </body>
        </html>
        """
        return html
    
    def _format_issues_html(self, issues: List[Dict[str, Any]]) -> str:
        """Format configuration issues as HTML."""
        if not issues:
            return "<p>No configuration issues found.</p>"
        
        html = ""
        for issue in issues:
            severity_class = f"issue-{issue.get('severity', 'medium')}"
            html += f"""
            <div class="issue {severity_class}">
                <strong>{issue.get('type', 'Unknown').replace('_', ' ').title()}:</strong>
                {issue.get('description', '')}
                <br><em>Recommendation: {issue.get('recommendation', '')}</em>
            </div>
            """
        return html
    
    def _format_recommendations_html(self, recommendations: List[str]) -> str:
        """Format recommendations as HTML."""
        if not recommendations:
            return "<p>No specific recommendations at this time.</p>"
        
        html = ""
        for rec in recommendations:
            html += f'<div class="recommendation">{rec}</div>'
        return html
    
    def _format_bandwidth_analysis_html(self, analysis: Dict[str, Any]) -> str:
        """Format bandwidth analysis as HTML."""
        overutilized = analysis.get('overutilized_links', [])
        bottlenecks = analysis.get('bottlenecks', [])
        
        html = f"<p><strong>Average Utilization:</strong> {analysis.get('average_utilization', 0):.1%}</p>"
        
        if overutilized:
            html += "<h3>Overutilized Links</h3><ul>"
            for link in overutilized:
                html += f"<li>{link['source']} ↔ {link['target']}: {link['utilization']:.1%} utilization</li>"
            html += "</ul>"
        
        if bottlenecks:
            html += "<h3>Identified Bottlenecks</h3><ul>"
            for bottleneck in bottlenecks:
                html += f"<li>{bottleneck['type']} at {bottleneck['location']}</li>"
            html += "</ul>"
        
        return html
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp for report."""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def print_summary(self, analysis: AnalysisResult):
        """Print analysis summary to console."""
        print("\n" + "="*50)
        print("NETWORK ANALYSIS SUMMARY")
        print("="*50)
        
        # Network statistics
        stats = analysis.network_statistics
        print(f"\nNetwork Overview:")
        print(f"  Devices: {stats.get('total_devices', 0)}")
        print(f"  Links: {stats.get('total_links', 0)}")
        print(f"  Subnets: {stats.get('total_subnets', 0)}")
        print(f"  Average Utilization: {analysis.bandwidth_analysis.get('average_utilization', 0):.1%}")
        
        # Issues
        issues = analysis.configuration_issues
        if issues:
            print(f"\nConfiguration Issues Found: {len(issues)}")
            for issue in issues[:5]:  # Show first 5
                print(f"  - {issue.get('type', 'Unknown').replace('_', ' ').title()}: {issue.get('description', '')}")
        else:
            print("\nNo configuration issues found.")
        
        # Recommendations
        recommendations = analysis.optimization_recommendations
        if recommendations:
            print(f"\nOptimization Recommendations:")
            for rec in recommendations[:3]:  # Show first 3
                print(f"  - {rec}")
        
        print("\n" + "="*50)