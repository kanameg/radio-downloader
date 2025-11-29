#!/usr/bin/env python3
"""
Simple HTML downloader (list output).

Usage:
    programs = parse_programs_from_html(html)
    if not programs:
        print("No program entries found in the page.", file=sys.stderr)
        sys.exit(1)

    # Merge with existing CSV named {target}.csv if present (merge key: hls_url)
    existing_fname = f"{target}.csv"

    # DataFrame from parsed programs
    new_df = pd.DataFrame(programs) if programs else pd.DataFrame(
        columns=["title", "broadcast_date", "broadcast_start", "hls_url", "get"]
    )

    # Read existing CSV if present, else create empty with standard columns
    if os.path.exists(existing_fname):
        try:
            existing_df = pd.read_csv(existing_fname, dtype=str)
        except Exception as err:
            print(
                f"Warning: failed to read existing CSV {existing_fname}: {err}",
                file=sys.stderr,
            )
            existing_df = pd.DataFrame(
                columns=["title", "broadcast_date", "broadcast_start", "hls_url", "get"]
            )
    else:
        existing_df = pd.DataFrame(
            columns=["title", "broadcast_date", "broadcast_start", "hls_url", "get"]
        )

    # Ensure union of columns
    for column_name in existing_df.columns.difference(new_df.columns):
        new_df[column_name] = ""
    for column_name in new_df.columns.difference(existing_df.columns):
        existing_df[column_name] = ""

    # Place existing first so its values take precedence when dropping duplicates
    combined = pd.concat([existing_df, new_df], ignore_index=True, sort=False)
    if "hls_url" in combined.columns:
        combined = combined.drop_duplicates(subset=["hls_url"], keep="first")

    # Normalize `get` column (use to_numeric to avoid FutureWarning about downcasting)
    if "get" in combined.columns:
        combined["get"] = (
            pd.to_numeric(combined["get"], errors="coerce").fillna(0).astype(int)
        )

    # Write CSV to output file if specified, otherwise write to stdout
    if args.output:
        out_fname = args.output
        try:
            combined.to_csv(out_fname, index=False, encoding="utf-8")
        except Exception as err:
            print(f"Error writing CSV to {out_fname}: {err}", file=sys.stderr)
            sys.exit(1)
    else:
        # print CSV to stdout
        try:
            combined.to_csv(sys.stdout, index=False)
        except Exception as err:
            print(f"Error writing CSV to stdout: {err}", file=sys.stderr)
            sys.exit(1)
    except Exception as err:
        print(f"Error downloading {url}: {err}", file=sys.stderr)
        sys.exit(1)

    programs = parse_programs_from_html(html)
    if not programs:
        print("No program entries found in the page.", file=sys.stderr)
        sys.exit(1)
<<<<<<< HEAD
    # Merge with existing file named {target}.csv if present (merge key: hls_url)
    existing_fname = f"{target}.csv"
    existing = []
    try:
        import csv as _csv

        with open(existing_fname, "r", encoding="utf-8", newline="") as ef:
            reader = _csv.DictReader(ef)
            for row in reader:
                hls = row.get("hls_url")
                if not hls:
                    continue
                entry = dict(row)
                if "get" in entry:
                    try:
                        entry["get"] = int(entry["get"]) if entry["get"] != "" else 0
                    except Exception:
                        # leave as-is if cannot convert
                        pass
                existing.append(entry)
    except FileNotFoundError:
        existing = []
    except Exception as e:
        print(
            f"Warning: failed to read existing CSV file {existing_fname}: {e}",
            file=sys.stderr,
=======
    # Merge with existing CSV named {target}.csv if present (merge key: hls_url)
    existing_fname = f"{target}.csv"

    # DataFrame from parsed programs
    new_df = (
        pd.DataFrame(programs)
        if programs
        else pd.DataFrame(
            columns=["title", "broadcast_date", "broadcast_start", "hls_url", "get"]
>>>>>>> feature/update-get-on-success
        )
    )

<<<<<<< HEAD
    existing_by_hls = {
        e.get("hls_url"): e
        for e in existing
        if isinstance(e, dict) and e.get("hls_url")
    }
    parsed_by_hls = {p.get("hls_url"): p for p in programs if p.get("hls_url")}

    merged = []
    # For each parsed program, prefer existing file's values when keys overlap
    for hls, p in parsed_by_hls.items():
        if hls in existing_by_hls:
            ex = existing_by_hls[hls]
            m = p.copy()
            m.update(ex)
            merged.append(m)
        else:
            merged.append(p)

    # Also include any existing entries that are not present in newly parsed list
    for hls, ex in existing_by_hls.items():
        if hls and hls not in parsed_by_hls:
            merged.append(ex)

    # Output merged CSV
    # Determine CSV columns: prefer core fields first, then any extras
    core_cols = ["title", "broadcast_date", "broadcast_start", "hls_url", "get"]
    extra_cols = []
    for entry in merged:
        for k in entry.keys():
            if k not in core_cols and k not in extra_cols:
                extra_cols.append(k)
    cols = core_cols + extra_cols

    import csv

    try:
        if args.output:
            out_f = open(args.output, "w", encoding="utf-8", newline="")
        else:
            out_f = sys.stdout

        writer = csv.writer(out_f)
        writer.writerow(cols)
        for e in merged:
            row = [e.get(c, "") for c in cols]
            writer.writerow(row)
    except Exception as e:
        print(f"Error writing CSV to {args.output or 'stdout'}: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        if args.output:
            out_f.close()
=======
    # Read existing CSV if present, else create empty with standard columns
    if os.path.exists(existing_fname):
        try:
            existing_df = pd.read_csv(existing_fname, dtype=str)
        except Exception as err:
            print(
                f"Warning: failed to read existing CSV {existing_fname}: {err}",
                file=sys.stderr,
            )
            existing_df = pd.DataFrame(
                columns=["title", "broadcast_date", "broadcast_start", "hls_url", "get"]
            )
    else:
        existing_df = pd.DataFrame(
            columns=["title", "broadcast_date", "broadcast_start", "hls_url", "get"]
        )

    # Ensure union of columns
    for column_name in existing_df.columns.difference(new_df.columns):
        new_df[column_name] = ""
    for column_name in new_df.columns.difference(existing_df.columns):
        existing_df[column_name] = ""

    # Place existing first so its values take precedence when dropping duplicates
    combined = pd.concat([existing_df, new_df], ignore_index=True, sort=False)
    if "hls_url" in combined.columns:
        combined = combined.drop_duplicates(subset=["hls_url"], keep="first")

    # Normalize `get` column (use to_numeric to avoid FutureWarning about downcasting)
    if "get" in combined.columns:
        combined["get"] = (
            pd.to_numeric(combined["get"], errors="coerce").fillna(0).astype(int)
        )

    # Write CSV to output file if specified, otherwise write to stdout
    if args.output:
        out_fname = args.output
        try:
            combined.to_csv(out_fname, index=False, encoding="utf-8")
        except Exception as err:
            print(f"Error writing CSV to {out_fname}: {err}", file=sys.stderr)
            sys.exit(1)
    else:
        # print CSV to stdout
        try:
            combined.to_csv(sys.stdout, index=False)
        except Exception as err:
            print(f"Error writing CSV to stdout: {err}", file=sys.stderr)
            sys.exit(1)
>>>>>>> feature/update-get-on-success


if __name__ == "__main__":
    main()
