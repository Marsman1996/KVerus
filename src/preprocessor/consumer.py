"""
Process consumer cases

DESIGN:
The whole concept here is library consumers(like UT) contain a lot of information
about how the API functions should be used. On the one hand, we can extract
the calling order of the APIs, and directly use them to generate the fuzz
driver. On the other hand, we can build a call graph from the consumer cases,
and use the call graph to evaluate the relevance of the API functions.

For calling order extraction, the process is:
1. Get all the API calling chains from the consumer cases. Only the direct calls are considered.
2. Since the calling chains may be too long or too short, we need to normalize them into
    a rather fixed size of OrderSet.
3. Since the number of calling chains may be huge, we need to minimize them using the Set Cover algorithm.

For call graph building, the process is:
1. Extract the caller-callee pairs from the consumer cases.
2. Build the call graph from the caller-callee pairs, on which every node is a function and
    every edge is a call relation.
3. Calculate the relevance of the API functions based on the shortest path length among them.
"""

from dataclasses import dataclass
from functools import cached_property, cache
from pathlib import Path
from loguru import logger
import pickle
import json
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import cpu_count
import subprocess
import tempfile
import shutil
from tqdm import tqdm

from src.utils import path_in_paths, FilePos


@dataclass
class CallGraphNode:
    """
    Class for a Call Graph Node
    """

    function_name: str
    """
    The function name
    """

    function_location: str
    """
    The function declaration location
    """

    caller: list["CallGraphNode"]
    """
    The list of functions that call this function
    """

    callee: list["CallGraphNode"]
    """
    The list of functions that this function calls
    """

    def __eq__(self, value):
        if isinstance(value, CallGraphNode):
            return self.function_location == value.function_location
        return False

    def __hash__(self):
        return hash(self.function_location)

    @classmethod
    def new_solitary_node(cls, function_name: str, function_location: str):
        """
        Create a CallGraphNode object with empty caller and callee

        :param function_name: The function name
        :param function_location: The function declaration location
        """
        return cls(function_name, function_location, [], [])

    def add_caller(self, caller: "CallGraphNode"):
        """
        Add a caller to the function

        :param caller: The caller function
        """
        if caller not in self.caller:
            self.caller.append(caller)

    def add_callee(self, callee: "CallGraphNode"):
        """
        Add a callee to the function

        :param callee: The callee function
        """
        if callee not in self.callee:
            self.callee.append(callee)


class CallGraph:
    """
    Class for Call Graph
    """

    def __init__(self):
        """
        Initialize the Call Graph
        """
        # The dictionary of call nodes, key is the function location
        self.call_nodes: dict[str, CallGraphNode] = {}
        # The list of API nodes
        self.api_nodes: list[CallGraphNode] = []

    def add_call(
        self,
        caller_name: str,
        caller_location: str,
        callee_name: str,
        callee_location: str,
    ):
        """
        Add a call from caller to callee

        :param caller_name: The caller function name
        :param caller_location: The caller function declaration location
        :param callee_name: The callee function name
        :param callee_location: The callee function declaration location
        """
        # create the caller and callee nodes or get them if they already exist
        if caller_location in self.call_nodes:
            caller = self.call_nodes[caller_location]
        else:
            caller = CallGraphNode.new_solitary_node(caller_name, caller_location)
        if callee_location in self.call_nodes:
            callee = self.call_nodes[callee_location]
        else:
            callee = CallGraphNode.new_solitary_node(callee_name, callee_location)

        # add the call
        caller.add_callee(callee)
        callee.add_caller(caller)

        # add to the call_nodes dictionary
        self.call_nodes[caller_location] = caller
        self.call_nodes[callee_location] = callee

    def traverse(self, start_node: CallGraphNode, is_directed_graph: bool = True):
        """
        Traverse the call graph from the start_node using BFS, emitting nodes and distance as a Generator.

        :param start_node: The node to start the traversal
        :param is_directed_graph: Whether the graph is directed. If False, the traversal will be undirected.
        :return: The Generator of nodes and distance
        """
        visited = set()
        queue = [(start_node, 0)]
        while queue:
            node, distance = queue.pop(0)
            if node in visited:
                continue
            visited.add(node)
            yield node, distance
            for callee in node.callee:
                queue.append((callee, distance + 1))
            if not is_directed_graph:
                for caller in node.caller:
                    queue.append((caller, distance + 1))

    @cache
    def reachable_nodes(
        self, start_node: CallGraphNode, is_directed_graph: bool = True
    ) -> list[CallGraphNode]:
        """
        Get the reachable nodes from the start_node using BFS

        :param start_node: The node to start the traversal
        :param is_directed_graph: Whether the graph is directed. If False, the traversal will be undirected.
        :return: The set of reachable nodes
        """
        return [node for node, _ in self.traverse(start_node, is_directed_graph)]

    def dump(self, path: Path):
        """
        Dump the Call Graph to a file

        :param path: The path to the file
        """
        with open(path, "wb") as f:
            pickle.dump(self.call_nodes, f)

    @classmethod
    def load(cls, path: Path) -> "CallGraph":
        """
        Load the Call Graph from a file

        :param path: The path to the file
        """
        with open(path, "rb") as f:
            call_nodes = pickle.load(f)
        call_graph = cls()
        call_graph.call_nodes = call_nodes

        return call_graph

    def dump_json(self, path: Path):
        """
        Dump the Call Graph to a JSON file, only for human-readable, not for loading

        :param path: The path to the file
        """
        data = {
            f"{node.function_name}@{node.function_location}": {
                "caller": [
                    f"{caller.function_name}@{caller.function_location}"
                    for caller in node.caller
                ],
                "callee": [
                    f"{callee.function_name}@{callee.function_location}"
                    for callee in node.callee
                ],
            }
            for node in self.call_nodes.values()
        }
        with open(path, "w") as f:
            json.dump(data, f, indent=4)
