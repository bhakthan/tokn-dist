# Task: list the items below their reorder level

The repository root for this run is the `workspace` folder, so every path
below is relative to it.

1. Read `inventory.csv`. It has three columns: `item`, `qty` and
   `reorder_level`. Each row after the header describes one item.
2. An item needs reordering when its `qty` is strictly less than its
   `reorder_level`. When the two numbers are equal, the item does not need
   reordering.
3. Create `reorder.md`. It must contain a markdown table with exactly these
   columns, in this order: `item`, `qty`, `reorder_level`.
4. Put one row per item that needs reordering. Keep the rows in the same order
   as they appear in `inventory.csv`.
5. Do not add any other text, notes, items or columns to `reorder.md`.

Use file reading and file writing only. Do not write or run scripts.

When the file is written, reply with one line: DONE.
