# Entropy — A Terminal Cosmology

A terminal simulation that runs the universe forward (and backward) through discrete microstates, making the abstract viscerally observable. Not a game — an **instrument**. Like something you'd find running on a terminal at Los Alamos in 1962.

## The Strange Angle

The second law of thermodynamics is arguably the most philosophically loaded law in physics. It's the only fundamental law that distinguishes past from future. Everything else in physics is time-reversible. Entropy is what makes time *real*. That's the hook.

## Core Modules

### 1. The Box

A particle grid simulation where you watch an ordered system (all particles in one corner) dissolve into equilibrium. Run it backward and watch the absurdity — the "past hypothesis" made visible. The user controls the number of particles, dimensions, and can toggle between macro/micro views.

### 2. Maxwell's Demon

An interactive module where the user *becomes* the demon, manually sorting fast/slow particles between chambers. Track the information cost of each decision. Show that the user's brain is generating more entropy than they're reduced — the demon always loses. This is the Landauer's principle section.

### 3. The Arrow of Time

Show two animations side by side. One forward, one reversed. At low entropy differences, the user genuinely cannot tell which is "real." As entropy gradients increase, the arrow becomes obvious. A visceral demonstration of why we remember the past but not the future.

### 4. Heat Death Terminal

A long-running mode where the simulation runs cosmological timescales. Stars form, burn, die. Black holes evaporate. The last photons red-shift into nothing. The terminal slowly dims. Text gets sparser. Eventually — nothing. Just a cursor blinking in void. The whole thing takes maybe 5 minutes but it should feel like watching the end of everything.

### 5. Boltzmann Brain

After heat death, let it run. At some absurd timescale counter, a fluctuation occurs. A momentary structure appears in the noise. Was it conscious? The simulation doesn't answer. It just shows you the fluctuation and moves on.

## Design Philosophy

- **No color.** Monochrome. Unicode block characters and braille patterns for particle rendering. It should look like classified output.
- **Minimal UI.** Keyboard-driven. Module selection via a simple menu at launch.
- **Mathematically honest.** Real statistical mechanics underneath. Boltzmann entropy `S = k_B ln Ω`, actual microstate counting, proper energy distributions.
- **Narration as commentary.** Sparse text annotations that appear like research notes. Feynman-style — clear, direct, slightly unsettling in their implications.

## Technical Stack

- Python with `curses` for terminal rendering
- NumPy for the statistical mechanics engine
- No external dependencies beyond that — it should run anywhere

## The Strange Part

The truly skunkworks move: embed an actual information-theoretic argument throughout. The simulation itself is increasing entropy in the user's machine. The CPU heats up. The electrons scatter. Show this. Calculate the entropic cost of running the simulation and display it. The tool for studying entropy *is itself subject to entropy*. The observer cannot escape the observation.

## Build Order

1. **The Box** — core particle engine and terminal renderer
2. **Arrow of Time** — forward/reverse comparison using the Box engine
3. **Maxwell's Demon** — interactive sorting mode
4. **Heat Death Terminal** — cosmological long-run mode
5. **Boltzmann Brain** — post-heat-death fluctuation epilogue
6. **Self-entropy** — meta-layer calculating the simulation's own entropic cost

## Project Structure

```
entropy.py              Entry point — shows menu or launches a module directly
core/
  engine.py             ParticleSystem — Newtonian mechanics, Boltzmann entropy
  renderer.py           BrailleCanvas + Renderer — curses, braille dots, block density
  narrator.py           Condition-triggered research note annotations
  menu.py               Module selection menu with ASCII art title
modules/
  box.py                Module 1: The Box
  arrow.py              Module 2: Arrow of Time
  demon.py              Module 3: Maxwell's Demon
  heatdeath.py          Module 4: Heat Death Terminal
  boltzmann.py          Module 5: Boltzmann Brain
  selfentropy.py        Module 6: Self-Entropy
tests/
  test_engine.py        Physics engine, renderer, and narrator tests
```

## Development

- **Run:** `make run` or `python3 entropy.py` to open the menu. `python3 entropy.py box` to launch a module directly.
- **Test:** `make test` or `python3 -m pytest tests/`
- **Dependencies:** Python 3.8+, NumPy. No others.
- **Style:** No color in output. Monochrome only. Unicode braille + block characters.
- **Physics:** All entropy calculations must use real Boltzmann counting `S = k_B ln(N!/∏n_i!)` via log-gamma. No approximations. Maxwell-Boltzmann velocity distributions. Elastic wall reflections.
- **Architecture:** `core/` for shared library (engine, renderer, narrator, menu), `modules/` for simulation modules. Each module is a single file with a `run(stdscr)` entry point registered in `entropy.py`.
