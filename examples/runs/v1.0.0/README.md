# SV Investigator v1.0.0 reference run

This directory is the checked-in end-to-end run for the six cases in
`tests/cases/manifest.json` using `gemini-3.5-flash` and SV Investigator v1.0.0.

Run command:

```powershell
sv-runner --run-dir examples/runs/v1.0.0 --case-timeout 900 --save-events summary
```

All six workflows completed and produced schema-valid reports. One report is marked
`complete`; five are intentionally marked `incomplete` because at least one external
source failed or returned incomplete coverage. `run_status=complete` means the workflow
finished, while `report_status` records scientific evidence completeness.

Start with `summary.json` for aggregate metrics. Each case directory contains the
exact model input, complete final state, structured report, human-readable `report.md`,
compact event log, and operational metrics. These outputs are research examples, not
clinical classifications; database contents and model responses may change on rerun.

The manifest records a resume because the first attempt exposed an ungrounded factual
claim that failed strict synthesis validation. v1.0.0 now drops such claims, records a
limitation, and continues the workflow; the six case artifacts here are from the
successful corrected rerun.
