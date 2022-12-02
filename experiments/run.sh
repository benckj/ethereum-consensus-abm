# ER, 300s tau_block 0.5/10, tau_attest 0.5/10
python3 ../ethereum_abm.py --repeat=20 --workers=32 a.spg
# UNIFORM, 300s tau_block 0.5/10, tau_attest 0.5/10
python3 ../ethereum_abm.py --repeat=20 --workers=32 b.spg
# BA, 300s tau_block 0.5/10, tau_attest 0.5/10
python3 ../ethereum_abm.py --repeat=20 --workers=32 c.spg
