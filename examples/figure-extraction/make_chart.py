"""Synthetic fixtures for the TOKN visual-perception examples (no real data)."""
import argparse, numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

ap = argparse.ArgumentParser()
ap.add_argument("--center", type=float, default=0.245, help="FSC midpoint, 1/A")
ap.add_argument("--steepness", type=float, default=0.025)
a = ap.parse_args()
s = np.linspace(0.0, 0.5, 400)
fsc = 1.0 / (1.0 + np.exp((s - a.center) / a.steepness))
fig, ax = plt.subplots(figsize=(8, 5), dpi=100)
ax.plot(s, fsc, color="#1f77b4", linewidth=2)
ax.axhline(0.143, color="#888888", linestyle="--", linewidth=1)
ax.set_xlim(0, 0.5); ax.set_ylim(0, 1.0)
ax.set_xlabel("Spatial frequency (1/A)"); ax.set_ylabel("FSC")
ax.set_title("Gold-standard FSC")
fig.tight_layout(); fig.savefig("fsc.png")
