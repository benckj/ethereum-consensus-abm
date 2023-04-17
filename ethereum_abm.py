"""
    copyright 2022 uzh
    This file is part of ethereum-consensus-abm.
    ethereum-consensus-abm is free software: you can redistribute it and/or modify
    it under the terms of the GNU Lesser General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.
    ethereum-consensus-abm is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Lesser General Public License for more details.
    You should have received a copy of the GNU Lesser General Public License
    along with ethereum-consensus-abm.  If not, see <http://www.gnu.org/licenses/>.
"""

from spg.runner import SingleRunner
from agent.modeling import Model
import networkx as nx


def parse_command_line():
    import sys
    import optparse

    parser = optparse.OptionParser()

    parser.add_option("--repeat", action='store', dest="repeat", type='int',
                      default=None, help="number of repetitions")
    parser.add_option("--filter", action='store', dest="filter", type='str',
                      default=None, help="filter the parameters")
    parser.add_option("--workers", action='store', dest="workers", type='int',
                      default=None, help="number of workers")
    parser.add_option(
        "--rewrite",
        action='store_true',
        dest="rewrite",
        help="if the csv file - if existing - should be rewritten. If not added, append operation is performed"
    )

    command = sys.argv[0]
    options, args = parser.parse_args()

    return command, options, args


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
        malicious_percent=parameters['malicious_stake'],
        adversary_offset=parameters['adversary_offset'],
        proposer_vote_boost=parameters['proposer_vote_boost'],
    )
    model.run(parameters["simulation_time"])
    return model.results()


command, options, args = parse_command_line()


if __name__ == "__main__":
    for arg in args:
        runner = SingleRunner(arg, options.repeat)
        if options.filter is not None:
            runner.filter(options.filter)
        runner.run(run_simulation, options.workers)
        runner.save_results(options.rewrite)