"""Plot function
"""
import numpy as np
import pandas as pd
from util import mpl, plt, latex_label


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
    parser.add_option("--x", action='store', dest="x", type='str',
                      default=None, help="x axis var")
    parser.add_option("--y", action='store', dest="y", type='str',
                      default=None, help="y axis var")
    parser.add_option("--z", action='store', dest="z", type='str',
                      default=None, help="z axis var for colormap")
    parser.add_option("--mode", action='store', dest="mode", type='str',
                      default='mean', help="aggregate statistics of the data")
    opts, args = parser.parse_args()
    if opts.output_path == None:
        opts.output_path = f'{opts.input_path.replace(".csv","")}_plot_{opts.x}_{opts.y}_{opts.z}.pdf'
    return opts, args


def plot_xyz_gradient(
        to_plot,
        x_label,
        y_label,
        z_label,
        output_path
        ):
    """Plot x vs y with different lines for each z,
    using a gradient colormap for z.
    """
    fig, ax = plt.subplots()
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
    norm = mpl.colors.Normalize(vmin=0, vmax=10)
    color_map = mpl.cm.ScalarMappable(norm=norm, cmap=cmap)
    # plot
    for color_value in to_plot.keys():
        ax.plot(
                to_plot[color_value][x_label],
                to_plot[color_value][y_label],
                c=color_map.to_rgba(color_value),
                marker='x',
                alpha=0.8
                )
    ax.set_xlabel(latex_label[x_label])
    ax.set_ylabel(latex_label[y_label])
    # colorbar
    fig.colorbar(
            color_map,
            ticks=range(len(to_plot)),
            orientation='vertical',
            label=latex_label[z_label]
            )

    plt.savefig(output_path)


if __name__ == "__main__":
    options, arguments = parse_command_line()
    with open(options.input_path, 'r', encoding='utf-8') as csv_file:
        df = pd.read_csv(csv_file)

    to_plot = {}
    to_plot_aggregate = {}
    for z_value in np.unique(df[options.z]):
        to_plot_aggregate[z_value] = {
                options.x: df.loc[df[options.z] == z_value][options.x],
                options.y: df.loc[df[options.z] == z_value][options.y]
                }
        x_list = []
        y_list = []
        for x_value in np.unique(to_plot_aggregate[z_value][options.x]):
            x_list.append(x_value)
            y_list.append(df.loc[(df[options.z] == z_value) & (df[options.x] == x_value)][options.y].mean())
        to_plot[z_value] = {
                options.x: x_list,
                options.y: y_list
                }

    # debug
    # print(to_plot[0.5])

    plot_xyz_gradient(
            to_plot,
            options.x,
            options.y,
            options.z,
            options.output_path
            )
