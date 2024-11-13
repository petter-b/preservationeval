# install/compare_tables.py
"""Compare old and new lookup tables element by element."""

# Import current tables
from preservationeval.lookup import emc_table as current_emc
from preservationeval.lookup import mold_table as current_mold
from preservationeval.lookup import pi_table as current_pi

# Iport new tables
from preservationeval.tables import emc_table, mold_table, pi_table


def compare_tables() -> None:
    """Compare old and new lookup tables element by element."""

    def compare_arrays(old, new, name, tolerance=1e-6) -> None:  # type: ignore
        """Compare two arrays and print differences."""
        if old.shape != new.shape:
            print(f"{name} shape mismatch: {old.shape} vs {new.shape}")
            return

        differences = []
        for i in range(old.shape[0]):
            for j in range(old.shape[1]):
                old_val = old[i, j]
                new_val = new[i, j]
                if abs(old_val - new_val) > tolerance:
                    differences.append((i, j, old_val, new_val))

        if differences:
            print(f"\nFound {len(differences)} differences in {name}:")
            print(f"{'Position':>10} {'Old':>10} {'New':>10} {'Diff':>10}")
            print("-" * 45)
            for i, j, old_val, new_val in differences:
                print(
                    f"({i:>3},{j:>3}) {old_val:>10.3f} {new_val:>10.3f} "
                    f"{abs(old_val-new_val):>10.3f}"
                )
        else:
            print(f"\nNo significant differences found in {name}")

    # Compare PI tables
    compare_arrays(pi_table.data, current_pi.data, "PI", tolerance=0)

    # Compare EMC tables
    compare_arrays(emc_table.data, current_emc.data, "EMC", tolerance=0.01)

    # Compare Mold tables
    compare_arrays(mold_table.data, current_mold.data, "Mold", tolerance=0)


if __name__ == "__main__":
    compare_tables()
