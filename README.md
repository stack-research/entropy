# Entropy

A terminal simulation that runs the universe forward (and backward) through discrete microstates, making the abstract viscerally observable. Not a game — an instrument.

The second law of thermodynamics is the only fundamental law of physics that distinguishes past from future. Everything else is time-reversible. Entropy is what makes time real.

## Quick Start

```
pip install numpy
python3 entropy.py
```

Or with make:

```
make run
```

This opens the module selection menu. You can also launch a module directly:

```
python3 entropy.py box
```

## Modules

### 1. The Box

200 particles start packed in one corner. Watch them dissolve into equilibrium. Reverse time and watch the absurdity — the past hypothesis made visible.

Toggle between micro view (individual particles as braille dots) and macro view (coarse-grained density blocks). The transition itself is the lesson: statistical mechanics is about which description level you choose.

### 2. Arrow of Time

Two simulations side by side. One runs forward from low entropy, one runs backward from a higher-entropy prepared state. At low entropy differences, you genuinely cannot tell which is "real." As the gradient increases, the arrow becomes obvious.

A visceral demonstration of why we remember the past but not the future.

### 3. Maxwell's Demon

You become the demon, opening and closing a gate between two chambers to sort fast and slow particles. The simulation tracks the information cost of each decision. Landauer's principle in action — the demon always loses.

### 4. Heat Death

The universe dies in ~5 minutes. Stars form, burn, and gutter out. Black holes evaporate. Photons red-shift into nothing. The terminal slowly dims. Text gets sparser. Eventually — nothing. Just a cursor blinking in void.

### 5. Boltzmann Brain

After heat death, the simulation keeps running at absurd timescales. A thermal fluctuation produces a momentary structure in the noise. Was it conscious? The simulation doesn't answer.

### 6. Self-Entropy

The simulation measures its own thermodynamic cost. CPU time, operations, the Landauer bound on every bit erased. The tool for studying entropy is itself subject to entropy. The observer cannot escape the observation.

## Controls

### Menu

| Key | Action |
|-----|--------|
| `Up` / `Down` or `j` / `k` | Navigate |
| `ENTER` or `1`-`6` | Launch module |
| `q` | Quit |

### The Box

| Key | Action |
|-----|--------|
| `SPACE` | Pause / resume |
| `r` | Reverse time |
| `m` | Toggle macro / micro view |
| `+` / `-` | Add / remove particles |
| `?` | Help overlay |
| `q` | Back to menu |

### Arrow of Time

| Key | Action |
|-----|--------|
| `SPACE` | Reveal which direction is forward |
| `r` | Reset with new arrangement |
| `q` | Back to menu |

### Maxwell's Demon

| Key | Action |
|-----|--------|
| `SPACE` | Open / close the gate |
| `p` | Pause / resume |
| `r` | Reset |
| `q` | Back to menu |

### Heat Death / Boltzmann Brain / Self-Entropy

| Key | Action |
|-----|--------|
| `q` | Back to menu |

## Requirements

- Python 3.8+
- NumPy

No other dependencies. Runs anywhere with a terminal.

## Tests

```
make test
```

## Physics

Particles obey continuous Newtonian mechanics with elastic wall reflections. Velocities are drawn from the Maxwell-Boltzmann distribution. Time reversal is exact — pressing `r` flips the simulation's time direction, and the system retraces its trajectory. The second law is statistical, not dynamical.

Entropy is computed via Boltzmann counting on a coarse-grained 8x8 grid:

```
S = k_B * [ln(N!) - Σ ln(n_i!)]
```

where `n_i` is the particle count in cell `i`. Computed in log-space via `lgamma` for numerical stability.

## The Strange Part

The simulation itself is increasing entropy in your machine. The CPU heats up. The electrons scatter. The tool for studying entropy is itself subject to entropy. The observer cannot escape the observation.
