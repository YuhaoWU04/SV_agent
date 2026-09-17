# Architecture map maintenance

`data_lineage.json` is the editable source of truth for the human-facing system map.
It describes stages, fields, transformations, external queries, model-controlled
steps, schema checks, failure behavior, and implementation locations.

Do not edit `docs/system_flow.html` or `docs/field_dictionary.md` directly. Regenerate
them after a change to an agent, prompt, tool, schema, configuration value, or field:

```powershell
py sv_investigator/scripts/generate_flow_diagram.py
```

Check that the manifest is internally consistent and generated files are current:

```powershell
py sv_investigator/scripts/generate_flow_diagram.py --check
```

The check covers:

- unique stage, field, and transformation IDs;
- valid stage and field references;
- a producer for every non-input field;
- documented ADK state keys still present in `agent.py`;
- generated HTML and field dictionary matching the manifest and implementation
  fingerprint.

When changing the implementation:

1. Update code, prompts, and schemas.
2. Update affected fields and transformations in `data_lineage.json`.
3. Regenerate both documentation files.
4. Run `--check` and the unit tests.

Processing kinds used in the map:

- `deterministic`: fixed Python validation or calculation;
- `external-query`: an actual external API request;
- `model-controlled`: model organization constrained by a prompt;
- `model-structured`: model output constrained by a Pydantic schema;
- `schema-validation`: deterministic structured-output validation.
