.PHONY: run test clean

PYTHON ?= python3

# Run the default module (The Box)
run:
	$(PYTHON) entropy.py

# Run a specific module: make module=box run-module
run-module:
	$(PYTHON) entropy.py $(module)

# Run tests
test:
	$(PYTHON) -m pytest tests/ -v

# Quick smoke test without pytest
smoke:
	$(PYTHON) -c "from core.engine import ParticleSystem; s = ParticleSystem(200, (160, 88), 'corner'); [s.step() for _ in range(100)]; e, _ = s.entropy(); print(f'S={e:.2f} S/Smax={s.entropy_normalized():.3f} T={s.measured_temperature():.3f} — OK')"

# Remove bytecode
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name '*.pyc' -delete 2>/dev/null || true
	find . -name '*.pyo' -delete 2>/dev/null || true
	find . -type d -name '.pytest_cache' -exec rm -rf {} + 2>/dev/null || true
