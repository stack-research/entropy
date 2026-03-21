"""Tests for Heat Death rendering robustness."""

from core.engine import ParticleSystem
from modules.heatdeath import CosmologicalToyEngine, StarField


class TestStarField:

    def test_small_terminal_sizes_do_not_crash(self):
        for rows, cols in ((1, 1), (2, 4), (3, 6), (4, 7)):
            field = StarField(rows, cols)
            for obj in field.objects:
                assert 0 <= obj['x'] < cols
                assert 0 <= obj['y'] < rows


class TestCosmologicalToyEngine:

    def test_wraps_particle_system(self):
        eng = CosmologicalToyEngine(30, (80, 60))
        assert isinstance(eng.system, ParticleSystem)

    def test_evolve_applies_non_hamiltonian_steps(self):
        eng = CosmologicalToyEngine(100, (200, 200), temperature=2.0)
        ke0 = eng.system.kinetic_energy()
        for _ in range(50):
            eng.evolve_tick(10, 0.5, 0, [(0, 'x', 1.0)])
        assert eng.system.kinetic_energy() != ke0
