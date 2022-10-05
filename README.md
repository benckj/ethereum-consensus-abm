# EthereumPOS

## running pyspg example
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
