#!/bin/bash
#SBATCH --job-name=bd
#SBATCH --gres=gpu:1
python scripts/run_hoomd.py
