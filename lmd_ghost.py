
# '''
# FUNCTIONS
# '''
# '''
# LMD Ghost following functions handle LMD Ghost Evaluation of Blocks
# '''

# def find_leaves_of_blockchain(blockchain):
#     parent_blocks = {b.parent for b in blockchain}
#     return blockchain - parent_blocks

# def lmd_ghost(blockchain, attestations, eval = simple_attestation_evaluation):
#     #identify leaf blocks
#     leaves = find_leaves_of_blockchain(blockchain)
#     if len(leaves)==1:
#         return leaves.pop()
#     #invert attestations: from node:block to block:[nodes]
#     inverse_attestations= {}
#     for n, b in attestations.items():
#         inverse_attestations[b] = inverse_attestations.get(b, []) + [n]

#     attested_blocks = set(inverse_attestations.keys())

#     lowest_attestation = next(iter(attested_blocks))
#     for b in attested_blocks:
#         if b.height < lowest_attestation.height:
#             lowest_attestation = b

#     cut_trees_per_leave = {b:b.predecessors - lowest_attestation.predecessors for b in leaves}
#     attested_blocks = set(inverse_attestations.keys())
#     attested_blocks_per_leave = {b: cut_trees_per_leave[b] & attested_blocks for b in leaves}
#     attestations_per_leave = {b:[inverse_attestations[x] for x in attested_blocks_per_leave[b]] for b in leaves}

#     sum_attestations_per_leave = {b:sum([eval(n) for n in attestations_per_leave[b]])}
#     return max(sum_attestations_per_leave, key=attestations_per_leave.get)


# def simple_attestation_evaluation(n):
#     return 1

# def stake_attestation_evaluation(n):
#     pass

# def blockchain_to_digraph(blockchain):
#     leaves = find_leaves_of_blockchain(blockchain)

#     d = {}
#     for l in leaves:
#         b=l
#         while b:
#             d[b]={b.parent}
#             b = b.parent
#             if b in d.keys():
#                 break

#     return nx.from_dict_of_dicts(d, create_using=nx.DiGraph)

# # def blockchain_layout(blockchain_digraph):
# #     #get max height
# #     #get start block
# #     #add to left for each height
# #     for b in blockchain_digraph.nodes()