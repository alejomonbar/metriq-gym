import numpy as np
import networkx as nx
import math
from docplex.mp.model import Model


def weighted_maxcut_solver(G: nx.Graph) -> str:
    """Constructs a mathematical model for the Max-Cut problem using the CPLEX solver.
    This function creates a binary optimization model to maximize the cut in a weighted graph.
    Args:
        G (networkx.Graph): The input weighted graph where edges represent cut costs.
    Returns:
        str: A binary string representing the optimal partition of the graph nodes (e.g., "1010").
    """
    mdl = Model("MaxCut")
    num_nodes = G.number_of_nodes()
    x = {i: mdl.binary_var(name=f"x_{i}") for i in range(num_nodes)}
    mdl.minimize(mdl.sum(G[i][j]["weight"] * (2 * x[i] * x[j] - x[i] - x[j]) for (i, j) in G.edges))
    mdl.solve()
    optimal_solution = "".join(
        str(round(mdl.solution.get_value(var))) for var in mdl.iter_binary_vars()
    )
    return optimal_solution


def cost_maxcut(bitstring: str, G: nx.Graph) -> float:
    """
    Computes the cost of a given bitstring solution for the Max-Cut problem.

    Parameters:
    bitstring (str): A binary string representing a partition of the graph nodes (e.g., "1010").
    G (networkx.Graph): The input weighted graph where edges represent cut costs.

    Returns:
    float: The computed cost of the Max-Cut solution.
    """
    cost = 0
    for i, j in G.edges():
        if bitstring[i] + bitstring[j] in ["10", "01"]:
            cost += G[i][j]["weight"]
    return cost


def objective_func(samples_dict: dict, G: nx.Graph, optimal: str) -> dict:
    """
    Evaluates the performance of LR-QAOA for the Max-Cut problem.

    Parameters:
    samples_dict (dict): A dictionary where keys are bitstrings (binary solutions),
                         and values are their occurrence counts.
    G (networkx.Graph): The input weighted graph where edges represent cut costs.
    optimal (str): The optimal bitstring solution found by classical solvers (e.g., CPLEX).

    Returns:
    dict: A dictionary containing:
        - "r": The expected approximation ratio.
        - "probability": The probability of sampling the optimal solution.
    """

    max_cost = cost_maxcut(optimal, G)
    probability = 0.0
    total_cost = 0.0
    shots = 0.0
    for bitstring, counts in samples_dict.items():
        cost = cost_maxcut(bitstring, G)
        total_cost += counts * cost
        if math.isclose(cost, max_cost):
            probability += counts

        if cost > max_cost:
            print(f"There is a better cost than that of CPLEX: {cost - max_cost}")
        shots += counts
    r = total_cost / (max_cost * shots)
    probability /= shots
    return {"r": r, "probability": probability}


def random_samples(num_samples: int, n_qubits: int) -> dict:
    """
    Generates random bitstring samples for a given number of qubits.

    Parameters:
    num_samples (int): The number of random bitstrings to generate.
    n_qubits (int): The number of qubits (length of each bitstring).

    Returns:
    dict: A dictionary where keys are randomly generated bitstrings
          and values are their occurrence counts.
    """

    random_samples = {}

    for _ in range(num_samples):
        bitstring = "".join(str(i) for i in np.random.choice([0, 1], n_qubits))
        if bitstring not in random_samples:
            random_samples[bitstring] = 0
        random_samples[bitstring] += 1

    return random_samples


def decode_parity(sample: str, p_layers: int, list_parity: list) -> str:
    """Decodes a sample based on the parity list and the number of layers (p).

    Parameters:
        sample (str): A binary string representing the sample.
        p (int): The number of layers in the QAOA circuit.
        list_parity (list): A list of lists where each sublist contains indices of qubits
                           that share the same parity in the sample.
    Returns:
        str: A binary string representing the decoded sample.
    """

    depth = len(list_parity)
    spin = {1: "0", -1: "1"}
    sz = [(1 if i == "0" else -1) for i in sample]
    nq = len(sample)
    x = nq * [0]
    if p_layers % 2 == 0:
        list_parity = list_parity[0]
        list_q = list(range(nq))
    else:
        list_parity = list_parity[-1]
        list_q = list(reversed(range(depth))) + list(range(depth, nq))
    for i in list_q:
        if len(list_parity[i]) == 1:
            x[list_parity[i][0]] = sz[i]
        else:
            if x[list_parity[i][0]] != 0:
                x[list_parity[i][1]] = sz[i] / x[list_parity[i][0]]
            elif x[list_parity[i][1]] != 0:
                x[list_parity[i][0]] = sz[i] / x[list_parity[i][1]]
            else:
                print(list_parity[i])
    return "".join(spin[xi] for xi in x)
