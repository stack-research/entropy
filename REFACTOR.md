# Refactor Notes

## Findings

### High

#### Collision handling fires after overlap, not on approach

Status: completed on 2026-03-18

Implemented:

- Switched collision detection to use each pair's swept motion over the timestep.
- Added a regression test that requires a head-on pair to collide on the first overlap step.
- Verified with `python3 -m pytest -q` after the change.

In [core/engine.py](/Users/macos-user/.projects/stack-research/entropy/core/engine.py#L136), the collision resolver treats `proj > 0` as "approaching", but for `dp = pos[i] - pos[j]` and `dv = vel[i] - vel[j]`, a positive dot product means the pair is separating. The current logic therefore misses the actual impact step and resolves only after particles have already overlapped and started moving apart.

Observed reproduction:

- Particle A at `x=500`, Particle B at `x=503`
- Velocities `+2` and `-1`
- First step: both land at `x=502` with no collision response
- Second step: velocities swap after they have already crossed

This undermines the "real physics" claim and affects modules that rely on collisions, especially Maxwell's Demon and Heat Death.

#### Maxwell's Demon wall allows tunneling when gate is closed

In [modules/demon.py](/Users/macos-user/.projects/stack-research/entropy/modules/demon.py#L128), the internal wall only reflects particles if the post-step position still lies within `wall_x +/- 2`. Fast particles can step from one side of the divider to the other in a single frame and never satisfy that condition.

Observed reproduction:

- Closed gate
- Particle at `wall_x - 1`
- Velocity `vx = +5`
- After one step the particle ends on the right side with unchanged velocity

In repeated randomized checks, leakage occurred in 8 of 200 first-step runs. That breaks the core mechanic of the module.

### Medium

#### Arrow of Time does not actually run one system backward

The module description says one simulation runs forward from low entropy and one runs backward from high entropy, but the implementation creates one low-entropy system and one equilibrium system and steps both forward.

Relevant code:

- [modules/arrow.py](/Users/macos-user/.projects/stack-research/entropy/modules/arrow.py#L63)
- [modules/arrow.py](/Users/macos-user/.projects/stack-research/entropy/modules/arrow.py#L103)

On reveal, the equilibrium system is labeled "backward" in [modules/arrow.py](/Users/macos-user/.projects/stack-research/entropy/modules/arrow.py#L124), but no reversed dynamics are used. The presentation currently overstates what the simulation is doing.

#### `entropy_max()` is not the exact combinatorial maximum

In [core/engine.py](/Users/macos-user/.projects/stack-research/entropy/core/engine.py#L176), `entropy_max()` rounds `N / M` and computes:

`lgamma(N + 1) - M * lgamma(round(N / M) + 1)`

That is only exact when `N` is divisible by the number of cells. The docs explicitly promise exact Boltzmann counting, so the normalization should use the true maximizing occupancy: distribute the remainder across `r` cells and compute the exact multinomial count.

Example with `N = 200`, `M = 64`:

- Current code: `748.56`
- Exact combinatorial maximum: `737.47`

Because `S/Smax` is displayed throughout the UI, this skews a core user-facing metric.

#### Heat Death crashes on very small terminals

`StarField._populate()` in [modules/heatdeath.py](/Users/macos-user/.projects/stack-research/entropy/modules/heatdeath.py#L70) uses `random.randint(3, self.cols - 4)` and similar ranges without guarding tiny terminal sizes. Small dimensions such as `(1, 1)`, `(2, 4)`, and `(3, 6)` raise `ValueError`.

That conflicts with the project expectation that it should run broadly in terminal environments.

## Test Gaps

- The current suite passes: `python3 -m pytest -q` reported `24 passed`.
- The tests do not cover collision timing correctness.
- [tests/test_engine.py](/Users/macos-user/.projects/stack-research/entropy/tests/test_engine.py#L133) checks momentum conservation for a two-particle setup, but that still passes even when the collision is resolved a step late.
- There are no tests for the Demon wall tunneling case.
- There are no tests verifying that Arrow of Time actually uses reversed dynamics.
- There are no tests validating the exact `entropy_max()` normalization against the multinomial optimum.
- There are no robustness tests for tiny terminal sizes in Heat Death.

## Overall

The repo structure and module separation are good, and the code is readable. The main issue is that several modules currently claim stronger physical fidelity than the implementation delivers. The next refactor pass should prioritize physics correctness and module-behavior alignment before aesthetic or content expansion.
