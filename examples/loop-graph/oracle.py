"""Held-out grading oracle for the Graph of Loops example (Python standard library only).

Fits a polynomial of the degree named in model.json to the TRAINING (x, y) CSV by
ordinary least squares, then reports the mean-squared error (MSE) of that fitted
model on the EVALUATION CSV. Two output modes:

  --emit exit (default): print one line; exit 0 if MSE <= --max-mse, else 1.
  --emit json          : print {"dimensions", "gates", "metadata"} and exit 0.
                         Pass/fail is in the gate, not the exit code.

Fitting always uses --train and scoring always uses --eval, so a held-out check
scores the training-fitted model on data it never saw. It never refits on the
held-out set.
"""

import argparse
import csv
import json
import math
import sys


def read_xy(path):
    xs, ys = [], []
    with open(path, encoding="utf-8") as fh:
        for line_no, row in enumerate(csv.reader(fh), start=1):
            cells = [c.strip() for c in row if c.strip() != ""]
            if not cells or cells[0].startswith("#"):
                continue
            if len(cells) < 2:
                raise ValueError(f"{path}:{line_no}: expected 'x,y', got {row!r}")
            try:
                x, y = float(cells[0]), float(cells[1])
            except ValueError:
                if line_no == 1:
                    continue  # header row
                raise ValueError(f"{path}:{line_no}: non-numeric row {row!r}")
            xs.append(x)
            ys.append(y)
    return xs, ys


def mean_std(xs):
    mean = sum(xs) / len(xs)
    var = sum((x - mean) ** 2 for x in xs) / len(xs)
    std = math.sqrt(var)
    if std < 1e-12:
        std = 1.0
    return mean, std


def solve(a, b):
    """Solve A x = b by Gaussian elimination with partial pivoting."""
    n = len(b)
    for col in range(n):
        piv = max(range(col, n), key=lambda r: abs(a[r][col]))
        if abs(a[piv][col]) < 1e-15:
            raise ValueError("singular normal-equations matrix (degree too high for the data)")
        a[col], a[piv] = a[piv], a[col]
        b[col], b[piv] = b[piv], b[col]
        for r in range(col + 1, n):
            f = a[r][col] / a[col][col]
            for c in range(col, n):
                a[r][c] -= f * a[col][c]
            b[r] -= f * b[col]
    x = [0.0] * n
    for i in range(n - 1, -1, -1):
        s = b[i] - sum(a[i][j] * x[j] for j in range(i + 1, n))
        x[i] = s / a[i][i]
    return x


def polyfit(xs, ys, degree):
    """Least-squares coefficients [c0 .. c_degree] via the normal equations."""
    m = degree + 1
    a = [[0.0] * m for _ in range(m)]
    b = [0.0] * m
    for x, y in zip(xs, ys):
        powers = [1.0]
        for _ in range(2 * degree):
            powers.append(powers[-1] * x)
        for i in range(m):
            for j in range(m):
                a[i][j] += powers[i + j]
            b[i] += powers[i] * y
    return solve(a, b)


def polyval(coeffs, x):
    v = 0.0
    for c in reversed(coeffs):
        v = v * x + c
    return v


def evaluate(train_path, eval_path, model_path):
    with open(model_path, encoding="utf-8") as fh:
        degree = int(json.load(fh)["degree"])
    if degree < 0:
        raise ValueError(f"degree must be >= 0, got {degree}")
    tr_x, tr_y = read_xy(train_path)
    if not tr_x:
        raise ValueError(f"training set {train_path!r} has no rows")
    ev_x, ev_y = read_xy(eval_path)
    if not ev_x:
        raise ValueError(f"evaluation set {eval_path!r} has no rows")

    # Standardize x by the TRAINING mean/std. The same transform is used at scoring time.
    mean, std = mean_std(tr_x)
    coeffs = polyfit([(x - mean) / std for x in tr_x], tr_y, degree)
    sse = sum((polyval(coeffs, (x - mean) / std) - y) ** 2 for x, y in zip(ev_x, ev_y))
    return sse / len(ev_x), degree, len(ev_x)


def main(argv=None):
    p = argparse.ArgumentParser(description="Held-out polynomial-fit grading oracle.")
    p.add_argument("--model", required=True, help="path to model.json ({\"degree\": N})")
    p.add_argument("--train", help="TRAINING x,y CSV (the model is fitted on this)")
    p.add_argument("--eval", help="EVALUATION x,y CSV (defaults to --train)")
    p.add_argument("--data", help="alias used for --train and --eval when they are unset")
    p.add_argument("--max-mse", type=float, default=0.10, help="MSE threshold for the gate")
    p.add_argument("--gate", default="fits", help="gate name reported in --emit json mode")
    p.add_argument("--emit", choices=["exit", "json"], default="exit")
    args = p.parse_args(argv)

    train = args.train or args.data
    if not train:
        p.error("--train (or --data) is required")
    evaluation = args.eval or train

    try:
        mse, degree, n = evaluate(train, evaluation, args.model)
    except (OSError, ValueError, KeyError) as exc:
        # Fail closed: a broken oracle must never look like a passing gate.
        if args.emit == "json":
            out = {
                "dimensions": {"error": 1},
                "gates": {args.gate: False},
                "metadata": {"error": str(exc)},
            }
            print(json.dumps(out, sort_keys=True))
        else:
            print(f"oracle: {exc}", file=sys.stderr)
        return 2

    passed = mse <= args.max_mse
    if args.emit == "json":
        out = {
            "dimensions": {"mse": round(mse, 6), "degree": float(degree), "n": float(n)},
            "gates": {args.gate: passed},
            "metadata": {"max_mse": args.max_mse},
        }
        print(json.dumps(out, sort_keys=True))
        return 0

    print(f"degree={degree} n={n} mse={mse:.6f} max_mse={args.max_mse:.6f} pass={str(passed).lower()}")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
