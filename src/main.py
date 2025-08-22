#!/usr/bin/env python3
"""
Network Topology Analyzer - Main Entry Point

Usage:
    python main.py --config-dir ./Conf --output topology.json
    python main.py --config-dir ./Conf --analyze --report analysis_report.html
    python main.py --config-dir ./Conf --simulate --scenario day1
    python main.py --config-dir ./Conf --validate --verbose
"""

import click
import sys
import os
from pathlib import Path
from typing import Optional

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.topology_builder import TopologyBuilder
from src.core.config_parser import ConfigParser
from src.core.network_analyzer import NetworkAnalyzer
from src.simulation.simulator import NetworkSimulator
from src.validation.config_validator import ConfigValidator
from src.utils.logger import setup_logger


@click.command()
@click.option('--config-dir', '-c', required=True, type=click.Path(exists=True),
              help='Directory containing router configuration files')
@click.option('--output', '-o', type=click.Path(), 
              help='Output file for topology (JSON format)')
@click.option('--analyze', is_flag=True, 
              help='Perform network analysis')
@click.option('--report', '-r', type=click.Path(),
              help='Generate analysis report (HTML format)')
@click.option('--simulate', is_flag=True,
              help='Run network simulation')
@click.option('--scenario', type=click.Choice(['day1', 'day2']), default='day1',
              help='Simulation scenario to run')
@click.option('--visualize', is_flag=True,
              help='Generate interactive HTML topology visualization')
@click.option('--validate', is_flag=True,
              help='Validate network configurations')
@click.option('--verbose', '-v', is_flag=True,
              help='Enable verbose output')
@click.option('--config-file', type=click.Path(exists=True),
              default='config/settings.yaml',
              help='Configuration file path')
def cli(config_dir: str, output: Optional[str], analyze: bool, 
        report: Optional[str], simulate: bool, scenario: str,
        validate: bool, visualize: bool, verbose: bool, config_file: str):
    """Network Topology Analyzer - Analyze Cisco network configurations."""
    
    # Setup logging
    logger = setup_logger(verbose=verbose)
    logger.info("Starting Network Topology Analyzer")
    
    try:
        # Initialize components
        config_parser = ConfigParser(config_file)
        topology_builder = TopologyBuilder(config_parser)
        
        # Parse configuration files
        logger.info(f"Parsing configuration files from: {config_dir}")
        devices = config_parser.parse_directory(config_dir)
        logger.info(f"Found {len(devices)} network devices")
        
        # Build topology
        logger.info("Building network topology")
        topology = topology_builder.build_topology(devices)
        
        # Save topology if output specified
        if output:
            logger.info(f"Saving topology to: {output}")
            topology_builder.save_topology(topology, output)
        
        # Perform analysis if requested
        if analyze:
            logger.info("Performing network analysis")
            analyzer = NetworkAnalyzer(config_parser.config)
            analysis_results = analyzer.analyze_network(topology, devices)
            
            if report:
                logger.info(f"Generating analysis report: {report}")
                analyzer.generate_report(analysis_results, report)
            else:
                # Print summary to console
                analyzer.print_summary(analysis_results)
        
        # Run validation if requested
        if validate:
            logger.info("Validating network configurations")
            validator = ConfigValidator(config_parser.config)
            validation_results = validator.validate_all(devices, topology)
            validator.print_validation_results(validation_results)
        
        # Run simulation if requested
        if simulate:
            logger.info(f"Running {scenario} simulation")
            simulator = NetworkSimulator(config_parser.config)
            simulation_results = simulator.run_simulation(topology, devices, scenario)
            simulator.print_simulation_results(simulation_results)
        
        # Generate visualization if requested
        if visualize:
            logger.info("Generating network topology visualization")
            from src.visualization.topology_visualizer import TopologyVisualizer
            
            # Save topology to temporary file if not already saved
            temp_topology_file = output or "temp_topology.json"
            if not output:
                topology_builder.save_topology(topology, temp_topology_file)
            
            # Generate visualization
            visualizer = TopologyVisualizer()
            if visualizer.load_topology(temp_topology_file):
                viz_output = temp_topology_file.replace('.json', '_visualization.html')
                visualizer.generate_html_visualization(viz_output)
                logger.info(f"Interactive visualization saved to: {viz_output}")
            
            # Clean up temporary file if created
            if not output and os.path.exists(temp_topology_file):
                os.remove(temp_topology_file)
        
        logger.info("Analysis completed successfully")
        
    except Exception as e:
        logger.error(f"Error during analysis: {str(e)}")
        if verbose:
            import traceback
            logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == '__main__':
    cli()