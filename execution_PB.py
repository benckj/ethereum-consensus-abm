import matplotlib.pyplot as plt
import networkx as nx
import pydot
from agent_w_pb.modelling import Model
from networkx.drawing.nx_pydot import graphviz_layout

from agent_w_pb.base_utils import *
from agent_w_pb.node import *
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
            total_weights += get_cummulative_weight_subTree(block, attestations)[0]

    return total_weights, only_attestation_weights


def draw_blockchain(all_known_blocks, attestations, head_block):
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

    fig.savefig('chain_layout_{}.png'.format(int(np.random.random()*10)), dpi='figure')


if __name__ == "__main__":
    # As mentioned in the Stochatic Modelling paper,
    # the number of neighbors fixed but have to experiment multiple topologies
    net_p2p = nx.barabasi_albert_graph(
        32, 3)
    lcc_set = max(nx.connected_components(net_p2p), key=len)
    net_p2p = net_p2p.subgraph(lcc_set).copy()
    net_p2p = nx.convert_node_labels_to_integers(
        net_p2p, first_label=0)

    model = Model(
        graph=net_p2p,
        tau_block=0.5,
        tau_attest=0.5,
        malicious_percent=0,
        adversary_offset=0,
        proposer_vote_boost=0,
    )

    model.run(1000)
    print('\n Gods View Results',model.results())

    end_state = ChainState(model.time,model.epoch_event.counter, model.slot_event.counter, 0, 0, model.genesis_block)
    rng_node = np.random.default_rng().choice(model.validators)
    rng_node.gasper.lmd_ghost(end_state, rng_node.state)

    print('\n attestations', rng_node.gasper.get_latest_attestations(rng_node.state.attestations))
    print(rng_node.gasper.consensus_chain)
    print(model.results(rng_node))

    draw_blockchain(list(model.chain_state.god_view_blocks), rng_node.gasper.get_latest_attestations(rng_node.state.attestations),
                        rng_node.gasper.get_head_block())

    rng_node2 = np.random.default_rng().choice(model.validators)
    rng_node2.gasper.lmd_ghost(end_state, rng_node2.state)

    print('\n attestations', rng_node2.gasper.get_latest_attestations(rng_node2.state.attestations))
    print(rng_node2.gasper.consensus_chain)
    print(model.results(rng_node2))
    
    draw_blockchain(list(model.chain_state.god_view_blocks), rng_node2.gasper.get_latest_attestations(rng_node2.state.attestations),
                        rng_node2.gasper.get_head_block())