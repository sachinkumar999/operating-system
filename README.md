# operating-system

# project name 
A tool that will detect potential deadlock in the system process

# Introduction
Deadlocks in system processes occur when two or more processes are stuck in a circular waiting state, preventing further execution. Our tool is designed to automatically detect potential deadlocks in an operating system, analyze resource allocation, and provide insights for resolution.

# How the Tool Works

1. Graph Representation of Process Dependencies
The tool represents system processes as a directed graph, where:
Nodes represent processes.
Edges indicate resource dependencies (e.g., Process A waiting for Process B).

2. Deadlock Detection Algorithm
Uses Kahn’s Algorithm (Topological Sorting) to detect cycles in the dependency graph.
Steps:
Calculate in-degree for each process (number of incoming dependencies).
Use BFS (Queue) to process nodes with zero in-degree.
If all processes are visited, no deadlock exists.
If some processes remain unvisited, they form a cycle (deadlock detected).

3. REST API Endpoints
/detect_deadlock (POST)
Accepts a JSON payload containing:
List of processes.
List of dependencies between processes.
Runs the deadlock detection algorithm.
Response:
✅ No Deadlock: Returns a success message.
⚠️ Deadlock Detected: Lists the processes involved in the deadlock.
/terminate_deadlock (POST)

Clears all processes and dependencies.
Response:
✅ Deadlocked processes terminated.

4. Running the Server
The tool runs on a local web server (http://localhost:5000) using Crow.
Supports multithreading for handling multiple requests efficiently.
Use Case Example
Send a POST request to /detect_deadlock with process dependencies.
If a deadlock is detected, the system reports the affected processes.
Send a POST request to /terminate_deadlock to remove deadlocked processes.
Re-run /detect_deadlock to confirm the issue is resolved.