#!/usr/bin/env python3
"""Find where an FSC curve crosses 0.143 and convert that crossing to a resolution.

The curve is FSC(x) = 1 / (1 + exp((x - center) / steepness)), with x in 1/Angstrom.
Solving FSC(x) = 0.143 gives x = center + steepness * ln(1/0.143 - 1).
"""
import argparse
import math

FSC_THRESHOLD = 0.143


def crossing(center, steepness, threshold=FSC_THRESHOLD):
    return center + steepness * math.log(1.0 / threshold - 1.0)


def main():
    parser = argparse.ArgumentParser(
        description="Print the FSC=0.143 crossing (1/A) and the resolution (A) of an FSC curve."
    )
    parser.add_argument("--center", type=float, required=True,
                        help="spatial frequency (1/A) where FSC = 0.5")
    parser.add_argument("--steepness", type=float, required=True,
                        help="width parameter of the logistic curve (1/A), must be positive")
    args = parser.parse_args()

    if args.steepness <= 0:
        parser.error("--steepness must be positive")

    x = crossing(args.center, args.steepness)
    if x <= 0:
        parser.error("the crossing is not at a positive spatial frequency")

    print(f"FSC=0.143 crossing: {x:.4f} 1/A")
    print(f"Resolution: {1.0 / x:.2f} A")


if __name__ == "__main__":
    main()
