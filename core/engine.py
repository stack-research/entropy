"""Statistical mechanics engine."""

import numpy as np
from math import lgamma, log, sqrt

# Natural units: k_B = 1, m = 1
K_B = 1.0


class ParticleSystem:
    """N particles in a 2D box with elastic walls and optional collisions.

    Continuous Newtonian mechanics — time-reversible by construction.
    Entropy computed via Boltzmann counting of coarse-grained microstates.
    """

    def __init__(self, n_particles, bounds, initial_config='corner', temperature=1.0,
                 collisions=False, collision_radius=3.0):
        self.n = n_particles
        self.width, self.height = bounds
        self.bounds = bounds
        self.dt = 1.0
        self.time_direction = 1
        self.temperature = temperature
        self.grid_shape = (8, 8)  # coarse-graining grid for entropy
        self.collisions = collisions
        self.collision_radius = collision_radius

        self._init_positions(initial_config)
        self._init_velocities()

    def _init_positions(self, config):
        if config == 'corner':
            # All particles in top-left quadrant
            self.pos = np.column_stack([
                np.random.uniform(0, self.width * 0.25, self.n),
                np.random.uniform(0, self.height * 0.25, self.n),
            ])
        elif config == 'center':
            cx, cy = self.width / 2, self.height / 2
            spread = min(self.width, self.height) * 0.1
            self.pos = np.column_stack([
                np.random.normal(cx, spread, self.n),
                np.random.normal(cy, spread, self.n),
            ])
            self.pos[:, 0] = np.clip(self.pos[:, 0], 0.1, self.width - 0.1)
            self.pos[:, 1] = np.clip(self.pos[:, 1], 0.1, self.height - 0.1)
        elif config == 'half':
            # Left half — for Maxwell's Demon
            self.pos = np.column_stack([
                np.random.uniform(0, self.width * 0.5, self.n),
                np.random.uniform(0, self.height, self.n),
            ])
        else:  # uniform
            self.pos = np.column_stack([
                np.random.uniform(0, self.width, self.n),
                np.random.uniform(0, self.height, self.n),
            ])

    def _init_velocities(self):
        # Maxwell-Boltzmann: v_i ~ Normal(0, sqrt(k_B * T / m))
        sigma = np.sqrt(K_B * self.temperature)
        self.vel = np.random.normal(0, sigma, (self.n, 2))

    def step(self):
        """Advance one timestep. Vectorized."""
        prev_pos = self.pos.copy()
        self.pos += self.vel * self.dt * self.time_direction
        self._reflect_walls()
        if self.collisions:
            self._resolve_collisions(prev_pos)

    def _reflect_walls(self):
        # X-axis reflection
        mask_lo = self.pos[:, 0] < 0
        self.pos[mask_lo, 0] = -self.pos[mask_lo, 0]
        self.vel[mask_lo, 0] = -self.vel[mask_lo, 0]

        mask_hi = self.pos[:, 0] >= self.width
        self.pos[mask_hi, 0] = 2 * self.width - self.pos[mask_hi, 0]
        self.vel[mask_hi, 0] = -self.vel[mask_hi, 0]

        # Y-axis reflection
        mask_lo = self.pos[:, 1] < 0
        self.pos[mask_lo, 1] = -self.pos[mask_lo, 1]
        self.vel[mask_lo, 1] = -self.vel[mask_lo, 1]

        mask_hi = self.pos[:, 1] >= self.height
        self.pos[mask_hi, 1] = 2 * self.height - self.pos[mask_hi, 1]
        self.vel[mask_hi, 1] = -self.vel[mask_hi, 1]

    def _resolve_collisions(self, prev_pos):
        """Resolve equal-mass collisions that occur during the last timestep.

        The detector uses each pair's swept relative motion over the timestep,
        so head-on impacts are handled when they occur instead of one frame late
        after particles have already crossed or perfectly overlapped.
        """
        r = self.collision_radius
        if r <= 0 or self.n < 2:
            return

        cell_size = max(r * 2.0, 1.0)
        r_sq = r * r
        eps = 1e-10
        displacements = self.pos - prev_pos
        grid = {}

        for i in range(self.n):
            min_x = min(prev_pos[i, 0], self.pos[i, 0]) - r
            max_x = max(prev_pos[i, 0], self.pos[i, 0]) + r
            min_y = min(prev_pos[i, 1], self.pos[i, 1]) - r
            max_y = max(prev_pos[i, 1], self.pos[i, 1]) + r

            x0 = int(np.floor(min_x / cell_size))
            x1 = int(np.floor(max_x / cell_size))
            y0 = int(np.floor(min_y / cell_size))
            y1 = int(np.floor(max_y / cell_size))

            for cx in range(x0, x1 + 1):
                for cy in range(y0, y1 + 1):
                    key = (cx, cy)
                    if key not in grid:
                        grid[key] = []
                    grid[key].append(i)

        checked = set()
        for particle_ids in grid.values():
            if len(particle_ids) < 2:
                continue

            for idx in range(len(particle_ids) - 1):
                i = particle_ids[idx]
                for jdx in range(idx + 1, len(particle_ids)):
                    j = particle_ids[jdx]
                    pair = (i, j) if i < j else (j, i)
                    if pair in checked:
                        continue
                    checked.add(pair)

                    i, j = pair
                    dp0 = prev_pos[i] - prev_pos[j]
                    dv_step = displacements[i] - displacements[j]

                    a = dv_step[0] * dv_step[0] + dv_step[1] * dv_step[1]
                    b = 2.0 * (dp0[0] * dv_step[0] + dp0[1] * dv_step[1])
                    c = dp0[0] * dp0[0] + dp0[1] * dp0[1] - r_sq

                    collided = c <= 0.0
                    t_collide = 0.0

                    if not collided and a > eps:
                        disc = b * b - 4.0 * a * c
                        if disc >= 0.0:
                            root = sqrt(disc)
                            t_first = (-b - root) / (2.0 * a)
                            if 0.0 <= t_first <= 1.0:
                                collided = True
                                t_collide = t_first

                    if not collided:
                        dp_end = self.pos[i] - self.pos[j]
                        dist_end_sq = dp_end[0] * dp_end[0] + dp_end[1] * dp_end[1]
                        if dist_end_sq < r_sq:
                            collided = True
                            t_collide = 1.0

                    if not collided:
                        continue

                    normal = dp0 + dv_step * t_collide
                    normal_sq = normal[0] * normal[0] + normal[1] * normal[1]
                    if normal_sq <= eps:
                        dp_end = self.pos[i] - self.pos[j]
                        normal = dp_end if np.dot(dp_end, dp_end) > eps else dp0
                        normal_sq = normal[0] * normal[0] + normal[1] * normal[1]
                        if normal_sq <= eps:
                            continue

                    rel_vel = self.vel[i] - self.vel[j]
                    proj = (rel_vel[0] * normal[0] + rel_vel[1] * normal[1]) / normal_sq
                    if proj < 0.0:
                        impulse = proj * normal
                        self.vel[i] -= impulse
                        self.vel[j] += impulse

                    dp_end = self.pos[i] - self.pos[j]
                    dist_end_sq = dp_end[0] * dp_end[0] + dp_end[1] * dp_end[1]
                    if dist_end_sq < r_sq:
                        dist_end = sqrt(dist_end_sq) if dist_end_sq > eps else 0.0
                        normal_len = sqrt(normal_sq)
                        if normal_len <= eps:
                            continue
                        normal_hat = normal / normal_len
                        overlap = r - dist_end
                        correction = 0.5 * overlap * normal_hat
                        self.pos[i] += correction
                        self.pos[j] -= correction

    def reverse(self):
        """Flip time direction. Negate all velocities."""
        self.time_direction *= -1

    def entropy(self):
        """Boltzmann configurational entropy via coarse-grained microstate counting.

        S = k_B * ln(W) where W = N! / prod(n_i!)
        Computed in log-space via lgamma for numerical stability.
        """
        rows, cols = self.grid_shape
        cell_w = self.width / cols
        cell_h = self.height / rows

        # Bin particles into grid cells
        cx = np.clip((self.pos[:, 0] / cell_w).astype(int), 0, cols - 1)
        cy = np.clip((self.pos[:, 1] / cell_h).astype(int), 0, rows - 1)
        cell_idx = cy * cols + cx

        counts = np.bincount(cell_idx, minlength=rows * cols)
        cell_counts = counts.reshape((rows, cols))

        # S = k_B * [ln(N!) - sum(ln(n_i!))]
        log_W = lgamma(self.n + 1) - sum(lgamma(int(c) + 1) for c in counts)
        S = K_B * log_W

        return S, cell_counts

    def entropy_max(self):
        """Maximum entropy: uniform distribution across all cells."""
        M = self.grid_shape[0] * self.grid_shape[1]
        if M == 0:
            return 1.0
        # S_max = k_B * ln(M^N / ...) ≈ N * ln(M) for large N uniform
        # More precisely: S_max = k_B * [ln(N!) - M * ln((N/M)!)]
        # For the combinatorial definition, max is when all cells have N/M particles
        n_per_cell = self.n / M
        if n_per_cell < 1:
            return K_B * self.n * log(M) if M > 0 else 1.0
        log_W_max = lgamma(self.n + 1) - M * lgamma(int(round(n_per_cell)) + 1)
        return K_B * log_W_max if log_W_max > 0 else 1.0

    def entropy_normalized(self):
        """S / S_max. 0 = perfect order, 1 = equilibrium."""
        S, _ = self.entropy()
        S_max = self.entropy_max()
        return min(S / S_max, 1.0) if S_max > 0 else 0.0

    def kinetic_energy(self):
        """Total kinetic energy. KE = 0.5 * m * v^2, m=1."""
        return 0.5 * np.sum(self.vel ** 2)

    def measured_temperature(self):
        """T from equipartition: <KE> = (d/2) * N * k_B * T, d=2."""
        if self.n == 0:
            return 0.0
        return self.kinetic_energy() / (self.n * K_B)

    def particle_positions(self):
        """Integer pixel positions for rendering."""
        px = np.clip(self.pos[:, 0].astype(int), 0, self.width - 1)
        py = np.clip(self.pos[:, 1].astype(int), 0, self.height - 1)
        return np.column_stack([px, py])

    def add_particles(self, count=10):
        """Add particles at random positions with MB velocities."""
        sigma = np.sqrt(K_B * self.temperature)
        new_pos = np.column_stack([
            np.random.uniform(0, self.width, count),
            np.random.uniform(0, self.height, count),
        ])
        new_vel = np.random.normal(0, sigma, (count, 2))
        self.pos = np.vstack([self.pos, new_pos])
        self.vel = np.vstack([self.vel, new_vel])
        self.n += count

    def remove_particles(self, count=10):
        """Remove particles. Keep at least 1."""
        count = min(count, self.n - 1)
        if count <= 0:
            return
        self.pos = self.pos[:-count]
        self.vel = self.vel[:-count]
        self.n -= count
