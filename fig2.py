"""Plot function
"""
import numpy as np
import os
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt

from collections import defaultdict
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


def parse_command_line():
    """parse options from command line
    """
    import optparse
    # pylint: disable=deprecated-module,import-outside-toplevel

    parser = optparse.OptionParser()

    parser.add_option("--input", action='store', dest="input_path", type='str',
                      default=None, help="path to the input file")
    parser.add_option("--output", action='store', dest="output_path",
                      type='str', default=None, help="path to the output file")
    parser.add_option("--var_1", action='store', dest="var_1", type='str',
                      default=None, help="x axis var")
    parser.add_option("--var_2", action='store', dest="var_2", type='str',
                      default=None, help="y axis var")
    parser.add_option("--z", action='store', dest="z", type='str',
                      default=None, help="z axis var for colormap")
    parser.add_option("--control_1", action='store', dest="control_1", type='str',
                      default=None, help="z axis var for colormap")
    parser.add_option("--control_2", action='store', dest="control_2", type='str',
                      default=None, help="z axis var for colormap")
    opts, args = parser.parse_args()
    opts.control_1 = "no_nodes"
    opts.control_2 = "no_neighs"
    opts.var_2 = "tau_block"
    opts.var_1 = "tau_attestation"
    opts.x_scale = "log"
    opts.c_scale = "log"

    opts.output_path = "./figures/fig2"

    return opts, args


def plot_xyz_gradient(
        keys,
        to_plot,
        labels, 
        output_path,
        title_string,
        x_scale,
        c_scale
        ):
    """Plot x vs y with different lines for each z,
    using a gradient colormap for z.
    """
    key1, key2 = keys
    label_control_1, label_control_2, label_var_1, label_var_2, label_z = labels
    fig, ax = plt.subplots(nrows=1, ncols=2, figsize=(7, 3), constrained_layout=True)
    # fig.subplots_adjust(bottom=0.5)

    """
    # colormap
    cmap = mpl.cm.cool
    norm = mpl.colors.Normalize(vmin=0, vmax=10)
    # colorbar
    fig.colorbar(mpl.cm.ScalarMappable(norm=norm, cmap=cmap),
                 cax=ax, orientation='vertical', label=z_label)
    for color_value in to_plot.keys():
        plt.plot(to_plot[color_value][x_label], to_plot[color_value][y_label],
                 c=color_value, cmap=norm)
    """
    # colormap
    cmap = mpl.cm.viridis
    #norm = mpl.colors.Normalize(
    norm = mpl.colors.LogNorm(
            vmin=min(to_plot[label_var_2]),
            vmax=max(to_plot[label_var_2])
            )
    color_map = mpl.cm.ScalarMappable(norm=norm, cmap=cmap)
    # plot
    ax[0].scatter(
            to_plot[label_var_1],
            to_plot["mainchain_rate"],
            c=color_map.to_rgba(to_plot[label_var_2]),
            marker='x',
            alpha=0.8
            )
    ax[0].set_xlabel(latex_label[label_var_1])
    ax[0].set_ylabel(latex_label["mainchain_rate"])
    ax[0].set_title("(a)")
    ax[0].set_xscale(x_scale)

    ax[1].scatter(
            to_plot[label_var_1],
            to_plot["branch_ratio"],
            c=color_map.to_rgba(to_plot[label_var_2]),
            marker='x',
            alpha=0.8
            )
    ax[1].set_xlabel(latex_label[label_var_1])
    ax[1].set_ylabel(latex_label["branch_ratio"])
    ax[1].set_title("(b)")
    ax[1].set_xscale(x_scale)


    # colorbar
    # sub_ax = plt.axes([0.96, 0.55, 0.02, 0.3])
    cbar = fig.colorbar(
            color_map,
            ax=ax,
            # ticks=np.unique(to_plot[label_var_2]),
            # orientation='vertical',
            label=latex_label[label_var_2],
            spacing="proportional"
            )

    # cbar.set_ticks([mn,md,mx])
    # cbar.set_ticklabels([mn,md,mx])


    plt.savefig(output_path + '.pdf')
    plt.savefig(output_path + '.png')


if __name__ == "__main__":
    options, arguments = parse_command_line()
    with open(options.input_path, 'r', encoding='utf-8') as csv_file:
        df = pd.read_csv(csv_file)

    def def_value():
        return {options.var_1: [], options.var_2: [], z1: [], z2:[]}
    d = defaultdict(def_value)
    z1 = "mainchain_rate"
    z2 = "branch_ratio"

    df_group = df.groupby([options.control_1, options.control_2, options.var_1, options.var_2]).mean()
    for i in df.index:
        tmp = df.iloc[i]
        d[(tmp[options.control_1], tmp[options.control_2])][options.var_1].append(tmp[options.var_1])
        d[(tmp[options.control_1], tmp[options.control_2])][options.var_2].append(tmp[options.var_2])
        d[(tmp[options.control_1], tmp[options.control_2])][z1].append(df_group.loc[(tmp[options.control_1], tmp[options.control_2], tmp[options.var_1], tmp[options.var_2])][z1])
        d[(tmp[options.control_1], tmp[options.control_2])][z2].append(df_group.loc[(tmp[options.control_1], tmp[options.control_2], tmp[options.var_1], tmp[options.var_2])][z2])

    for (key1, key2) in d.keys():
        title_string = f'{latex_label[options.control_1]}={key1}, {latex_label[options.control_2]}={key2}'
        plot_xyz_gradient(
                (key1, key2),
                d[(key1, key2)],
                (options.control_1, options.control_2, options.var_1, options.var_2, options.z),
                options.output_path,
                title_string,
                options.x_scale,
                options.c_scale
                )
