"""Build the learner and solved PM4Py workshop notebooks."""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import nbformat as nbf


ROOT = Path(__file__).resolve().parents[1]


def md(text: str):
    return nbf.v4.new_markdown_cell(dedent(text).strip())


def code(text: str, *, tags: list[str] | None = None):
    cell = nbf.v4.new_code_cell(dedent(text).strip())
    if tags:
        cell.metadata["tags"] = tags
    return cell


def exercise(learner: str, solution: str, solved: bool):
    return code(solution if solved else learner, tags=["exercise-solution" if solved else "exercise"])


def build_notebook(solved: bool):
    label = "Complete solutions" if solved else "Learner edition"
    cells = [
        md(
            f"""
            # Process Mining with Python and PM4Py
            ## A fictional investment-banking booking process — {label}

            **Duration:** 60 minutes &nbsp; | &nbsp; **Level:** Intermediate Python, new to process mining

            > **Fictional-data notice:** Every trade, counterparty, resource, and event in this workshop is synthetic.
            > An anomaly is a reason to investigate—not proof of error or misconduct.
            """
        ),
        md(
            """
            ## Learning objectives and agenda

            By the end, you will be able to:

            1. explain what process mining adds to ordinary reporting;
            2. recognize and prepare a case-based event log;
            3. discover and visualize control flow and performance with PM4Py;
            4. find suspicious cases with rare variants, duration, and conformance diagnostics.

            | Time | Topic |
            |---:|---|
            | 0–8 min | What process mining is |
            | 8–20 min | Load and prepare an event log |
            | 20–40 min | Discover and visualize the process |
            | 40–56 min | Find and explain outliers |
            | 56–60 min | Recap and next steps |
            """
        ),
        code(
            """
            from pathlib import Path
            import shutil
            import tempfile

            import matplotlib.pyplot as plt
            import networkx as nx
            import numpy as np
            import pandas as pd
            import pm4py
            from IPython.display import SVG, display

            pd.set_option("display.max_colwidth", 120)
            pd.set_option("display.max_columns", 20)

            CASE_ID = "case:concept:name"
            ACTIVITY = "concept:name"
            TIMESTAMP = "time:timestamp"

            print("PM4Py version:", pm4py.__version__)
            print("Graphviz dot available:", shutil.which("dot") is not None)
            """
        ),
        md(
            """
            # 1. What is process mining? (0–8 minutes)

            A business process is not just a flowchart: it is what cases actually did over time. **Process mining**
            reconstructs and measures that behavior from event data.

            Every useful event log needs three essential ideas:

            - **Case:** one process instance, such as one booking ID.
            - **Activity:** a step performed for the case, such as `Compliance Check`.
            - **Timestamp:** when that step occurred.

            Optional attributes—resource, desk, product, amount, or counterparty tier—help explain *why* behavior differs.

            The three common process-mining questions are:

            - **Discovery:** What process does the data reveal?
            - **Performance:** Where are delays, queues, or rework?
            - **Conformance:** Which cases deviate from expected behavior?

            Traditional BI usually aggregates rows into totals. Process mining retains the **sequence within each case**,
            which exposes loops, skipped controls, premature steps, and alternative paths.
            """
        ),
        md(
            """
            ### Quick check: which table is an event log?

            **A.** One row per desk with monthly trade count and average value.  
            **B.** One row per booking event with booking ID, activity, and timestamp.  
            **C.** One row per employee with team and job title.

            <details><summary>Reveal the answer</summary>

            **B.** It preserves the case, activity, and time needed to reconstruct each trace. A and C may enrich an
            analysis, but cannot reconstruct a process by themselves.
            </details>
            """
        ),
        md(
            """
            ### Scenario

            A fictional investment bank wants to understand its post-trade booking process. A normal booking may include:

            `Trade Captured → Validate Economics → Enrich Counterparty → Compliance Check → Credit Check →`
            `[Supervisor Approval for high-value trades] → Confirm Booking → Post to Ledger → Booking Complete`

            Some legitimate cases require one amendment and revalidation. We will inspect 120 historical baseline cases
            and 40 later monitoring cases.

            **Predict before coding:** Where would you expect rework, delays, or control failures to appear?
            """
        ),
        md(
            """
            # 2. Load and prepare the event log (8–20 minutes)

            The CSV deliberately contains no anomaly label. In real work, the point is to find behavior worth reviewing
            before an investigator confirms what happened.

            ### Your turn 1 — load and inspect

            Load the CSV, parse the timestamp column, and show the first five rows.
            """
        ),
        exercise(
            """
            DATA_PATH = Path("data/investment_banking_booking_log.csv")

            # TODO: load DATA_PATH with pandas.
            # Hint: use parse_dates=[TIMESTAMP].
            raw_log = None
            raw_log
            """,
            """
            DATA_PATH = Path("data/investment_banking_booking_log.csv")
            raw_log = pd.read_csv(DATA_PATH, parse_dates=[TIMESTAMP])
            raw_log.head()
            """,
            solved,
        ),
        md(
            """
            ### Data contract

            | Column | Meaning |
            |---|---|
            | `case:concept:name` | Booking/case identifier |
            | `concept:name` | Activity name |
            | `time:timestamp` | UTC event timestamp |
            | `org:resource` | Fictional person or system performing the event |
            | `booking_period` | `baseline` or `monitoring` cohort |
            | `desk`, `product`, `currency` | Trade dimensions |
            | `counterparty_tier`, `notional_usd` | Case context repeated on each event |

            ### Your turn 2 — validate the minimum event-log quality

            Calculate row count, case count, activity count, missing values in required columns, and whether timestamps
            increase within every case.
            """
        ),
        exercise(
            """
            required = [CASE_ID, ACTIVITY, TIMESTAMP]

            # TODO: populate this dictionary.
            quality = {
                "events": None,
                "cases": None,
                "activities": None,
                "missing_required_values": None,
                "all_cases_time_ordered": None,
            }
            pd.Series(quality, name="value")
            """,
            """
            required = [CASE_ID, ACTIVITY, TIMESTAMP]
            quality = {
                "events": len(raw_log),
                "cases": raw_log[CASE_ID].nunique(),
                "activities": raw_log[ACTIVITY].nunique(),
                "missing_required_values": int(raw_log[required].isna().sum().sum()),
                "all_cases_time_ordered": bool(
                    raw_log.groupby(CASE_ID)[TIMESTAMP].apply(lambda s: s.is_monotonic_increasing).all()
                ),
            }
            pd.Series(quality, name="value")
            """,
            solved,
        ),
        md(
            """
            PM4Py accepts a pandas DataFrame when the case, activity, and timestamp keys are supplied. Formatting makes
            the types and ordering explicit. We retain business attributes for later slicing and interpretation.
            """
        ),
        exercise(
            """
            # TODO: use pm4py.format_dataframe and sort by case and timestamp.
            log = None
            baseline = None
            monitoring = None
            """,
            """
            log = pm4py.format_dataframe(
                raw_log,
                case_id=CASE_ID,
                activity_key=ACTIVITY,
                timestamp_key=TIMESTAMP,
            ).sort_values([CASE_ID, TIMESTAMP], kind="stable")

            baseline = log.loc[log["booking_period"].eq("baseline")].copy()
            monitoring = log.loc[log["booking_period"].eq("monitoring")].copy()

            print("Baseline cases:", baseline[CASE_ID].nunique())
            print("Monitoring cases:", monitoring[CASE_ID].nunique())
            """,
            solved,
        ),
        md(
            """
            ### Your turn 3 — summarize cases and durations

            Build one row per case with start time, end time, event count, cohort, and duration in minutes. Then compare
            median duration by cohort.
            """
        ),
        exercise(
            """
            # TODO: group by CASE_ID and aggregate start/end/event count/cohort.
            case_summary = None
            """,
            """
            case_summary = (
                log.groupby(CASE_ID)
                .agg(
                    start_time=(TIMESTAMP, "min"),
                    end_time=(TIMESTAMP, "max"),
                    event_count=(ACTIVITY, "size"),
                    booking_period=("booking_period", "first"),
                )
                .reset_index()
            )
            case_summary["duration_minutes"] = (
                case_summary["end_time"] - case_summary["start_time"]
            ).dt.total_seconds() / 60

            display(case_summary.head())
            case_summary.groupby("booking_period")["duration_minutes"].agg(["count", "median", "max"])
            """,
            solved,
        ),
        md(
            """
            # 3. Discover and visualize the process (20–40 minutes)

            A **trace** is the ordered activity sequence of one case. A **variant** is a distinct trace shared by one or
            more cases. Variant frequency gives a compact view of the process's dominant and unusual routes.

            ### Your turn 4 — extract variants

            Create an activity tuple for every case, count the tuples, and display the ten most frequent variants.
            """
        ),
        exercise(
            """
            # TODO: create variant_by_case and variant_counts.
            variant_by_case = None
            variant_counts = None
            """,
            """
            variant_by_case = (
                log.sort_values([CASE_ID, TIMESTAMP])
                .groupby(CASE_ID)[ACTIVITY]
                .agg(tuple)
                .rename("variant")
            )
            variant_counts = variant_by_case.value_counts().rename_axis("variant").reset_index(name="case_count")
            variant_counts.head(10)
            """,
            solved,
        ),
        md(
            """
            **Interpretation prompt:** Is the most common route the only valid route? Which optional step or loop explains
            the main alternatives? A rare route is a useful signal, but rarity alone is not a control failure.

            A **Directly-Follows Graph (DFG)** counts adjacent activity pairs across cases. A frequency DFG shows what
            happens often; a performance DFG shows elapsed time between adjacent activities.
            """
        ),
        code(
            """
            def draw_dfg(dfg, start_activities, end_activities, title, performance=False, max_edges=18):
                \"\"\"Render through PM4Py/Graphviz when available, otherwise use a notebook-safe fallback.\"\"\"
                if shutil.which("dot"):
                    output = Path(tempfile.mkdtemp()) / "dfg.svg"
                    if performance:
                        pm4py.save_vis_performance_dfg(
                            dfg, start_activities, end_activities, str(output),
                            rankdir="LR", graph_title=title, max_num_edges=max_edges,
                        )
                    else:
                        pm4py.save_vis_dfg(
                            dfg, start_activities, end_activities, str(output),
                            rankdir="LR", graph_title=title, max_num_edges=max_edges,
                        )
                    display(SVG(filename=str(output)))
                    return

                def metric_value(value):
                    if isinstance(value, dict):
                        return float(value.get("mean", next(iter(value.values()))))
                    return float(value)

                strongest = sorted(
                    dfg.items(), key=lambda item: metric_value(item[1]), reverse=True
                )[:max_edges]
                graph = nx.DiGraph()
                for (source, target), value in strongest:
                    graph.add_edge(source, target, weight=metric_value(value))
                process_positions = {
                    "Trade Captured": (0, 0),
                    "Validate Economics": (2.5, 0),
                    "Amend Booking": (2.5, 2.8),
                    "Enrich Counterparty": (5, 0),
                    "Compliance Check": (7.5, 0),
                    "Manual Override": (8.8, 2.8),
                    "Credit Check": (10, 0),
                    "Supervisor Approval": (12.5, 2.8),
                    "Confirm Booking": (12.5, 0),
                    "Post to Ledger": (15, 0),
                    "Booking Complete": (17.5, 0),
                }
                positions = {
                    node: process_positions.get(node, (index * 2.5, -2.5))
                    for index, node in enumerate(graph.nodes)
                }
                display_labels = {
                    "Trade Captured": "Trade\\nCaptured",
                    "Validate Economics": "Validate\\nEconomics",
                    "Amend Booking": "Amend\\nBooking",
                    "Enrich Counterparty": "Enrich\\nCounterparty",
                    "Compliance Check": "Compliance\\nCheck",
                    "Manual Override": "Manual\\nOverride",
                    "Credit Check": "Credit\\nCheck",
                    "Supervisor Approval": "Supervisor\\nApproval",
                    "Confirm Booking": "Confirm\\nBooking",
                    "Post to Ledger": "Post to\\nLedger",
                    "Booking Complete": "Booking\\nComplete",
                }

                fig, ax = plt.subplots(figsize=(22, 9), dpi=110)
                nx.draw_networkx_edges(
                    graph, positions, ax=ax, edge_color="#64748b", width=1.8,
                    node_size=5200, arrowsize=24,
                    connectionstyle="arc3,rad=0.06",
                    min_source_margin=18, min_target_margin=18,
                )

                for node, (x, y) in positions.items():
                    if node in start_activities:
                        facecolor = "#dcfce7"
                    elif node in end_activities:
                        facecolor = "#fee2e2"
                    elif y > 0:
                        facecolor = "#fef3c7"
                    else:
                        facecolor = "#dbeafe"
                    ax.text(
                        x, y, display_labels.get(node, node),
                        ha="center", va="center", fontsize=10, fontweight="semibold",
                        bbox={
                            "boxstyle": "round,pad=0.65",
                            "facecolor": facecolor,
                            "edgecolor": "#475569",
                            "linewidth": 1.2,
                        },
                        zorder=3,
                    )

                labels = {
                    edge: (
                        f"{metric_value(value) / 60:.1f}m"
                        if performance else f"{int(metric_value(value))}"
                    )
                    for edge, value in strongest
                }
                nx.draw_networkx_edge_labels(
                    graph, positions, ax=ax, edge_labels=labels,
                    font_size=8.5, rotate=False, label_pos=0.5,
                    connectionstyle="arc3,rad=0.06",
                    bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.9, "pad": 0.2},
                )
                ax.set_xlim(-1.3, 18.8)
                ax.set_ylim(-1.5, 4.3)
                ax.set_title(title + " (NetworkX fallback)", fontsize=18, pad=20)
                ax.axis("off")
                fig.tight_layout(pad=2.5)
                plt.show()
            """
        ),
        md(
            """
            ### Your turn 5 — discover the frequency DFG

            Use `pm4py.discover_dfg` on the full log, then visualize it. Before running the cell, predict which edge will
            have the highest frequency.
            """
        ),
        exercise(
            """
            # TODO: discover dfg, start_activities, and end_activities with PM4Py.
            dfg = start_activities = end_activities = None
            # draw_dfg(dfg, start_activities, end_activities, "Booking process — frequency")
            """,
            """
            dfg, start_activities, end_activities = pm4py.discover_dfg(
                log,
                activity_key=ACTIVITY,
                timestamp_key=TIMESTAMP,
                case_id_key=CASE_ID,
            )
            draw_dfg(dfg, start_activities, end_activities, "Booking process — frequency")
            """,
            solved,
        ),
        md(
            """
            ### Your turn 6 — discover the performance DFG

            Repeat the discovery with `pm4py.discover_performance_dfg`. Edge labels are mean elapsed times. Which edge
            looks slow, and is it slow for every case or only a few?
            """
        ),
        exercise(
            """
            # TODO: discover and draw the performance DFG.
            performance_dfg = performance_starts = performance_ends = None
            """,
            """
            performance_dfg, performance_starts, performance_ends = pm4py.discover_performance_dfg(
                log,
                activity_key=ACTIVITY,
                timestamp_key=TIMESTAMP,
                case_id_key=CASE_ID,
            )
            draw_dfg(
                performance_dfg, performance_starts, performance_ends,
                "Booking process — mean elapsed time", performance=True,
            )
            """,
            solved,
        ),
        md(
            """
            A DFG is descriptive. For formal conformance diagnostics, we discover a Petri net from the known-clean
            baseline cohort using the **Inductive Miner**. The same discovery also produces a readable process tree.

            ### Your turn 7 — discover a reference model
            """
        ),
        exercise(
            """
            # TODO: discover a process tree and Petri net from baseline.
            process_tree = None
            net = initial_marking = final_marking = None
            """,
            """
            process_tree = pm4py.discover_process_tree_inductive(
                baseline, noise_threshold=0.0,
                activity_key=ACTIVITY, timestamp_key=TIMESTAMP, case_id_key=CASE_ID,
            )
            net, initial_marking, final_marking = pm4py.discover_petri_net_inductive(
                baseline, noise_threshold=0.0,
                activity_key=ACTIVITY, timestamp_key=TIMESTAMP, case_id_key=CASE_ID,
            )

            if shutil.which("dot"):
                tree_path = Path(tempfile.mkdtemp()) / "process_tree.svg"
                pm4py.save_vis_process_tree(process_tree, str(tree_path), rankdir="LR")
                display(SVG(filename=str(tree_path)))
            else:
                print("Discovered process tree (text view):")
                print(process_tree)
            """,
            solved,
        ),
        md(
            """
            # 4. Find outliers with three complementary signals (40–56 minutes)

            No single anomaly rule is sufficient:

            - **Rare variant:** good for unusual routes, but can flag legitimate rare work.
            - **Long duration:** good for delay, but misses fast control violations.
            - **Low conformance fitness:** good for unexpected order or activities, but may accept unusual repetitions if
              the reference model contains a loop.

            We will flag a monitoring case when **any** signal fires, then preserve the reasons for human review.

            ### Signal 1 — rare monitoring variants

            For this small teaching log, define rare as at most three monitoring cases. In production this threshold
            should be calibrated against volume, seasonality, and investigation capacity.
            """
        ),
        exercise(
            """
            # TODO: compute variant frequency in monitoring and flag frequency <= 3.
            monitoring_variants = None
            """,
            """
            monitoring_case_variants = (
                monitoring.sort_values([CASE_ID, TIMESTAMP])
                .groupby(CASE_ID)[ACTIVITY]
                .agg(tuple)
                .rename("variant")
            )
            monitoring_variant_frequency = monitoring_case_variants.value_counts()
            monitoring_variants = monitoring_case_variants.to_frame()
            monitoring_variants["variant_frequency"] = monitoring_variants["variant"].map(monitoring_variant_frequency)
            monitoring_variants["rare_variant"] = monitoring_variants["variant_frequency"].le(3)
            monitoring_variants.sort_values(["rare_variant", "variant_frequency"], ascending=[False, True]).head(10)
            """,
            solved,
        ),
        md(
            """
            ### Signal 2 — unusually long duration

            Learn a robust upper bound from baseline duration: `Q3 + 1.5 × IQR`. This avoids using planted labels and is
            less sensitive to a few large values than mean plus standard deviation.
            """
        ),
        exercise(
            """
            # TODO: calculate the baseline IQR threshold and flag monitoring durations above it.
            duration_upper_bound = None
            duration_signals = None
            """,
            """
            baseline_durations = case_summary.loc[
                case_summary["booking_period"].eq("baseline"), "duration_minutes"
            ]
            q1, q3 = baseline_durations.quantile([0.25, 0.75])
            iqr = q3 - q1
            duration_upper_bound = q3 + 1.5 * iqr

            duration_signals = case_summary.loc[
                case_summary["booking_period"].eq("monitoring"),
                [CASE_ID, "duration_minutes"],
            ].copy()
            duration_signals["duration_outlier"] = duration_signals["duration_minutes"].gt(duration_upper_bound)
            print(f"Baseline duration upper bound: {duration_upper_bound:.1f} minutes")
            duration_signals.sort_values("duration_minutes", ascending=False).head(10)
            """,
            solved,
        ),
        md(
            """
            ### Signal 3 — conformance fitness

            An alignment compares an observed trace with the reference Petri net. A fitness of `1.0` means the trace can
            be replayed perfectly. Lower fitness indicates moves present only in the log or only in the model.

            **Prediction:** Will an excessive number of repetitions always have low fitness when the model contains a loop?
            """
        ),
        exercise(
            """
            # TODO: align the monitoring EventLog to the reference Petri net.
            alignment_scores = None
            """,
            """
            monitoring_event_log = pm4py.convert_to_event_log(
                monitoring,
                case_id_key=CASE_ID,
            )
            alignment_results = pm4py.conformance_diagnostics_alignments(
                monitoring_event_log,
                net,
                initial_marking,
                final_marking,
                multi_processing=False,
                return_diagnostics_dataframe=False,
            )
            alignment_scores = pd.DataFrame(
                {
                    CASE_ID: [trace.attributes["concept:name"] for trace in monitoring_event_log],
                    "alignment_fitness": [result["fitness"] for result in alignment_results],
                    "alignment_cost": [result["cost"] for result in alignment_results],
                }
            )
            alignment_scores["conformance_outlier"] = alignment_scores["alignment_fitness"].lt(0.999999)
            alignment_scores.sort_values(["alignment_fitness", CASE_ID]).head(10)
            """,
            solved,
        ),
        md(
            """
            ### Your turn 8 — combine and rank the evidence

            Join the three case-level signals. Create a readable `anomaly_reasons` field and rank flagged cases by number
            of signals, then by lowest fitness and longest duration.
            """
        ),
        exercise(
            """
            # TODO: merge the three signal tables and build is_anomaly/anomaly_reasons.
            ranked_outliers = None
            """,
            """
            case_signals = (
                monitoring_variants.reset_index()
                .merge(duration_signals, on=CASE_ID, validate="one_to_one")
                .merge(alignment_scores, on=CASE_ID, validate="one_to_one")
            )

            signal_columns = ["rare_variant", "duration_outlier", "conformance_outlier"]
            case_signals["signal_count"] = case_signals[signal_columns].sum(axis=1)
            case_signals["is_anomaly"] = case_signals["signal_count"].gt(0)

            def reasons(row):
                labels = []
                if row["rare_variant"]:
                    labels.append("rare variant")
                if row["duration_outlier"]:
                    labels.append("long duration")
                if row["conformance_outlier"]:
                    labels.append("low conformance")
                return ", ".join(labels) if labels else "none"

            case_signals["anomaly_reasons"] = case_signals.apply(reasons, axis=1)
            ranked_outliers = case_signals.loc[case_signals["is_anomaly"]].sort_values(
                ["signal_count", "alignment_fitness", "duration_minutes"],
                ascending=[False, True, False],
            )
            ranked_outliers[
                [CASE_ID, "variant_frequency", "duration_minutes", "alignment_fitness",
                 "signal_count", "anomaly_reasons"]
            ].head(20)
            """,
            solved,
        ),
        md(
            """
            ### Investigate before judging

            Pick two flagged booking IDs and inspect their ordered traces. Explain in plain business language what looks
            unusual. Then inspect one unflagged case as a comparison.
            """
        ),
        exercise(
            """
            # TODO: choose case IDs and print their ordered activity/timestamp/resource history.
            cases_to_review = []
            log.loc[log[CASE_ID].isin(cases_to_review), [CASE_ID, ACTIVITY, TIMESTAMP, "org:resource"]]
            """,
            """
            cases_to_review = ranked_outliers[CASE_ID].head(2).tolist()
            normal_comparison = case_signals.loc[~case_signals["is_anomaly"], CASE_ID].head(1).tolist()
            cases_to_review += normal_comparison
            log.loc[
                log[CASE_ID].isin(cases_to_review),
                [CASE_ID, ACTIVITY, TIMESTAMP, "org:resource"],
            ].sort_values([CASE_ID, TIMESTAMP])
            """,
            solved,
        ),
        md(
            """
            ### Validate against planted truth

            During real investigations, ground truth comes from source records and domain experts. For this synthetic
            lesson only, the instructor answer key lets us measure precision, recall, and coverage by anomaly type.
            """
        ),
        exercise(
            """
            # The learner edition intentionally does not load or expose the planted labels.
            # After ranking cases, compare your explanations with the instructor or solved notebook.
            """,
            """
            answer_key = pd.read_csv(Path("data/instructor_outlier_answer_key.csv"))
            detected_ids = set(case_signals.loc[case_signals["is_anomaly"], CASE_ID])
            truth_ids = set(answer_key[CASE_ID])

            true_positives = len(detected_ids & truth_ids)
            false_positives = len(detected_ids - truth_ids)
            false_negatives = len(truth_ids - detected_ids)
            precision = true_positives / len(detected_ids) if detected_ids else 0.0
            recall = true_positives / len(truth_ids) if truth_ids else 0.0

            evaluation = pd.Series(
                {
                    "true_positives": true_positives,
                    "false_positives": false_positives,
                    "false_negatives": false_negatives,
                    "precision": precision,
                    "recall": recall,
                },
                name="result",
            )
            display(evaluation)

            coverage = answer_key.assign(
                detected=answer_key[CASE_ID].isin(detected_ids)
            ).groupby("planted_anomaly")["detected"].agg(["sum", "count", "all"])
            display(coverage)

            answer_key.merge(
                case_signals[[CASE_ID, "anomaly_reasons", "duration_minutes", "alignment_fitness"]],
                on=CASE_ID,
                how="left",
            ).sort_values(["planted_anomaly", CASE_ID])
            """,
            solved,
        ),
        md(
            """
            # 5. Recap and next steps (56–60 minutes)

            The reusable workflow is:

            1. **Frame the case and event semantics.** Bad identifiers or timestamps produce misleading models.
            2. **Explore variants and performance.** Understand dominant paths before labeling deviations.
            3. **Discover a reference model from trustworthy behavior.** Avoid training blindly on known incidents.
            4. **Combine signals.** Rarity, time, and conformance reveal different failure modes.
            5. **Investigate with context.** Thresholds prioritize work; they do not replace business judgment.

            **Exit question:** Which signal found something the other two could miss, and what false positive could it create?

            Optional extensions:

            - compare desks, products, counterparties, or resources;
            - use PM4Py temporal profiles for activity-to-activity timing deviations;
            - monitor model fitness over time for process drift;
            - export XES and connect findings to a case-management workflow.
            """
        ),
    ]

    notebook = nbf.v4.new_notebook(cells=cells)
    notebook.metadata["kernelspec"] = {
        "display_name": "Python 3",
        "language": "python",
        "name": "python3",
    }
    notebook.metadata["language_info"] = {"name": "python", "version": "3.13"}
    return notebook


def main() -> None:
    outputs = {
        "process_mining_workshop.ipynb": build_notebook(solved=False),
        "process_mining_workshop_solutions.ipynb": build_notebook(solved=True),
    }
    for filename, notebook in outputs.items():
        path = ROOT / filename
        nbf.write(notebook, path)
        print(f"Wrote {path}")


if __name__ == "__main__":
    main()
