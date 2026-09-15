"""Google ADK workflow for evidence-grounded SV investigation.

ADK discovers ``root_agent`` from :mod:`sv_investigator.agent`. Keeping package
initialization side-effect free also lets deterministic tools be tested without
requiring an API key or importing the full agent runtime.
"""
