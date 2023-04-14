import matplotlib.pyplot as plt
import networkx as nx
import pydot
from agent.modeling import Model
from networkx.drawing.nx_pydot import graphviz_layout

from agent.base_utils import *
from agent.node import *
import numpy as np
import matplotlib.pyplot as plt
from networkx.drawing.nx_pydot import graphviz_layout
import matplotlib as mpl


# dynamic_programming
central_block_weight = {}
central_attestation_weight = {}


def to_digraph(blockchain):
    G = nx.DiGraph()
    for b in blockchain:
        G.add_node(b.value)
        if b.parent:
            G.add_edge(b.value, b.parent.value)
    return G


def get_cummulative_weight_subTree(given_block, attestations):
    total_weights = 0
    only_attestation_weights = 0

    for slot in attestations.keys():
        for block in attestations[slot].values():
            if given_block == block:
                total_weights += 1
                only_attestation_weights += 1

    if len(given_block.children) != 0:
        for block in given_block.children:
            total_weights += get_cummulative_weight_subTree(block, attestations)[
                0]

    return total_weights, only_attestation_weights


def draw_blockchain(all_known_blocks, nodes_at, head_block, name):
    attestations = {}
    for node, attestation in nodes_at.items():
        if attestation.slot not in attestations.keys():
            attestations.update({attestation.slot: {
                node: attestation.block}})
        else:
            attestations[attestation.slot].update(
                {node: attestation.block})

    T = to_digraph(all_known_blocks)
    pos = graphviz_layout(T, prog="dot")

    weights = {b.value: get_cummulative_weight_subTree(
        b, attestations, ) for b in all_known_blocks}
    block_weights = {block: total_weight[0]
                     for block, total_weight in weights.items()}
    attestations_weights = {block: total_weight[1]
                            for block, total_weight in weights.items()}

    total_attestations = sum([attestations_weights[b] for b in pos.keys()])

    print(total_attestations)
    weight_list = [block_weights[b] for b in pos.keys()]
    attest_list = [attestations_weights[b] for b in pos.keys()]

    labels = {b: str(block_weights[b]) for b in pos.keys()}
    for k in labels:
        if labels[k] == 0:
            labels[k] = '0'

    fig, ax = plt.subplots(figsize=(15, 15), dpi=300)

    # pos = {k: (v[0], (1 + [b.slot for b in all_known_blocks if b.value == k][0])*40.0) for k,v in pos.items()}

    nx.draw_networkx_nodes(T, nodelist=[head_block[1].value],
                           pos=pos, node_shape='s', node_size=500,
                           node_color='cornflowerblue', alpha=0.5, ax=ax)

    nx.draw_networkx_nodes(T, pos=pos, node_shape='s',
                           node_size=[150+(10000/total_attestations)
                                      * n for n in attest_list],
                           node_color='grey', edgecolors='black', alpha=0.1,
                           ax=ax)

    nx.draw_networkx_nodes(T, node_shape='s', edgecolors='k',
                           node_color=weight_list,
                           cmap=mpl.cm.YlGn, pos=pos, node_size=150, ax=ax)

    nx.draw_networkx_labels(T, pos=pos, labels=labels,
                            font_size=8, font_color='k', ax=ax)

    nx.draw_networkx_edges(T, pos=pos, node_shape='s', node_size=150, ax=ax)

    fig.savefig('chain_layout_con-teja_{}.png'.format(name), dpi='figure')


if __name__ == "__main__":
    # As mentioned in the Stochatic Modelling paper,
    # the number of neighbors fixed but have to experiment multiple topologies
    net_p2p = nx.barabasi_albert_graph(
        128, 4)
    lcc_set = max(nx.connected_components(net_p2p), key=len)
    net_p2p = net_p2p.subgraph(lcc_set).copy()
    net_p2p = nx.convert_node_labels_to_integers(
        net_p2p, first_label=0)

    model = Model(
        graph=net_p2p,
        tau_block=10,
        tau_attest=1,
        malicious_percent=0.35,
        adversary_offset=10,
        proposer_vote_boost=0.1,
    )

    model.run(200)

    end_state = ChainState(model.time, model.epoch_event.counter,
                           model.slot_event.counter, 0, 0, model.genesis_block)
    rng_node = np.random.default_rng().choice(model.validators)
    rng_node.gasper.lmd_ghost(end_state, rng_node.state)

    draw_blockchain(list(model.chain_state.god_view_blocks), rng_node.state.nodes_at,
                    rng_node.gasper.get_head_block(), "node1")

    rng_node2 = np.random.default_rng().choice(model.validators)
    rng_node2.gasper.lmd_ghost(end_state, rng_node2.state)

    draw_blockchain(list(model.chain_state.god_view_blocks), rng_node2.state.nodes_at,
                    rng_node2.gasper.get_head_block(), 'node2')

    print(model.results())
    # analyse_node = Node(model.genesis_block, 1000)
    # analyse_node.state.local_blockchain = model.chain_state.god_view_blocks

    # for slot, node_attestaions in model.chain_state.god_view_attestations.items():
    #     for node, block in node_attestaions.items():
    #             analyse_node.state.add_attestation(model.chain_state,
    #                 Attestation(node, block, slot))

    # analyse_node.gasper.lmd_ghost(model.chain_state, analyse_node.state)
    # draw_blockchain(list(model.chain_state.god_view_blocks), analyse_node.state.nodes_at,
    #                     analyse_node.gasper.get_head_block(), "god")
