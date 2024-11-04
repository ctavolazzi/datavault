import matplotlib.pyplot as plt
import networkx as nx
from pathlib import Path
from typing import Dict, List

class GraphGenerator:
    """Generate dependency visualizations"""
    
    def __init__(self, theme: str = 'light'):
        self.theme = theme
        self._setup_colors()
    
    def _setup_colors(self):
        """Set up color scheme based on theme"""
        if self.theme == 'dark':
            self.bg_color = '#1c1c1c'
            self.text_color = 'white'
            self.edge_color = '#404040'
            self.source_color = '#4a9eff'
            self.target_color = '#ff4a4a'
        else:
            self.bg_color = 'white'
            self.text_color = 'black'
            self.edge_color = '#808080'
            self.source_color = '#4a9eff'
            self.target_color = '#ff4a4a'
    
    def generate_graph(self, dependencies: Dict[str, List[str]], 
                      style: str = 'spring') -> plt.Figure:
        """Generate a visualization of project dependencies"""
        # Create directed graph
        G = nx.DiGraph()
        
        # Add nodes and edges
        for source, targets in dependencies.items():
            source_name = Path(source).name
            G.add_node(source_name, type='source')
            for target in targets:
                target_name = Path(target).name
                G.add_node(target_name, type='target')
                G.add_edge(source_name, target_name)
        
        if not G.nodes():
            return None
        
        # Set up plot
        plt.figure(figsize=(12, 8))
        
        # Set node colors
        node_colors = [
            self.source_color if G.nodes[n].get('type') == 'source' 
            else self.target_color for n in G.nodes()
        ]
        
        # Set layout
        if style == 'spring':
            pos = nx.spring_layout(G, k=1, iterations=50, seed=42)
        elif style == 'circular':
            pos = nx.circular_layout(G)
        else:
            pos = nx.shell_layout(G)
        
        # Draw graph
        nx.draw(G, pos,
                node_color=node_colors,
                node_size=2000,
                edge_color=self.edge_color,
                with_labels=True,
                font_size=8,
                font_weight='bold',
                font_color=self.text_color,
                arrows=True,
                arrowsize=20)
        
        # Add legend
        legend_elements = [
            plt.Line2D([0], [0], marker='o', color='w', 
                      markerfacecolor=self.source_color, markersize=10, 
                      label='Source Files'),
            plt.Line2D([0], [0], marker='o', color='w', 
                      markerfacecolor=self.target_color, markersize=10, 
                      label='Target Files')
        ]
        plt.legend(handles=legend_elements, loc='upper right', 
                  facecolor=self.bg_color, labelcolor=self.text_color)
        
        # Set title and colors
        plt.title(f"Project Dependencies\n{len(G.nodes())} modules, {len(G.edges())} dependencies",
                 color=self.text_color, pad=20, size=14)
        
        plt.gca().set_facecolor(self.bg_color)
        plt.gcf().set_facecolor(self.bg_color)
        
        return plt.gcf()