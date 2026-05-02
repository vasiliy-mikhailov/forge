# Forge-level capabilities

In TOGAF terms, *capability* (what forge can do) and *organization
unit* (who does it) are independent. Forge has several business
capabilities; they are realised partially by every lab (application
component in Phase C), and some labs lean heavily on one.

| Capability                                   | Quality dimension                                                                                                     |
|----------------------------------------------|-----------------------------------------------------------------------------------------------------------------------|
| **Research & Development**                   | Architect-velocity (capability advances per architect-hour); falsifiability (every change has IF-THEN-BECAUSE); reproducibility (replay from `Dockerfile + raw` only) |
| **Service operation (production framework)** | Stability (mean-time-to-crash); throughput; cost-per-output-token                                                    |
| **Product delivery to consumers**            | Branch hygiene; verify-by-artifact (not by agent); canonical-branch promotion                                        |
| **Architecture knowledge management**        | TOGAF-style doc threading; single source of truth (AGENTS.md per location); trajectory model with delete-on-promotion (see [`../../phase-preliminary/architecture-method.md`](../../phase-preliminary/architecture-method.md)) |

These capabilities are not products. They are forge's repeatable
abilities. Each is realised partially by every lab; some labs lean
heavily on one.

Per-capability detail (quality-dimension trajectories Level 1 →
Level 2) lives in:

- [`service-operation.md`](service-operation.md) — current detail.
- (R&D, Product delivery, Architecture knowledge mgmt — populate
  when their next trajectory step is opened in Phase F.)


## Measurable motivation chain
Per [P7](../../phase-preliminary/architecture-principles.md):

- **Driver**: ArchiMate Strategy layer requires top-level
  Capabilities to anchor lower-level Functions; without them,
  Phase B Roles have nowhere to point.
- **Goal**: Quality (KR: pre_prod_share ≥ 0.95).
- **Outcome**: 4 forge-level Capabilities (R&D, Service
  operation, Product delivery, Architecture knowledge
  management) realised by per-product Capabilities.
- **Measurement source**: runner-aggregate: test-auditor-runner, test-wiki-pm-runner, test-developer-runner, test-devops-runner, test-source-author-runner, test-concept-curator-runner, test-lab-AGENTS-runner (12-unit aggregate per audit AU-11 table)
- **Contribution**: runner-aggregate of realising-Role runners — Capability health = mean of role pass rates; contributes to Quality KR via aggregated pre-prod bug-catch.
- **Capability realised**: meta — this file IS the catalog.
- **Function**: Define-forge-level-Capabilities.
- **Element**: this file.
