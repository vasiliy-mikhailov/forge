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
