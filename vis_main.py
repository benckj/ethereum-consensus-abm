import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize

if __name__ == "__main__":
    df = pd.read_csv("./main.csv")
    df = df.iloc[:, 5: ]
    df = df.groupby(["tau_block","tau_attestation"]).mean().reset_index(level=-1).reset_index(level=-1)
    fig, ax = plt.subplots(1,3, figsize=(15,6))

    plt.Axes.set_xscale(ax[0], 'log' )
    plt.Axes.set_xscale(ax[1], 'log' )
    plt.Axes.set_xscale(ax[2], 'log' )

    cmap = plt.colormaps["viridis"]
    ax[0].set_title('mainchain_rate')
    ax[0].set_xlabel('tau_block')
    ax[0].set_ylabel('mainchain_rate') 
    ax[1].set_title('branch_ratio')
    ax[1].set_xlabel('tau_block')
    ax[1].set_ylabel('branch_ratio') 
    ax[2].set_title('blocktree_entropy')
    ax[2].set_xlabel('tau_block')
    ax[2].set_ylabel('blocktree_entropy') 


    for i in df.index: 
        ax[0].plot(df.loc[i, 'tau_block'], df.loc[i, 'mainchain_rate'],  's', color=cmap(df.loc[i, 'tau_attestation']) )
        ax[1].plot(df.loc[i, 'tau_block'], df.loc[i, 'branch_ratio'], 'x', color=cmap(df.loc[i, 'tau_attestation']))
        ax[2].plot(df.loc[i, 'tau_block'], df.loc[i, 'blocktree_entropy'], 'o', color=cmap(df.loc[i, 'tau_attestation']))

    plt.colorbar(plt.cm.ScalarMappable(norm=plt.Normalize(vmin=0.1, vmax=900),cmap=cmap),
                ax=ax, label="tau attestation")

    fig.savefig('tau_block.png')

    fig, ax = plt.subplots(1,3, figsize=(15,6))

    cmap = plt.colormaps["viridis"].resampled(20)
    ax[0].set_title('mainchain_rate')
    ax[0].set_xlabel('tau_attestation')
    ax[0].set_ylabel('mainchain_rate') 
    ax[1].set_title('branch_ratio')
    ax[1].set_xlabel('tau_attestation')
    ax[1].set_ylabel('branch_ratio') 
    ax[2].set_title('blocktree_entropy')
    ax[2].set_xlabel('tau_attestation')
    ax[2].set_ylabel('blocktree_entropy') 

    plt.Axes.set_xscale(ax[0], 'log' )
    plt.Axes.set_xscale(ax[1], 'log' )
    plt.Axes.set_xscale(ax[2], 'log' )

    for i in df.index: 
        ax[0].plot(df.loc[i, 'tau_attestation'], df.loc[i, 'mainchain_rate'], 'x', color=cmap(int(df.loc[i, 'tau_block']))  )
        ax[1].plot(df.loc[i, 'tau_attestation'], df.loc[i, 'branch_ratio'], 'x', color=cmap(int(df.loc[i, 'tau_block']))  )
        ax[2].plot(df.loc[i, 'tau_attestation'], df.loc[i, 'blocktree_entropy'], 'o', color=cmap(int(df.loc[i, 'tau_block']))  )

    plt.colorbar(plt.cm.ScalarMappable(norm=Normalize(1, 100), cmap=cmap),
                ax=ax, label="tau block")

    fig.savefig('tau_attestation.png')