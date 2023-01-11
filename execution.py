import matplotlib.pyplot as plt
import networkx as nx
import pydot
from agent.modelling import Model
from networkx.drawing.nx_pydot import graphviz_layout

from agent.base_utils import *
from agent.node import *
import numpy as np
import matplotlib.pyplot as plt
from networkx.drawing.nx_pydot import graphviz_layout
import matplotlib as mpl


def to_digraph(blockchain):
    G = nx.DiGraph()
    for b in blockchain:
        G.add_node(b.value)
        if b.parent:
            G.add_edge(b.value, b.parent.value)
    return G


def get_cummulative_weight_subTree(slot, given_block, attestations):
    # optimize this with dynamic programming approach
    total_weights = 0

    if slot not in attestations.keys():
        return total_weights

    slot_block_weights = {}
    for block in attestations[slot].values():
        if block in slot_block_weights.keys():
            slot_block_weights[block] += 1
        else:
            slot_block_weights[block] = 1

    if len(given_block.children) == 0 and given_block in slot_block_weights.keys():
        total_weights += slot_block_weights[given_block]

    else:
        total_weights += slot_block_weights[given_block] if given_block in slot_block_weights.keys(
        ) else 0
        for block in given_block.children:
            total_weights += get_cummulative_weight_subTree(
                block.slot, block, attestations)

    return total_weights


def draw_blockchain(all_known_blocks, attestations, head_block, genesis_block, node):
    total_attestations = sum([get_cummulative_weight_subTree(
        b.slot, b, attestations) for b in genesis_block.children])
    total_attestations =  total_attestations if total_attestations > 0 else 1
    block_weights = {b.value: get_cummulative_weight_subTree(
        b.slot, b, attestations) if b.value != '0' else total_attestations for b in all_known_blocks}

    block_children = {b.value: 
        b.children for b in all_known_blocks}

    print(block_weights, block_children)

    weight_list = [block_weights[b.value] for b in all_known_blocks]


    labels = {b.value: str(block_weights[b.value]) for b in all_known_blocks}
    for k in labels:
        if labels[k] == 0:
            labels[k] = '0'

    fig, ax = plt.subplots(figsize=(5, 5), dpi=150)

    T = to_digraph(all_known_blocks)

    pos = graphviz_layout(T, prog="dot")

    nx.draw_networkx_nodes(T, nodelist=[head_block[1].value],
                           pos=pos, node_shape='s', node_size=500,
                           node_color='cornflowerblue', alpha=0.5, ax=ax)

    nx.draw_networkx_nodes(T, pos=pos, node_shape='s',
                           node_size=[150+(1000/total_attestations)
                                      * block_weights[n] for n in pos.keys()],
                           node_color='fuchsia', edgecolors='fuchsia', alpha=0.3,
                           ax=ax)

    nx.draw_networkx_nodes(T, node_shape='s', edgecolors='k',
                           node_color=weight_list,
                           cmap=mpl.cm.YlGn, pos=pos, node_size=150, ax=ax)

    nx.draw_networkx_labels(T, pos=pos, labels=labels,
                            font_size=8, font_color='k', ax=ax)

    nx.draw_networkx_edges(T, pos=pos, node_shape='s', node_size=150, ax=ax)

    fig.savefig('chain_layout{}.png'.format(node.id), dpi='figure')


if __name__ == "__main__":
    # As mentioned in the Stochatic Modelling paper,
    # the number of neighbors fixed but have to experiment multiple topologies
    net_p2p = nx.barabasi_albert_graph(
        64, 3)
    lcc_set = max(nx.connected_components(net_p2p), key=len)
    net_p2p = net_p2p.subgraph(lcc_set).copy()
    net_p2p = nx.convert_node_labels_to_integers(
        net_p2p, first_label=0)

    fig, ax = plt.subplots(figsize=(5, 5), dpi=150)
    pos = nx.nx_pydot.graphviz_layout(net_p2p, prog="dot")
    nx.draw_networkx_nodes(net_p2p, pos, ax=ax)
    nx.draw_networkx_edges(net_p2p, pos, ax=ax)

    fig.savefig('network_layout.png')

    model = Model(
        graph=net_p2p,
        tau_block=5,
        tau_attest=5,
        malicious_percent=0
    )
    model.run(100)

    rng_node = np.random.default_rng().choice(model.validators)
    rng_node.gasper.lmd_ghost(rng_node.attestations)
    print(rng_node.gasper.consensus_chain)
    print(model.results())
    draw_blockchain(model.god_view_blocks, rng_node.attestations,
                    rng_node.gasper.get_head_block(), model.genesis_block, rng_node)

    rng_node2 = np.random.default_rng().choice(model.validators)
    rng_node2.gasper.lmd_ghost(rng_node2.attestations)
    print(model.results())
    print(rng_node2.gasper.consensus_chain)
    draw_blockchain(model.god_view_blocks, rng_node2.attestations,
                    rng_node2.gasper.get_head_block(), model.genesis_block, rng_node2)
