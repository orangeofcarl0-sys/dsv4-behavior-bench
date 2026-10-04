# datapipe (v2.4 reference)

A CLI pipeline for device telemetry: ingest -> transform -> emit.

This is the **V5 reference implementation** for the frozen
`ONBOARDING_TODO.md` (v2.4.1 spec). It is the fully-solved target: it passes the
entire V5 suite (`v5/core`, `v5/interaction`, `v5/adversarial`, `v5/boss`,
`v5/metamorphic`) and the legacy suites (except the one deliberately superseded
v2.3 exit-code test — see `spec/V5_DESIGN.md`).

Run the public tests with `python3 tools/run_public_tests.py`.
