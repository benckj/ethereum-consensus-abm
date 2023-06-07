from eth_base import *

def __set_up_topology(parameters):
    topology = parameters['network_topology']
    number_of_nodes = parameters['no_nodes']
    desired_avg_degree = parameters['no_neighs']
    ba_m = parameters['no_neighs']

    # generate network depending on topology parameter
    if topology == "UNIFORM":
        net_p2p = nx.random_degree_sequence_graph(
            [desired_avg_degree for i in range(number_of_nodes)])

    elif topology == "ER":
        p = desired_avg_degree / (number_of_nodes - 1)
        net_p2p = nx.fast_gnp_random_graph(number_of_nodes, p)

    elif topology == "BA":
        net_p2p = nx.barabasi_albert_graph(number_of_nodes, ba_m)

    elif topology == "SBM":
        sbm_p_inter = parameters['p_sbm_inter']
        p_intra = desired_avg_degree/number_of_nodes*(1-sbm_p_inter)
        p_inter = desired_avg_degree/number_of_nodes*sbm_p_inter
        net_p2p = nx.stochastic_block_model(
                [
                    number_of_nodes//2,
                    number_of_nodes//2
                ],
                [
                    [p_intra, p_inter],
                    [p_inter, p_intra]
                ]
                    )

    elif topology == "TREE":
        tree_r = parameters['tree_r']
        net_p2p = nx.full_rary_tree(tree_r, number_of_nodes)

    # get largest connected component
    lcc_set = max(nx.connected_components(net_p2p), key=len)
    net_p2p = net_p2p.subgraph(lcc_set).copy()
    # some nodes may have been removed because they were not port of the lcc.
    # relabel nodes so that only nodes in lcc are labelled.
    # (without it we run into problems where node labels are higher than the
    # number of nodes -> loops run into indexing problems)
    net_p2p = nx.convert_node_labels_to_integers(
        net_p2p, first_label=0)

    # some nodes may have been removed as they were not part of the lcc
    # -> update num nodes
    number_of_nodes = len(net_p2p)

    return net_p2p


def run_simulation(parameters):
    """Simulation wrapper
    INPUTS:
    OUTPUTS:
    - results,  dict
    """
    model = Model(
            graph=__set_up_topology(parameters),
            tau_block=parameters['tau_block'],
            tau_attest=parameters['tau_attestation'],
            delay_share=parameters['delay_share'],
            delay_time=parameters['delay_time'],
            )
    model.run(parameters["simulation_time"])
    return model.results()

if __name__ == "__main__":

    parameters = {}
    parameters['tau_block'] = 5
    parameters['tau_attestation'] = 5
    parameters['delay_share'] = 0.5
    parameters['delay_time'] = 11.9
    parameters['network_topology'] = "ER"
    parameters['no_nodes'] = 30
    parameters['no_neighs'] = 3
    parameters['simulation_time'] = 1000

    res = run_simulation(parameters)
    print(res)
