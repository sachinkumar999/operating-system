import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import json
import os
from typing import Dict, List, Tuple, Set

class DeadlockDetector:
    def __init__(self):
        self.processes = {}  # process_id -> {resources_held, resources_waiting}
        self.resources = {}  # resource_id -> {allocated_to, waiting_processes}
        
    def add_process(self, process_id: str) -> None:
        """Add a new process to the system."""
        if process_id not in self.processes:
            self.processes[process_id] = {
                'resources_held': set(),
                'resources_waiting': set()
            }
    
    def add_resource(self, resource_id: str) -> None:
        """Add a new resource to the system."""
        if resource_id not in self.resources:
            self.resources[resource_id] = {
                'allocated_to': None,
                'waiting_processes': set()
            }
    
    def allocate_resource(self, process_id: str, resource_id: str) -> None:
        """Allocate a resource to a process."""
        # Add process and resource if they don't exist
        self.add_process(process_id)
        self.add_resource(resource_id)
        
        # Allocate the resource
        if self.resources[resource_id]['allocated_to'] is None:
            self.resources[resource_id]['allocated_to'] = process_id
            self.processes[process_id]['resources_held'].add(resource_id)
            
            # Remove from waiting if it was waiting
            if resource_id in self.processes[process_id]['resources_waiting']:
                self.processes[process_id]['resources_waiting'].remove(resource_id)
                self.resources[resource_id]['waiting_processes'].remove(process_id)
        else:
            # Resource is already allocated, add to waiting
            self.request_resource(process_id, resource_id)
    
    def request_resource(self, process_id: str, resource_id: str) -> None:
        """Process requests a resource but doesn't get it immediately."""
        # Add process and resource if they don't exist
        self.add_process(process_id)
        self.add_resource(resource_id)
        
        # Add to waiting lists
        if self.resources[resource_id]['allocated_to'] != process_id:
            self.processes[process_id]['resources_waiting'].add(resource_id)
            self.resources[resource_id]['waiting_processes'].add(process_id)
    
    def release_resource(self, process_id: str, resource_id: str) -> None:
        """Process releases a resource."""
        if (process_id in self.processes and 
            resource_id in self.processes[process_id]['resources_held']):
            
            # Release the resource
            self.processes[process_id]['resources_held'].remove(resource_id)
            self.resources[resource_id]['allocated_to'] = None
            
            # Could implement resource reallocation logic here
    
    def detect_deadlocks(self) -> Tuple[bool, List[List[str]], nx.DiGraph]:
        """
        Detect deadlocks in the system using a resource allocation graph.
        Returns a tuple: (deadlock_exists, cycles, graph)
        """
        # Create a directed graph
        G = nx.DiGraph()
        
        # Add all processes and resources as nodes
        for process_id in self.processes:
            G.add_node(process_id, type='process')
        
        for resource_id in self.resources:
            G.add_node(resource_id, type='resource')
        
        # Add edges for resource allocation and requests
        for resource_id, resource_data in self.resources.items():
            # Resource allocated to process (resource -> process)
            if resource_data['allocated_to']:
                G.add_edge(resource_id, resource_data['allocated_to'], type='allocation')
            
            # Process waiting for resource (process -> resource)
            for process_id in resource_data['waiting_processes']:
                G.add_edge(process_id, resource_id, type='request')
        
        # Find cycles in the graph
        try:
            cycles = list(nx.simple_cycles(G))
            return len(cycles) > 0, cycles, G
        except nx.NetworkXNoCycle:
            return False, [], G
    
    def suggest_resolutions(self, cycles: List[List[str]]) -> List[Dict]:
        """Suggest strategies to resolve the detected deadlocks."""
        resolutions = []
        
        for cycle in cycles:
            process_nodes = [node for node in cycle if node in self.processes]
            resource_nodes = [node for node in cycle if node in self.resources]
            
            # Strategy 1: Terminate a process
            for process in process_nodes:
                resolutions.append({
                    'type': 'terminate_process',
                    'target': process,
                    'description': f"Terminate process {process} to break the deadlock cycle."
                })
            
            # Strategy 2: Force resource preemption
            for resource in resource_nodes:
                current_owner = self.resources[resource]['allocated_to']
                if current_owner:
                    resolutions.append({
                        'type': 'preempt_resource',
                        'resource': resource,
                        'from_process': current_owner,
                        'description': f"Preempt resource {resource} from process {current_owner}."
                    })
            
            # Strategy 3: Reorder resource requests
            resolutions.append({
                'type': 'reorder_requests',
                'cycle': cycle,
                'description': f"Implement resource ordering to prevent circular wait: {' -> '.join(cycle)}."
            })
        
        return resolutions
    
    def export_to_json(self, filename: str) -> None:
        """Export the current state to a JSON file."""
        data = {
            'processes': {},
            'resources': {}
        }
        
        for process_id, process_data in self.processes.items():
            data['processes'][process_id] = {
                'resources_held': list(process_data['resources_held']),
                'resources_waiting': list(process_data['resources_waiting'])
            }
        
        for resource_id, resource_data in self.resources.items():
            data['resources'][resource_id] = {
                'allocated_to': resource_data['allocated_to'],
                'waiting_processes': list(resource_data['waiting_processes'])
            }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)
    
    def import_from_json(self, filename: str) -> None:
        """Import state from a JSON file."""
        with open(filename, 'r') as f:
            data = json.load(f)
        
        # Clear current state
        self.processes = {}
        self.resources = {}
        
        # Import processes
        for process_id, process_data in data['processes'].items():
            self.processes[process_id] = {
                'resources_held': set(process_data['resources_held']),
                'resources_waiting': set(process_data['resources_waiting'])
            }
        
        # Import resources
        for resource_id, resource_data in data['resources'].items():
            self.resources[resource_id] = {
                'allocated_to': resource_data['allocated_to'],
                'waiting_processes': set(resource_data['waiting_processes'])
            }

class DeadlockDetectorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Deadlock Detector")
        self.root.geometry("1200x800")
        
        self.detector = DeadlockDetector()
        self.canvas = None
        self.setup_ui()
        
    def setup_ui(self):
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create main tabs
        self.system_tab = ttk.Frame(self.notebook)
        self.analysis_tab = ttk.Frame(self.notebook)
        self.help_tab = ttk.Frame(self.notebook)
        
        self.notebook.add(self.system_tab, text="System Configuration")
        self.notebook.add(self.analysis_tab, text="Deadlock Analysis")
        self.notebook.add(self.help_tab, text="Help")
        
        # Set up each tab
        self.setup_system_tab()
        self.setup_analysis_tab()
        self.setup_help_tab()
        
    def setup_system_tab(self):
        # Create a frame for process management
        process_frame = ttk.LabelFrame(self.system_tab, text="Process Management")
        process_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        ttk.Label(process_frame, text="Process ID:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.process_id_entry = ttk.Entry(process_frame, width=15)
        self.process_id_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Button(process_frame, text="Add Process", command=self.add_process).grid(row=0, column=2, padx=5, pady=5)
        
        # Create a frame for resource management
        resource_frame = ttk.LabelFrame(self.system_tab, text="Resource Management")
        resource_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        
        ttk.Label(resource_frame, text="Resource ID:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.resource_id_entry = ttk.Entry(resource_frame, width=15)
        self.resource_id_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Button(resource_frame, text="Add Resource", command=self.add_resource).grid(row=0, column=2, padx=5, pady=5)
        
        # Create a frame for resource allocation
        allocation_frame = ttk.LabelFrame(self.system_tab, text="Resource Allocation")
        allocation_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")
        
        ttk.Label(allocation_frame, text="Process ID:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.alloc_process_id_entry = ttk.Entry(allocation_frame, width=15)
        self.alloc_process_id_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(allocation_frame, text="Resource ID:").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.alloc_resource_id_entry = ttk.Entry(allocation_frame, width=15)
        self.alloc_resource_id_entry.grid(row=0, column=3, padx=5, pady=5)
        
        ttk.Button(allocation_frame, text="Allocate", command=self.allocate_resource).grid(row=0, column=4, padx=5, pady=5)
        ttk.Button(allocation_frame, text="Request", command=self.request_resource).grid(row=0, column=5, padx=5, pady=5)
        ttk.Button(allocation_frame, text="Release", command=self.release_resource).grid(row=0, column=6, padx=5, pady=5)
        
        # Create a frame for the current system state
        state_frame = ttk.LabelFrame(self.system_tab, text="Current System State")
        state_frame.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")
        
        # Create a text widget to display the system state
        self.state_text = scrolledtext.ScrolledText(state_frame, width=80, height=15, wrap=tk.WORD)
        self.state_text.pack(padx=5, pady=5, fill="both", expand=True)
        self.state_text.config(state="disabled")
        
        # Create a frame for file operations
        file_frame = ttk.LabelFrame(self.system_tab, text="File Operations")
        file_frame.grid(row=3, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")
        
        ttk.Button(file_frame, text="Save Configuration", command=self.save_config).grid(row=0, column=0, padx=5, pady=5)
        ttk.Button(file_frame, text="Load Configuration", command=self.load_config).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(file_frame, text="Clear All", command=self.clear_all).grid(row=0, column=2, padx=5, pady=5)
        
        # Configure grid weights
        self.system_tab.columnconfigure(0, weight=1)
        self.system_tab.columnconfigure(1, weight=1)
        self.system_tab.rowconfigure(2, weight=1)
        
        # Update the state display
        self.update_state_display()
        
    def setup_analysis_tab(self):
        # Create a frame for analysis controls
        controls_frame = ttk.Frame(self.analysis_tab)
        controls_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Button(controls_frame, text="Detect Deadlocks", command=self.detect_deadlocks).pack(side="left", padx=5)
        
        # Create a frame for the graph visualization
        graph_frame = ttk.LabelFrame(self.analysis_tab, text="Resource Allocation Graph")
        graph_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # We'll create the figure when needed
        self.graph_container = ttk.Frame(graph_frame)
        self.graph_container.pack(fill="both", expand=True)
        
        # Create a frame for the analysis results
        results_frame = ttk.LabelFrame(self.analysis_tab, text="Analysis Results")
        results_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.results_text = scrolledtext.ScrolledText(results_frame, width=80, height=15, wrap=tk.WORD)
        self.results_text.pack(padx=5, pady=5, fill="both", expand=True)
        self.results_text.config(state="disabled")
        
    def setup_help_tab(self):
        # Create a scrolled text widget for the help content
        help_text = scrolledtext.ScrolledText(self.help_tab, width=80, height=30, wrap=tk.WORD)
        help_text.pack(padx=10, pady=10, fill="both", expand=True)
        
        # Add help content
        help_content = """
# Deadlock Detector Tool - Help Guide

## Overview
This tool helps you detect and analyze potential deadlocks in a system by modeling processes and resources and their interdependencies.

## Key Concepts
- **Process**: A running program or thread that needs resources to complete its task.
- **Resource**: An entity that can be used by processes (e.g., CPU, memory, files, devices).
- **Deadlock**: A situation where two or more processes are unable to proceed because each is waiting for resources held by others.

## Conditions for Deadlock
1. **Mutual Exclusion**: At least one resource must be held in a non-sharable mode.
2. **Hold and Wait**: Processes holding resources can request additional resources.
3. **No Preemption**: Resources cannot be forcibly taken from processes.
4. **Circular Wait**: A circular chain of processes exists, where each process holds resources needed by the next process.

## Using the Tool

### System Configuration Tab
- **Add Process**: Create a new process in the system.
- **Add Resource**: Create a new resource in the system.
- **Resource Allocation**:
  - **Allocate**: Assign a resource to a process (the process now holds this resource).
  - **Request**: Make a process wait for a resource that is currently allocated to another process.
  - **Release**: Free a resource that a process was holding.
- **Save/Load Configuration**: Export or import the current system state.

### Deadlock Analysis Tab
- **Detect Deadlocks**: Analyze the current system state to find potential deadlocks.
- **Resource Allocation Graph**: Visual representation of processes, resources, and their relationships.
- **Analysis Results**: Details of any detected deadlocks and suggested resolution strategies.

## Resolution Strategies
1. **Process Termination**: End one or more processes involved in the deadlock.
2. **Resource Preemption**: Force a process to release resources.
3. **Resource Ordering**: Implement a hierarchical ordering of resource requests to prevent circular wait.

## Example Scenario
1. Add processes P1, P2, P3
2. Add resources R1, R2, R3
3. Allocate R1 to P1
4. Allocate R2 to P2
5. Make P1 request R2
6. Make P2 request R1
7. Detect deadlocks
8. A deadlock will be found between P1 and P2
        """
        
        help_text.insert(tk.END, help_content)
        help_text.config(state="disabled")
    
    def add_process(self):
        process_id = self.process_id_entry.get().strip()
        if not process_id:
            messagebox.showerror("Error", "Please enter a process ID")
            return
        
        self.detector.add_process(process_id)
        self.process_id_entry.delete(0, tk.END)
        self.update_state_display()
    
    def add_resource(self):
        resource_id = self.resource_id_entry.get().strip()
        if not resource_id:
            messagebox.showerror("Error", "Please enter a resource ID")
            return
        
        self.detector.add_resource(resource_id)
        self.resource_id_entry.delete(0, tk.END)
        self.update_state_display()
    
    def allocate_resource(self):
        process_id = self.alloc_process_id_entry.get().strip()
        resource_id = self.alloc_resource_id_entry.get().strip()
        
        if not process_id or not resource_id:
            messagebox.showerror("Error", "Please enter both process ID and resource ID")
            return
        
        self.detector.allocate_resource(process_id, resource_id)
        self.update_state_display()
    
    def request_resource(self):
        process_id = self.alloc_process_id_entry.get().strip()
        resource_id = self.alloc_resource_id_entry.get().strip()
        
        if not process_id or not resource_id:
            messagebox.showerror("Error", "Please enter both process ID and resource ID")
            return
        
        self.detector.request_resource(process_id, resource_id)
        self.update_state_display()
    
    def release_resource(self):
        process_id = self.alloc_process_id_entry.get().strip()
        resource_id = self.alloc_resource_id_entry.get().strip()
        
        if not process_id or not resource_id:
            messagebox.showerror("Error", "Please enter both process ID and resource ID")
            return
        
        self.detector.release_resource(process_id, resource_id)
        self.update_state_display()
    
    def save_config(self):
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            self.detector.export_to_json(filename)
            messagebox.showinfo("Success", f"Configuration saved to {filename}")
    
    def load_config(self):
        filename = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                self.detector.import_from_json(filename)
                self.update_state_display()
                messagebox.showinfo("Success", f"Configuration loaded from {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load configuration: {str(e)}")
    
    def clear_all(self):
        if messagebox.askyesno("Confirm", "Are you sure you want to clear all data?"):
            self.detector = DeadlockDetector()
            self.update_state_display()
            
            # Clear the graph if it exists
            if self.canvas:
                for widget in self.graph_container.winfo_children():
                    widget.destroy()
                self.canvas = None
            
            # Clear the results text
            self.results_text.config(state="normal")
            self.results_text.delete(1.0, tk.END)
            self.results_text.config(state="disabled")
    
    def update_state_display(self):
        # Update the state text widget with the current system state
        self.state_text.config(state="normal")
        self.state_text.delete(1.0, tk.END)
        
        # Display processes
        self.state_text.insert(tk.END, "PROCESSES:\n")
        for process_id, process_data in self.detector.processes.items():
            resources_held = ", ".join(process_data['resources_held']) or "None"
            resources_waiting = ", ".join(process_data['resources_waiting']) or "None"
            
            self.state_text.insert(tk.END, f"Process {process_id}:\n")
            self.state_text.insert(tk.END, f"  Resources held: {resources_held}\n")
            self.state_text.insert(tk.END, f"  Resources waiting: {resources_waiting}\n\n")
        
        # Display resources
        self.state_text.insert(tk.END, "RESOURCES:\n")
        for resource_id, resource_data in self.detector.resources.items():
            allocated_to = resource_data['allocated_to'] or "None"
            waiting_processes = ", ".join(resource_data['waiting_processes']) or "None"
            
            self.state_text.insert(tk.END, f"Resource {resource_id}:\n")
            self.state_text.insert(tk.END, f"  Allocated to: {allocated_to}\n")
            self.state_text.insert(tk.END, f"  Waiting processes: {waiting_processes}\n\n")
        
        self.state_text.config(state="disabled")
    
    def detect_deadlocks(self):
        # Clear previous results
        self.results_text.config(state="normal")
        self.results_text.delete(1.0, tk.END)
        
        # Detect deadlocks
        has_deadlock, cycles, graph = self.detector.detect_deadlocks()
        
        if has_deadlock:
            self.results_text.insert(tk.END, "DEADLOCK DETECTED!\n\n")
            
            # Display the cycles
            self.results_text.insert(tk.END, "Deadlock Cycles:\n")
            for i, cycle in enumerate(cycles):
                self.results_text.insert(tk.END, f"Cycle {i+1}: {' -> '.join(cycle)} -> {cycle[0]}\n")
            
            self.results_text.insert(tk.END, "\n")
            
            # Display resolution suggestions
            resolutions = self.detector.suggest_resolutions(cycles)
            self.results_text.insert(tk.END, "Suggested Resolutions:\n")
            
            for i, resolution in enumerate(resolutions):
                self.results_text.insert(tk.END, f"{i+1}. {resolution['description']}\n")
        else:
            self.results_text.insert(tk.END, "No deadlocks detected in the current system state.\n")
        
        self.results_text.config(state="disabled")
        
        # Update the graph visualization
        self.visualize_graph(graph)
    
    def visualize_graph(self, graph):
        # Clear existing graph
        for widget in self.graph_container.winfo_children():
            widget.destroy()
        
        # Create a new figure
        fig, ax = plt.subplots(figsize=(8, 6))
        
        # Separate process and resource nodes for better visualization
        process_nodes = [node for node, attr in graph.nodes(data=True) if attr.get('type') == 'process']
        resource_nodes = [node for node, attr in graph.nodes(data=True) if attr.get('type') == 'resource']
        
        # Create node positions - processes on left, resources on right
        pos = {}
        
        # Position process nodes on the left
        for i, node in enumerate(process_nodes):
            pos[node] = (0.25, (len(process_nodes) - i) / (len(process_nodes) + 1))
        
        # Position resource nodes on the right
        for i, node in enumerate(resource_nodes):
            pos[node] = (0.75, (len(resource_nodes) - i) / (len(resource_nodes) + 1))
        
        # Draw nodes
        nx.draw_networkx_nodes(graph, pos, 
                              nodelist=process_nodes, 
                              node_color='lightblue', 
                              node_size=700, 
                              ax=ax)
        
        nx.draw_networkx_nodes(graph, pos, 
                              nodelist=resource_nodes, 
                              node_color='lightgreen', 
                              node_shape='s',  # square shape for resources
                              node_size=700, 
                              ax=ax)
        
        # Draw edges with different colors for allocation and request
        allocation_edges = [(u, v) for u, v, attr in graph.edges(data=True) if attr.get('type') == 'allocation']
        request_edges = [(u, v) for u, v, attr in graph.edges(data=True) if attr.get('type') == 'request']
        
        nx.draw_networkx_edges(graph, pos, 
                              edgelist=allocation_edges, 
                              edge_color='green', 
                              arrows=True, 
                              ax=ax)
        
        nx.draw_networkx_edges(graph, pos, 
                              edgelist=request_edges, 
                              edge_color='red', 
                              style='dashed',
                              arrows=True, 
                              ax=ax)
        
        # Draw labels
        nx.draw_networkx_labels(graph, pos, font_size=10, ax=ax)
        
        # Add a legend
        from matplotlib.lines import Line2D
        legend_elements = [
            Line2D([0], [0], marker='o', color='w', markerfacecolor='lightblue', markersize=15, label='Process'),
            Line2D([0], [0], marker='s', color='w', markerfacecolor='lightgreen', markersize=15, label='Resource'),
            Line2D([0], [0], color='green', lw=2, label='Allocation'),
            Line2D([0], [0], color='red', lw=2, linestyle='--', label='Request')
        ]
        ax.legend(handles=legend_elements, loc='upper center', bbox_to_anchor=(0.5, 1.1), ncol=4)
        
        # Remove axis
        ax.axis('off')
        
        # Display the graph in the GUI
        self.canvas = FigureCanvasTkAgg(fig, master=self.graph_container)
        canvas_widget = self.canvas.get_tk_widget()
        canvas_widget.pack(fill="both", expand=True)
        self.canvas.draw()


def main():
    root = tk.Tk()
    app = DeadlockDetectorGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()