import random
from collections import deque
from dataclasses import dataclass, field


@dataclass
class Stimulus:
    text: str
    danger: float
    familiarity: float
    novelty: float
    social_signal: float


@dataclass
class QuasiConsciousAgent:
    short_memory_size: int = 8
    memory: deque = field(default_factory=lambda: deque(maxlen=8))
    state: dict = field(default_factory=lambda: {
        "arousal": 0.35,      # pobudzenie / napięcie
        "curiosity": 0.55,    # ciekawość
        "fatigue": 0.15,      # zmęczenie
        "trust": 0.50,        # zaufanie do otoczenia
        "coherence": 0.60,    # spójność wewnętrzna
    })
    self_model: dict = field(default_factory=lambda: {
        "identity": "observer-agent",
        "dominant_mode": "scan",
        "confidence": 0.50,
        "last_action": "none",
        "expected_outcome": "reduce uncertainty"
    })

    def __post_init__(self):
        self.memory = deque(maxlen=self.short_memory_size)

    def clamp(self, x, lo=0.0, hi=1.0):
        return max(lo, min(hi, x))

    def perceive(self, stimulus: Stimulus):
        """Zapisz bodziec do pamięci krótkotrwałej."""
        self.memory.append(stimulus)

    def update_state(self, stimulus: Stimulus):
        """
        Aktualizacja stanu wewnętrznego na podstawie bodźca i pamięci.
        To nie jest świadomość, ale system dynamicznego stanu.
        """
        s = self.state

        # wpływ bieżącego bodźca
        s["arousal"] += 0.45 * stimulus.danger + 0.15 * stimulus.novelty - 0.20 * stimulus.familiarity
        s["curiosity"] += 0.40 * stimulus.novelty - 0.15 * stimulus.danger
        s["trust"] += 0.30 * stimulus.familiarity + 0.20 * stimulus.social_signal - 0.25 * stimulus.danger
        s["fatigue"] += 0.04
        s["coherence"] += 0.15 * stimulus.familiarity - 0.10 * stimulus.novelty

        # wpływ pamięci: średni poziom niebezpieczeństwa ostatnich zdarzeń
        if len(self.memory) > 0:
            avg_danger = sum(m.danger for m in self.memory) / len(self.memory)
            avg_familiarity = sum(m.familiarity for m in self.memory) / len(self.memory)

            s["arousal"] += 0.20 * avg_danger
            s["trust"] += 0.10 * avg_familiarity
            s["coherence"] += 0.05 * avg_familiarity - 0.05 * avg_danger

        # ograniczenia do [0,1]
        for key in s:
            s[key] = self.clamp(s[key])

    def attention_mechanism(self, stimulus: Stimulus):
        """
        Agent decyduje, na czym skupić uwagę.
        To jest uproszczona forma selekcji uwagi.
        """
        s = self.state

        scores = {
            "threat": 0.60 * stimulus.danger + 0.30 * s["arousal"],
            "novelty": 0.65 * stimulus.novelty + 0.20 * s["curiosity"],
            "social": 0.55 * stimulus.social_signal + 0.20 * stimulus.familiarity + 0.10 * s["trust"],
            "stability": 0.40 * stimulus.familiarity + 0.25 * s["coherence"] - 0.10 * s["arousal"],
        }

        focus = max(scores, key=scores.get)
        return focus, scores

    def decide(self, stimulus: Stimulus, focus: str):
        """
        Decyzja zależy od stanu, uwagi i bodźca.
        """
        s = self.state

        if focus == "threat":
            if s["arousal"] > 0.72 and stimulus.danger > 0.55:
                action = "withdraw"
            else:
                action = "observe"
        elif focus == "novelty":
            if s["curiosity"] > 0.55 and s["fatigue"] < 0.75:
                action = "explore"
            else:
                action = "observe"
        elif focus == "social":
            if s["trust"] > 0.52:
                action = "approach"
            else:
                action = "observe"
        else:
            action = "stabilize"

        self.self_model["last_action"] = action
        self.self_model["dominant_mode"] = focus
        self.self_model["confidence"] = self.estimate_confidence(stimulus, action)
        self.self_model["expected_outcome"] = self.expected_outcome(action)

        return action

    def estimate_confidence(self, stimulus: Stimulus, action: str):
        """
        Uproszczona pewność decyzji.
        """
        base = 0.45

        if action == "withdraw":
            base += 0.25 * stimulus.danger
        elif action == "explore":
            base += 0.20 * stimulus.novelty
        elif action == "approach":
            base += 0.20 * stimulus.social_signal + 0.15 * stimulus.familiarity
        elif action == "stabilize":
            base += 0.15 * self.state["coherence"]
        else:
            base += 0.10 * (1 - stimulus.danger)

        return round(self.clamp(base), 3)

    def expected_outcome(self, action: str):
        mapping = {
            "withdraw": "reduce risk",
            "observe": "gather more evidence",
            "explore": "reduce uncertainty through action",
            "approach": "test positive social contact",
            "stabilize": "restore internal coherence",
        }
        return mapping.get(action, "unknown")

    def inner_narration(self, stimulus: Stimulus, focus: str, action: str):
        """
        Wewnętrzna narracja. To daje efekt 'proto-refleksji'.
        """
        s = self.state
        conf = self.self_model["confidence"]

        lines = []
        lines.append(f"Bodziec: {stimulus.text}")
        lines.append(f"Fokus uwagi: {focus}")
        lines.append(
            f"Stan wewnętrzny -> arousal={s['arousal']:.2f}, curiosity={s['curiosity']:.2f}, "
            f"trust={s['trust']:.2f}, fatigue={s['fatigue']:.2f}, coherence={s['coherence']:.2f}"
        )
        lines.append(f"Decyzja: {action}")
        lines.append(f"Pewność: {conf:.2f}")
        lines.append(f"Przewidywany efekt: {self.self_model['expected_outcome']}")

        if action == "withdraw":
            lines.append("Interpretacja: wzorzec został uznany za potencjalnie zagrażający.")
        elif action == "explore":
            lines.append("Interpretacja: nowość bodźca przeważyła nad ostrożnością.")
        elif action == "approach":
            lines.append("Interpretacja: sygnał społeczny i znajomość obiektu obniżyły alarm.")
        elif action == "stabilize":
            lines.append("Interpretacja: system wybiera przywracanie równowagi zamiast ekspansji.")
        else:
            lines.append("Interpretacja: potrzebne są dalsze obserwacje przed silniejszą reakcją.")

        return "\n".join(lines)

    def step(self, stimulus: Stimulus):
        self.perceive(stimulus)
        self.update_state(stimulus)
        focus, scores = self.attention_mechanism(stimulus)
        action = self.decide(stimulus, focus)
        narration = self.inner_narration(stimulus, focus, action)
        return {
            "focus": focus,
            "attention_scores": scores,
            "action": action,
            "narration": narration,
            "state": dict(self.state),
            "self_model": dict(self.self_model),
        }


def demo():
    agent = QuasiConsciousAgent()

    scenarios = [
        Stimulus("hałas w ciemności", danger=0.72, familiarity=0.10, novelty=0.55, social_signal=0.00),
        Stimulus("znajomy głos z oddali", danger=0.12, familiarity=0.78, novelty=0.20, social_signal=0.75),
        Stimulus("nagły ruch po lewej stronie", danger=0.66, familiarity=0.18, novelty=0.62, social_signal=0.05),
        Stimulus("dziwny, świecący obiekt", danger=0.28, familiarity=0.05, novelty=0.92, social_signal=0.00),
        Stimulus("spokojna obecność bliskiej osoby", danger=0.02, familiarity=0.90, novelty=0.08, social_signal=0.85),
    ]

    print("=" * 72)
    print("DEMO: AGENT QUASI-ŚWIADOMY")
    print("To nie jest świadomość, tylko symulacja: stan + pamięć + uwaga + decyzja.")
    print("=" * 72)

    for i, stimulus in enumerate(scenarios, start=1):
        print(f"\n--- KROK {i} ---")
        result = agent.step(stimulus)

        print(result["narration"])
        print("Attention scores:", {k: round(v, 3) for k, v in result["attention_scores"].items()})
        print("Self-model:", result["self_model"])

    print("\n" + "=" * 72)
    print("KONIEC DEMO")
    print("=" * 72)


if __name__ == "__main__":
    demo()
