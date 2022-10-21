import networkx as nx

'''
FUNCTIONS
'''
'''
LMD Ghost following functions handle LMD Ghost Evaluation of Blocks
'''

def find_leaves_of_blockchain(blockchain):
    parent_blocks = {b.parent for b in blockchain}
    return blockchain - parent_blocks

def lmd_ghost(blockchain, attestations, stake=uniform_stake):
    #identify leaf blocks
    leaves = find_leaves_of_blockchain(blockchain)
    if len(leaves)==1:
        return leaves.pop()
        
    #invert attestations: from node:block to block:[nodes]
    inverse_attestations= {}
    for n, b in attestations.items():
        inverse_attestations[b] = inverse_attestations.get(b, []) + [n]


    if len(attested_blocks)==0:
        return next(iter(blockchain))

    lowest_attestation = next(iter(attested_blocks))
    for b in attested_blocks:
        if b.height < lowest_attestation.height:
            lowest_attestation = b

    if lowest_attestation.height == 0:
        cut_trees_per_leave = {b:b.predecessors for b in leaves}
    else:
        cut_trees_per_leave = {b:b.predecessors - lowest_attestation.parent.predecessors for b in leaves}

    attested_blocks_per_leaf = {b: cut_trees_per_leave[b] & attested_blocks for b in leaves}
    attested_blocks_per_leaf = {b: n for b, n in attested_blocks_per_leaf.items() if n}
    if attested_blocks_per_leaf.keys()==1:
        return next(iter(attested_blocks_per_leaf.keys()))

    leaves_with_attestations = set(attested_blocks_per_leaf.keys())

    attestations_per_leaf  = {b:[inverse_attestations[x] for x in attested_blocks_per_leaf[b]] for b in leaves_with_attestations}
    attestations_per_leaf  = {b:[node for nodes in n for node in nodes] for b,n in attestations_per_leaf.items()}

    sum_attestations_per_leaf = {b:sum([uniform_stake(n) for n in attestations_per_leaf[b]]) for b in leaves_with_attestations}
    return max(sum_attestations_per_leaf, key=sum_attestations_per_leaf.get)