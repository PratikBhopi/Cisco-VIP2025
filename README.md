# Network Topology Analyzer

A comprehensive network topology analysis and visualization tool that parses network device configurations, builds hierarchical topologies, and generates interactive HTML visualizations.

## 🚀 Features

- **Configuration Parsing**: Supports Cisco router, switch, and PC configurations
- **Topology Discovery**: Automatically discovers network connections and relationships
- **Hierarchical Visualization**: Generates clean, interactive HTML network diagrams
- **Network Analysis**: Provides detailed network statistics and optimization recommendations
- **Configuration Validation**: Validates network configurations and identifies issues
- **Multiple Output Formats**: JSON topology data and interactive HTML visualizations

## 📁 Project Structure

```
├── src/
│   ├── core/
│   │   ├── config_parser.py      # Configuration file parsing
│   │   ├── topology_builder.py   # Network topology construction
│   │   └── network_analyzer.py   # Network analysis and statistics
│   ├── visualization/
│   │   └── topology_visualizer.py # HTML visualization generator
│   ├── validation/
│   │   └── config_validator.py   # Configuration validation
│   └── main.py                   # Main CLI application
├── tests/
│   └── sample_configs/           # Sample network configurations
└── scenarios/                    # Day-1 and Day-2 test scenarios
```

## 🛠️ Installation

```bash
# Clone the repository
git clone <repository-url>
cd network-topology-analyzer

# Install Python dependencies (if any)
pip install -r requirements.txt  # If requirements.txt exists
```

## 📋 Quick Start Commands

### 1. Generate Complete Network Analysis with Recommendations Report

```bash
# Full analysis with HTML recommendations report
python src/main.py --config-dir tests/sample_configs --analyze --report network_analysis_report.html --validate --visualize --verbose
```

### 2. Generate Recommendations Report Only

```bash
# Generate detailed HTML recommendations report
python src/main.py --config-dir tests/sample_configs --analyze --report recommendations.html --verbose
```

### 3. Console Analysis with Recommendations

```bash
# View recommendations in console output
python src/main.py --config-dir tests/sample_configs --analyze --validate --verbose
```

### 4. Generate Topology with Analysis

```bash
# Basic topology with analysis summary
python src/main.py --config-dir tests/sample_configs --output topology.json --analyze
```

### 5. Generate HTML Visualization from Existing JSON

```bash
# Create interactive HTML from topology JSON
python src/visualization/topology_visualizer.py topology.json --output network_visualization.html
```

### 6. Clean Hierarchical Visualization

```bash
# Generate clean, simplified visualization
python src/visualization/topology_visualizer.py hierarchical_topology.json --output clean_network.html
```

## 📊 How to Generate Recommendations Reports

### Method 1: HTML Recommendations Report (Recommended)

```bash
# Generate comprehensive HTML report with all recommendations
python src/main.py --config-dir tests/sample_configs --analyze --report network_recommendations.html --validate --verbose
```

**Output**: `network_recommendations.html` - Professional HTML report with:

- Network statistics and overview
- Configuration issues and fixes
- Optimization recommendations
- Bandwidth analysis and bottlenecks
- Load balancing suggestions

### Method 2: Console Recommendations Summary

```bash
# View recommendations summary in console
python src/main.py --config-dir tests/sample_configs --analyze --validate --verbose
```

**Output**: Console display with:

- Network overview statistics
- Configuration issues found
- Top optimization recommendations

### Method 3: Complete Analysis Package

```bash
# Generate everything: topology, analysis, visualization, and report
python src/main.py --config-dir tests/sample_configs --output complete_analysis.json --analyze --report complete_report.html --validate --visualize --verbose
```

**Output**:

- `complete_analysis.json` - Network topology data
- `complete_report.html` - Detailed recommendations report
- `complete_analysis_visualization.html` - Interactive network diagram
- Console summary

## 🧪 Testing All Features

### Step 1: Basic Topology Generation

```bash
python src/main.py --config-dir tests/sample_configs --output basic_topology.json
```

**Expected Output**: JSON file with network devices and basic connections

### Step 2: Full Analysis with Reports

```bash
python src/main.py --config-dir tests/sample_configs --output full_topology.json --analyze --validate --visualize --verbose
```

**Expected Output**:

- `full_topology.json` - Complete topology data
- `full_topology_visualization.html` - Interactive visualization
- Console analysis report with statistics and recommendations

### Step 3: Standalone HTML Generation

```bash
python src/visualization/topology_visualizer.py full_topology.json --output standalone_viz.html
```

**Expected Output**: `standalone_viz.html` - Interactive network diagram

### Step 4: Test Day-1 Scenario (Network Startup)

```bash
python scenarios/day1_scenario.py
```

**Expected Output**: Simulated network startup events and device discovery

### Step 5: Test Day-2 Scenario (Operational Events)

```bash
python scenarios/day2_scenario.py
```

**Expected Output**: Simulated operational events and failure scenarios

### Step 6: Validation Only

```bash
python src/main.py --config-dir tests/sample_configs --validate
```

**Expected Output**: Configuration validation report with any issues found

## 📊 Sample Commands for Different Use Cases

### Enterprise Network Analysis

```bash
# Analyze large enterprise network
python src/main.py --config-dir /path/to/enterprise/configs --output enterprise_topology.json --analyze --validate --visualize
```

### Quick Visualization Check

```bash
# Quick visual check of existing topology
python src/visualization/topology_visualizer.py existing_topology.json --output quick_check.html
```

### Configuration Validation

```bash
# Validate configurations without building topology
python src/main.py --config-dir /path/to/configs --validate --verbose
```

### Export Network Documentation

```bash
# Generate complete documentation package
python src/main.py --config-dir tests/sample_configs --output documentation.json --analyze --validate --visualize --verbose
```

## 📈 Expected Results

### Topology Statistics

- **Devices**: 10 (3 Routers, 2 Switches, 5 PCs)
- **Links**: 19 hierarchical connections
- **Subnets**: 11 network segments
- **Device Types**: 4 (Router, Switch, PC, Firewall)

### Network Hierarchy

```
CORE LAYER:     [R3] ← [R2] → [R1]
                      ↓       ↓
DISTRIBUTION:        [SW2]   [SW1]
                      ↓       ↓ ↓ ↓
ACCESS LAYER:    [PC4,PC5] [PC1,PC2,PC3]
```

### Visualization Features

- **Interactive Controls**: Zoom, pan, fit to screen, export PNG
- **Device Information**: Click devices for detailed information
- **Connection Highlighting**: Hover to highlight connected devices
- **Color-Coded Hierarchy**:
  - 🟠 Orange: Routers (Core layer)
  - 🟢 Green: Switches (Distribution layer)
  - 🔵 Blue: PCs (Access layer)

## 🎯 Output Files

### Generated Files

1. **`topology.json`** - Network topology data
2. **`topology_visualization.html`** - Interactive network diagram
3. **Console Reports** - Analysis and validation results

### File Locations

- **Topology Data**: Root directory (`.json` files)
- **Visualizations**: Root directory (`.html` files)
- **Sample Configs**: `tests/sample_configs/`
- **Scenarios**: `scenarios/` directory

## 🔧 Advanced Usage

### Custom Configuration Directory

```bash
python src/main.py --config-dir /custom/path/to/configs --output custom_topology.json --analyze --visualize
```

### Specific Output Location

```bash
python src/main.py --config-dir tests/sample_configs --output /path/to/output/topology.json --visualize
```

### Verbose Logging

```bash
python src/main.py --config-dir tests/sample_configs --verbose --analyze --validate
```

## 🐛 Troubleshooting

### Common Issues

1. **No devices found**

   ```bash
   # Check if config directory exists and contains valid files
   ls -la tests/sample_configs/
   ```

2. **Visualization not loading**

   ```bash
   # Ensure JSON file is valid
   python -m json.tool topology.json
   ```

3. **Missing dependencies**
   ```bash
   # Check Python version (3.7+ required)
   python --version
   ```

### Debug Commands

```bash
# Run with maximum verbosity
python src/main.py --config-dir tests/sample_configs --verbose --analyze --validate --visualize

# Test individual components
python src/core/config_parser.py  # Test parser
python src/visualization/topology_visualizer.py topology.json  # Test visualizer
```

## 📝 Example Workflow

```bash
# 1. Generate topology and analysis
python src/main.py --config-dir tests/sample_configs --output my_network.json --analyze --validate --visualize --verbose

# 2. View results
# - Open my_network_visualization.html in browser
# - Review console output for analysis results
# - Check my_network.json for raw topology data

# 3. Generate additional visualizations
python src/visualization/topology_visualizer.py my_network.json --output clean_view.html

# 4. Test scenarios
python scenarios/day1_scenario.py
python scenarios/day2_scenario.py
```

## 🎉 Success Indicators

✅ **Topology Generation**: JSON file created with 10 devices and 19 links  
✅ **Visualization**: HTML file opens in browser showing hierarchical network  
✅ **Analysis**: Console shows network statistics and recommendations  
✅ **Validation**: No configuration issues reported  
✅ **Interactive Features**: Click, hover, zoom, and export work in HTML

## 📞 Support

For issues or questions:

1. Check the console output for error messages
2. Verify input file formats match expected configuration syntax
3. Ensure all required files are present in the configuration directory
4. Test with the provided sample configurations first

---

**Network Topology Analyzer** - Professional network documentation and visualization tool
