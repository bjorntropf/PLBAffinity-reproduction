class DFCompare:
    def __init__(self, df1, df2):
        self.df1 = df1
        self.df2 = df2

    def print_report(self, name, ignore_rows=None, verbose=False):
        missing_orig, missing_repr = self.missing_rows()
        print(
            f"Missing {name} rows in #1:",
            f"[{len(missing_orig)}]",
            ",".join(missing_orig),
        )
        print(
            f"Missing {name} rows in #2:",
            f"[{len(missing_repr)}]",
            ",".join(missing_repr),
        )

        diff_rows, diff_values = self.different_values(
            ignore_rows=ignore_rows, verbose=verbose
        )
        print(f"Different {name} rows:", f"[{diff_rows}]")
        print(f"Different {name} values:", f"[{diff_values}]")

    def missing_rows(self):
        miss1 = self.df2.index[~self.df2.index.isin(self.df1.index)].tolist()
        miss2 = self.df1.index[~self.df1.index.isin(self.df2.index)].tolist()

        return (list(map(str, miss1)), (list(map(str, miss2))))

    def different_values(self, ignore_rows=None, tolerance=0.1, verbose=False):
        if not ignore_rows:
            ignore_rows = []

        different_rows = 0
        different_values = 0

        combined_indices = set(self.df1.index).union(set(self.df2.index))
        for idx in combined_indices:
            if not (idx in self.df1.index and idx in self.df2.index):
                continue

            row_df1 = self.df1.loc[idx]
            row_df2 = self.df2.loc[idx]

            different_columns = []
            for col in self.df1.columns:
                if col not in row_df1:
                    continue

                if col in ignore_rows:
                    continue

                value_df1 = row_df1[col]
                value_df2 = row_df2[col]

                if value_df1 == 0 and value_df2 == 0:
                    continue

                relative_diff = abs(value_df1 - value_df2) / max(
                    abs(value_df1), abs(value_df2)
                )

                if relative_diff > tolerance:
                    different_columns.append(col)

            if not different_columns:
                continue

            different_rows += 1
            different_values += len(different_columns)

            if verbose:
                differences = []
                for col in different_columns:
                    differences.append(f"[{col}]{row_df1[col]}={row_df2[col]}")
                print(f"{idx} ({len(differences)}) {','.join(differences)}")

        return (different_rows, different_values)
