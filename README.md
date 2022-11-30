# EthereumPOS

## Install required libraries
Tested. on `python 3.9.2`.
The instructions will assume you are using a terminal, and a Unix-like OS.

Clone locally the repository and move in the cloned directory:
```
git clone https://github.com/benckj/EthereumPOS
cd EthereumPOS
```
Install a virtual environment to manage the python modules for the project.
We are going to cal our virtual environment `eth-env`:
```
python3 -m venv eth-env
```
Activate the virtual environment and install the required modules:
```
source eth-env/bin/activate
pip3 install requirements.txt
```
p.s. 

If the `pip3` command listed before doesnt work, you can install the modules 
listed in `requirements.txt` one by one.

You should be now ready to run the model!

## Running the model with pyspg
`pyspg` is a python module to run experiments in parallel over a large range of parameters.
The syntax to run an experiment:
```
python3 ethereum_abm.py --repeat=5 --workers=32 main.spg
```
- `--repeat=5` is setting the number of repetitions for each set of parameters to 5,
- `--workers=32` is setting 32 threads to work in parallel
- `main.spg` is the `.spg` with the actual parameters range in use for the experiment

Three files are needed in order for this command to work:
- `ethereum_abm.py` which is a wrapper to run the model trought pyspg
- `ethereum_abm.input` which is a file which records the inputs parameters for the model and their default value
- `ethereum_abm.stdout` which is a file which records the expected outputs
- `main.spg` wherech actually defines the "experiment": it assigns the parameters ranges, using pyspg sintax(see [pyspg wiki](https://github.com/tessonec/PySPG/wiki/Tutorial%3A-A-crash-course))

## Results intepretation
The output of the command in the previous section is a csv file,
named `main.csv`. 

For exanple, if we run the command:
```
python3 ethereum_abm.py --repeat=2 --workers=32 main.spg
```
with a `main.spg` like:
```
@execute ethereum_abm.py
:network_topology ER
:simulation_time 2e2
.no_neighs 3
.no_nodes 64
+tau_block 11 12 .5
+tau_attestation 11 12 0.5
```
we would obtain a `main.csv` looking something like this
```
no_neighs,no_nodes,tau_block,tau_attestation,Xi
3,64,11.0,11.0,0.4444444444444444
3,64,11.0,11.5,0.4444444444444444
3,64,11.0,12.0,0.4444444444444444
3,64,11.5,11.0,0.3888888888888889
3,64,11.5,11.5,0.5555555555555556
3,64,11.5,12.0,0.4444444444444444
3,64,12.0,11.0,0.3888888888888889
3,64,12.0,11.5,0.3888888888888889
3,64,12.0,12.0,0.4444444444444444
3,64,11.0,11.0,0.5
3,64,11.0,11.5,0.4444444444444444
3,64,11.0,12.0,0.4444444444444444
3,64,11.5,11.0,0.4444444444444444
3,64,11.5,11.5,0.4444444444444444
3,64,11.5,12.0,0.4444444444444444
3,64,12.0,11.0,0.3333333333333333
3,64,12.0,11.5,0.4444444444444444
3,64,12.0,12.0,0.3888888888888889
...
```
`no_neighs`,`no_nodes`,`tau_block`,`tau_attestation` are all parameters: 

- some are fixed value, like `no_neighs` and `no_nodes`, meaning they stay the same in all repetitions.
    In the `main.spg` file only one value is assigned to these parameters.
- some others change, like `tau_block` and `tau_attestations`, where you can observe the second change from the first to the second line for example.
    In the `main.spg` file they are both assigned `11 12 .5`, meaning start from 11 and arrive to 12 increasing 0.5 everytime.

`Xi` is an output result: is a function computed on the final result of the simulation for a specific set of parameters(defined on the same row).
In the specific `Xi` is the ratio of blocks in the mainchain over the total blocks produced in the simulation.

## Visualization
Using `pyspg` we can hastly generate plots to get an idea of the experiments results at a first glance.
Continuing with the experiment parameters we set in the previous section, the command to plot is:
```
spg-plotter.py --mean main.spg
```
In this case you are plotting the averages (on all repetitions) for a fixed set of parameters.
`spg-plotter` has options you may explore by running `spg-plotter.py --help`.

## Experiments folder
This folder contains some pre-defined experiments to help you understand how the repository works.
In order to obtain the resulta from the previous section you just need to move into the folder `experiments` and run the appropriate command:
```
cd experiments
python3 ../ethereum_abm.py --repeat=2 --workers=32 tutorial.spg
```
`tutorial.spg` is the `.spg` file containing the input parameters definitions used in previous section.
This is also a good method to check everything works smoothly.
In a similar fashion, `tutorial_plot_no_neighs_no_nodes.pdf` is the plot resulting on the visualization section, obtained by running
```
cd experiments
spg-plotter.py --mean tutorial.spg
```
The result look like this:
![Tutorial results plot](experiments/tutorial_plot_no_neighs_no_nodes.pdf)

## TODO for future extensions
- simulate reorg attacks [add reference]
- simulate balance attacks [add reference]
- improve and finish `visualizations.py`
