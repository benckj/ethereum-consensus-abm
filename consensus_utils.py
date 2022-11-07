
'''
FUNCTIONS
'''
'''
LMD Ghost following functions handle LMD Ghost Evaluation of Blocks
'''

def find_leaves_of_blockchain(blockchain):
    parent_blocks = [b for b in blockchain if b.parent is not None]
    return blockchain[len(parent_blocks)-1:]

def simple_attestation_evaluation(n):
    return 1

def stake_attestation_evaluation(n):
    pass

def lmd_ghost(blockchain, attestations, stake=simple_attestation_evaluation):
    leaves = find_leaves_of_blockchain(blockchain)
    if len(leaves)==1:
        return leaves.pop()

    inverse_attestations= {}
    for n, b in attestations.items():
        inverse_attestations[b] = inverse_attestations.get(b, []) + [n]

    attested_blocks = set(inverse_attestations.keys())
    if len(attested_blocks)==0:
        return next(iter(blockchain))
    
    lowest_attestation = next(iter(attested_blocks))
    for b in attested_blocks:
        if b.height < lowest_attestation.height:
            lowest_attestation = b
            
    if lowest_attestation.height == 0:
        cut_trees_per_leave = {b:b.predecessors.copy() for b in leaves}
    else:
        cut_trees_per_leave = {b:b.predecessors - lowest_attestation.parent.predecessors for b in leaves}

    attested_blocks_per_leaf = {b: cut_trees_per_leave[b] & attested_blocks for b in leaves}
    attested_blocks_per_leaf = {b: n for b, n in attested_blocks_per_leaf.items() if n}
    if attested_blocks_per_leaf.keys()==1:
        return next(iter(attested_blocks_per_leaf.keys()))

    leaves_with_attestations = set(attested_blocks_per_leaf.keys())

    attestations_per_leaf  = {b:[inverse_attestations[x] for x in attested_blocks_per_leaf[b]] for b in leaves_with_attestations}
    attestations_per_leaf  = {b:[node for nodes in n for node in nodes] for b,n in attestations_per_leaf.items()}

    sum_attestations_per_leaf = {b:sum([simple_attestation_evaluation(n) for n in attestations_per_leaf[b]]) for b in leaves_with_attestations}
    return max(sum_attestations_per_leaf, key=sum_attestations_per_leaf.get)



def blockchain_to_digraph(blockchain):
    leaves = find_leaves_of_blockchain(blockchain)

    d = {}
    for l in leaves:
        b=l
        while b:
            d[b]={b.parent}
            b = b.parent
            if b in d.keys():
                break

    return nx.from_dict_of_dicts(d, create_using=nx.DiGraph)


    


    
                    
                

     
