"""Sparse text annotations in the style of research notes.
Feynman-style — clear, direct, slightly unsettling."""


class Narrator:
    """Condition-triggered narration. Each annotation fires at most once.

    After all narration rules have fired and the last one expires,
    falls back to a persistent controls hint if one was set.
    """

    CONTROLS_DELAY = 90  # frames idle before showing controls (~3s at 30fps)

    def __init__(self):
        self._rules = []
        self._active_text = None
        self._ttl = 0  # frames remaining
        self._controls_text = None
        self._idle_frames = 0  # frames with no active narration

    def add_rule(self, condition_fn, text, duration=120):
        """Register an annotation. condition_fn(state) -> bool."""
        self._rules.append({
            'condition': condition_fn,
            'text': text,
            'duration': duration,
            'fired': False,
        })

    def set_controls(self, text):
        """Set persistent controls hint shown when narration is idle."""
        self._controls_text = text

    def update(self, state):
        """Check conditions against current state. Decrement TTL."""
        if self._ttl > 0:
            self._ttl -= 1
            if self._ttl == 0:
                self._active_text = None

        fired_this_update = False
        for rule in self._rules:
            if rule['fired']:
                continue
            if rule['condition'](state):
                rule['fired'] = True
                self._active_text = rule['text']
                self._ttl = rule['duration']
                self._idle_frames = 0
                fired_this_update = True
                break  # one annotation at a time

        if not fired_this_update and self._active_text is None:
            self._idle_frames += 1
        else:
            self._idle_frames = 0

    def current_text(self):
        if self._active_text:
            return self._active_text
        # Show controls after idle period (whether or not all rules have fired)
        if self._controls_text and self._idle_frames >= self.CONTROLS_DELAY:
            return self._controls_text
        return None


def make_box_narrator():
    """Create narrator with annotations for The Box module."""
    n = Narrator()

    n.add_rule(
        lambda s: s.get('entropy_norm', 0) > 0.5 and s.get('time_dir', 1) == 1,
        'The system forgets its initial condition.',
        duration=150,
    )

    n.add_rule(
        lambda s: s.get('entropy_norm', 0) > 0.9,
        'Equilibrium. The most probable state is also the most boring.',
        duration=180,
    )

    n.add_rule(
        lambda s: s.get('just_reversed', False),
        'Every collision reversed. Physically legal. Statistically absurd.',
        duration=150,
    )

    n.add_rule(
        lambda s: s.get('entropy_norm', 1) < 0.3 and s.get('time_dir', 1) == -1,
        'The past hypothesis: the universe started in extraordinarily low entropy. Why?',
        duration=200,
    )

    n.add_rule(
        lambda s: s.get('first_pause', False),
        "S = k_B ln \u03a9 \u2014 Boltzmann's epitaph. Literally carved on his tombstone.",
        duration=180,
    )

    n.set_controls('SPACE pause  r reverse  m macro/micro  +/- particles  ? help  q back')

    return n
