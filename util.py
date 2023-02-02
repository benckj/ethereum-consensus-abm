"""Util objects to plot
"""
import matplotlib.pyplot as plt
import matplotlib as mpl
# module setup
plt.rcParams['text.usetex'] = True
# objects definition
latex_label = {
        'tau_block': r'$\tau_{block}$',
        'tau_attestation': r'$\tau_{attestation}$',
        'mainchain_rate': r'$\mu$',
        'branch_ratio': r'$F$',
        'blocktree_entropy': r'$S_{b}$',
        'no_nodes': r'$N$',
        'no_neighs': r'$\langle d \rangle$',
        }
