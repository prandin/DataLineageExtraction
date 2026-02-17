import pandas as pd
import copy
import re

def intersession_merger_cf(df: pd.DataFrame) -> pd.DataFrame:

    if df.empty:
        return df.copy()

    # -----------------------------
    # Helper: detect max hop index
    # -----------------------------
    def _get_max_hop(row):
        pattern = r"CF_SRC_SCHEMA_TABLE_COLUMN_(\d+)"
        indices = []
        for col in row.index:
            match = re.match(pattern, col)
            if match and pd.notna(row[col]):
                indices.append(int(match.group(1)))
        return max(indices) if indices else 0

    # -----------------------------
    # Parse row into structured form
    # -----------------------------
    def _parse_row(row, row_id):

        max_hop = _get_max_hop(row)

        hops = []
        for i in range(1, max_hop + 1):
            transformation = row.get(f"CF_SRC_TGT_TRANSFORMATION_{i}")
            source_col = row.get(f"CF_SRC_SCHEMA_TABLE_COLUMN_{i}")

            if pd.notna(source_col):
                hops.append({
                    "transformation": transformation,
                    "source_column": source_col
                })

        return {
            "id": row_id,
            "data": {
                "base": {
                    "CF_FINAL_ATTRIBUTE": row.get("CF_FINAL_ATTRIBUTE"),
                    "CF_ACTUAL_SOURCE": row.get("CF_ACTUAL_SOURCE"),
                    "CF_SET_CODE": row.get("CF_SET_CODE")
                },
                "root_target": row.get("CF_TGT_SCHEMA_TABLE_COLUMN_1"),
                "hops": hops
            }
        }

    # -----------------------------
    # Reconstruct DataFrame
    # -----------------------------
    def _reconstruct_df(records):

        if not records:
            return pd.DataFrame()

        max_hops = max(len(r["data"]["hops"]) for r in records)

        flat_rows = []

        for rec in records:
            row = {}

            base = rec["data"]["base"]
            row.update(base)

            row["CF_TGT_SCHEMA_TABLE_COLUMN_1"] = rec["data"]["root_target"]

            for i, hop in enumerate(rec["data"]["hops"], start=1):
                row[f"CF_SRC_TGT_TRANSFORMATION_{i}"] = hop["transformation"]
                row[f"CF_SRC_SCHEMA_TABLE_COLUMN_{i}"] = hop["source_column"]

            flat_rows.append(row)

        df_out = pd.DataFrame(flat_rows)

        # ensure column order
        ordered_cols = [
            "CF_FINAL_ATTRIBUTE",
            "CF_ACTUAL_SOURCE",
            "CF_SET_CODE",
            "CF_TGT_SCHEMA_TABLE_COLUMN_1"
        ]

        for i in range(1, max_hops + 1):
            ordered_cols.append(f"CF_SRC_TGT_TRANSFORMATION_{i}")
            ordered_cols.append(f"CF_SRC_SCHEMA_TABLE_COLUMN_{i}")

        return df_out.reindex(columns=ordered_cols)

    # -----------------------------
    # Initial parsing
    # -----------------------------
    records = [_parse_row(row, i) for i, row in df.iterrows()]

    # -----------------------------
    # Iterative merge loop
    # -----------------------------
    while True:

        possible_merges = []

        final_map = {}
        for rec in records:
            final_attr = rec["data"]["base"]["CF_FINAL_ATTRIBUTE"]
            final_map.setdefault(final_attr, []).append(rec)

        for downstream in records:
            source = downstream["data"]["base"]["CF_ACTUAL_SOURCE"]
            upstreams = final_map.get(source, [])

            for upstream in upstreams:
                if upstream["id"] != downstream["id"]:
                    possible_merges.append({
                        "up": upstream,
                        "down": downstream
                    })

        if not possible_merges:
            break

        consumed_ids = set()
        new_records = []

        for merge in possible_merges:

            up = merge["up"]
            down = merge["down"]

            consumed_ids.add(up["id"])
            consumed_ids.add(down["id"])

            new_base = {
                "CF_FINAL_ATTRIBUTE": down["data"]["base"]["CF_FINAL_ATTRIBUTE"],
                "CF_ACTUAL_SOURCE": up["data"]["base"]["CF_ACTUAL_SOURCE"],
                "CF_SET_CODE": up["data"]["base"]["CF_SET_CODE"]
            }

            # Core logic:
            # Keep downstream root_target
            new_root = down["data"]["root_target"]

            # Append hops: [B][A]
            new_hops = (
                copy.deepcopy(down["data"]["hops"])
                + copy.deepcopy(up["data"]["hops"])
            )

            new_records.append({
                "id": f"merged_{up['id']}_{down['id']}",
                "data": {
                    "base": new_base,
                    "root_target": new_root,
                    "hops": new_hops
                }
            })

        survivors = [r for r in records if r["id"] not in consumed_ids]
        records = survivors + new_records

    return _reconstruct_df(records)
