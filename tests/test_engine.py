"""Tests for the physics engine."""

import sys
import os
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.engine import ParticleSystem


class TestParticleSystem:

    def test_init_corner(self):
        s = ParticleSystem(100, (160, 88), 'corner')
        assert s.n == 100
        assert s.pos.shape == (100, 2)
        assert s.vel.shape == (100, 2)
        # All particles should be in top-left quadrant
        assert s.pos[:, 0].max() <= 160 * 0.25
        assert s.pos[:, 1].max() <= 88 * 0.25

    def test_init_uniform(self):
        s = ParticleSystem(500, (160, 88), 'uniform')
        # With 500 particles, should span most of the box
        assert s.pos[:, 0].max() > 80
        assert s.pos[:, 1].max() > 44

    def test_init_half(self):
        s = ParticleSystem(100, (160, 88), 'half')
        assert s.pos[:, 0].max() <= 80

    def test_step_moves_particles(self):
        s = ParticleSystem(50, (160, 88), 'center')
        pos_before = s.pos.copy()
        s.step()
        assert not np.array_equal(pos_before, s.pos)

    def test_wall_reflection_keeps_particles_in_bounds(self):
        s = ParticleSystem(200, (160, 88), 'corner')
        for _ in range(500):
            s.step()
        assert s.pos[:, 0].min() >= 0
        assert s.pos[:, 0].max() < 160
        assert s.pos[:, 1].min() >= 0
        assert s.pos[:, 1].max() < 88

    def test_time_reversal(self):
        s = ParticleSystem(50, (160, 88), 'corner')
        # Record initial state
        pos_initial = s.pos.copy()
        vel_initial = s.vel.copy()

        # Run forward 100 steps
        for _ in range(100):
            s.step()

        # Reverse
        s.reverse()
        assert s.time_direction == -1

        # Run forward (effectively backward) 100 steps
        for _ in range(100):
            s.step()

        # Should return close to initial state (float precision)
        np.testing.assert_allclose(s.pos, pos_initial, atol=1e-6)

    def test_entropy_increases_from_corner(self):
        s = ParticleSystem(200, (160, 88), 'corner')
        e_initial, _ = s.entropy()
        for _ in range(200):
            s.step()
        e_after, _ = s.entropy()
        assert e_after > e_initial

    def test_entropy_normalized_range(self):
        s = ParticleSystem(200, (160, 88), 'corner')
        norm = s.entropy_normalized()
        assert 0.0 <= norm <= 1.0

    def test_entropy_uniform_is_high(self):
        s = ParticleSystem(500, (160, 88), 'uniform')
        norm = s.entropy_normalized()
        assert norm > 0.7

    def test_temperature_positive(self):
        s = ParticleSystem(100, (160, 88), 'corner')
        assert s.measured_temperature() > 0

    def test_kinetic_energy_conserved(self):
        s = ParticleSystem(100, (160, 88), 'corner')
        ke_initial = s.kinetic_energy()
        for _ in range(500):
            s.step()
        ke_after = s.kinetic_energy()
        np.testing.assert_allclose(ke_initial, ke_after, rtol=1e-10)

    def test_add_particles(self):
        s = ParticleSystem(100, (160, 88), 'corner')
        s.add_particles(25)
        assert s.n == 125
        assert s.pos.shape == (125, 2)

    def test_remove_particles(self):
        s = ParticleSystem(100, (160, 88), 'corner')
        s.remove_particles(20)
        assert s.n == 80

    def test_remove_particles_floor(self):
        s = ParticleSystem(5, (160, 88), 'corner')
        s.remove_particles(100)
        assert s.n >= 1

    def test_particle_positions_integer(self):
        s = ParticleSystem(50, (160, 88), 'corner')
        pp = s.particle_positions()
        assert pp.dtype in (np.int32, np.int64)
        assert pp[:, 0].min() >= 0
        assert pp[:, 0].max() < 160


class TestCollisions:

    def test_collisions_conserve_kinetic_energy(self):
        s = ParticleSystem(100, (160, 88), 'uniform', collisions=True, collision_radius=4.0)
        ke_initial = s.kinetic_energy()
        for _ in range(500):
            s.step()
        ke_after = s.kinetic_energy()
        np.testing.assert_allclose(ke_initial, ke_after, rtol=1e-6)

    def test_collisions_conserve_momentum(self):
        s = ParticleSystem(100, (160, 88), 'uniform', collisions=True, collision_radius=4.0)
        # Momentum changes with wall reflections, so test a single collision step
        # by placing two particles about to collide with no walls nearby
        s2 = ParticleSystem(2, (1000, 1000), 'uniform', collisions=True, collision_radius=5.0)
        s2.pos[0] = [500, 500]
        s2.pos[1] = [503, 500]
        s2.vel[0] = [2.0, 0.0]
        s2.vel[1] = [-1.0, 0.0]
        p_before = s2.vel.sum(axis=0).copy()
        s2.step()
        p_after = s2.vel.sum(axis=0)
        np.testing.assert_allclose(p_before, p_after, atol=1e-10)

    def test_collisions_thermalize_speeds(self):
        """With collisions, a bimodal speed distribution should thermalize."""
        s = ParticleSystem(200, (200, 200), 'uniform', collisions=True, collision_radius=4.0)
        # Give half the particles high speed, half low
        s.vel[:100] *= 3.0
        s.vel[100:] *= 0.3
        speeds_before = np.sqrt((s.vel ** 2).sum(axis=1))
        std_before = np.std(speeds_before)

        for _ in range(2000):
            s.step()

        speeds_after = np.sqrt((s.vel ** 2).sum(axis=1))
        std_after = np.std(speeds_after)
        # Distribution should become more uniform (lower relative spread)
        # Not a strict test since it's statistical, but with 200 particles
        # and 2000 steps the effect is strong
        assert std_after < std_before

    def test_particles_stay_in_bounds_with_collisions(self):
        s = ParticleSystem(200, (160, 88), 'corner', collisions=True, collision_radius=3.0)
        for _ in range(500):
            s.step()
        assert s.pos[:, 0].min() >= 0
        assert s.pos[:, 0].max() < 160
        assert s.pos[:, 1].min() >= 0
        assert s.pos[:, 1].max() < 88

    def test_no_collisions_when_disabled(self):
        """Without collisions, particles with different speeds never exchange energy."""
        s = ParticleSystem(50, (200, 200), 'uniform', collisions=False)
        speeds_before = np.sort(np.sqrt((s.vel ** 2).sum(axis=1)))
        for _ in range(500):
            s.step()
        speeds_after = np.sort(np.sqrt((s.vel ** 2).sum(axis=1)))
        np.testing.assert_allclose(speeds_before, speeds_after, rtol=1e-10)


class TestBrailleCanvas:

    def test_pixel_mapping(self):
        from core.renderer import BrailleCanvas, BRAILLE_MAP
        c = BrailleCanvas(10, 5)
        assert c.pixel_width == 20
        assert c.pixel_height == 20

        c.set_pixel(0, 0)
        assert c.buffer[0, 0] == BRAILLE_MAP[0][0]

        c.clear()
        c.set_pixel(1, 3)
        assert c.buffer[0, 0] == BRAILLE_MAP[3][1]

    def test_out_of_bounds_ignored(self):
        from core.renderer import BrailleCanvas
        c = BrailleCanvas(10, 5)
        c.set_pixel(-1, -1)
        c.set_pixel(999, 999)
        assert c.buffer.sum() == 0


class TestNarrator:

    def test_narrator_fires(self):
        from core.narrator import make_box_narrator
        n = make_box_narrator()
        # Trigger the equilibrium message
        for _ in range(5):
            n.update({'entropy_norm': 0.95, 'time_dir': 1})
        text = n.current_text()
        assert text is not None

    def test_narrator_fires_once(self):
        from core.narrator import make_box_narrator
        n = make_box_narrator()
        n.update({'entropy_norm': 0.55, 'time_dir': 1})
        first = n.current_text()
        # Exhaust TTL
        for _ in range(200):
            n.update({'entropy_norm': 0.55, 'time_dir': 1})
        # First rule should not re-fire
        n.update({'entropy_norm': 0.55, 'time_dir': 1})
        assert n.current_text() is None or n.current_text() != first
