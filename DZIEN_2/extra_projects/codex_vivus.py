#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
════════════════════════════════════════════════════════════════════════
 CODEX VIVUS — żywy organizm kodu
════════════════════════════════════════════════════════════════════════
 Quantum Dice        → probabilistyczny kolaps decyzji (amplitudy²)
 ROOTWEAVE-GA        → ewolucja drzew AST, fuzja korzeni, mutacje
 Teoria gier         → iterowany dylemat więźnia jako pole selekcji
 Autoprogramowanie   → organizmy SĄ kodem Pythona; kod pisze kod,
                       a silnik przepisuje własną politykę mutacji
                       i własną gramatykę. Trzy pętle zwrotne.

 Uruchomienie:
   python codex_vivus.py                # interfejs graficzny (tkinter)
   python codex_vivus.py --headless 50  # 50 pokoleń w terminalu

 Tylko biblioteka standardowa. Python 3.10+.

 Interpretatur, ergo est.
════════════════════════════════════════════════════════════════════════
"""

import math
import os
import random
import sys
import time

# ════════════════════════════════════════════════════════════════════
#  I. QUANTUM DICE — kolaps ważonych amplitud
# ════════════════════════════════════════════════════════════════════

class QuantumDice:
    """
    Kostka kwantowa: superpozycja opcji z amplitudami.
    P(opcja) ∝ amplituda². Źródło losowości: splot mapy logistycznej
    (chaos deterministyczny) z entropią sprzętową os.urandom.
    """

    def __init__(self, seed=None):
        self._chaos = 0.6180339887498949  # ziarno: złota proporcja
        self._rng = random.Random(seed if seed is not None
                                  else int.from_bytes(os.urandom(8), "big"))
        self.collapses = []          # historia kolapsów (etykiety)
        self.total_collapses = 0

    def _tick(self) -> float:
        self._chaos = 3.99 * self._chaos * (1.0 - self._chaos)
        hw = int.from_bytes(os.urandom(2), "big") / 65535.0
        return (self._chaos + hw + self._rng.random()) % 1.0

    def collapse(self, options):
        """options: lista (wartość, amplituda). Zwraca jedną wartość."""
        weights = [max(1e-9, float(a)) ** 2 for _, a in options]
        total = sum(weights)
        r = self._tick() * total
        acc = 0.0
        for (val, _), w in zip(options, weights):
            acc += w
            if r <= acc:
                self._record(val)
                return val
        self._record(options[-1][0])
        return options[-1][0]

    def _record(self, val):
        label = val if isinstance(val, str) else repr(val)
        self.collapses.append(label)
        if len(self.collapses) > 400:
            self.collapses = self.collapses[-400:]
        self.total_collapses += 1

    def uniform(self) -> float:
        return self._tick()

    def entropy(self) -> float:
        """Entropia Shannona ostatnich kolapsów (bity)."""
        if not self.collapses:
            return 0.0
        tail = self.collapses[-120:]
        counts = {}
        for c in tail:
            counts[c] = counts.get(c, 0) + 1
        n = len(tail)
        return -sum((k / n) * math.log2(k / n) for k in counts.values())


# ════════════════════════════════════════════════════════════════════
#  II. GENOM — drzewo AST renderowane do żywego źródła Pythona
# ════════════════════════════════════════════════════════════════════
#  node := ('const', float)
#        | ('var', nazwa)
#        | ('bin', op, L, R)          op ∈ + - *
#        | ('cmp', op, L, R)          op ∈ > < >=      (bool→float przez if)
#        | ('if', C, A, B)            (A if C else B)
# ════════════════════════════════════════════════════════════════════

VARS = ["t", "last_opp", "last_my", "opp_coop", "my_coop", "streak", "mood"]
BIN_OPS = ["+", "-", "*"]
CMP_OPS = [">", "<", ">="]
CONSTS = [0.0, 0.1, 0.25, 0.33, 0.5, 0.618, 0.75, 1.0, 1.5, 2.0]
MAX_DEPTH = 6


def random_tree(rng, depth, probs):
    """Losowe drzewo wg adaptowalnej gramatyki `probs`."""
    if depth <= 0:
        return (("const", rng.choice(CONSTS)) if rng.random() < 0.4
                else ("var", rng.choice(VARS)))
    r = rng.random()
    p_if, p_cmp, p_bin = probs["if"], probs["cmp"], probs["bin"]
    if r < p_if:
        return ("if",
                ("cmp", rng.choice(CMP_OPS),
                 random_tree(rng, depth - 2, probs),
                 random_tree(rng, depth - 2, probs)),
                random_tree(rng, depth - 1, probs),
                random_tree(rng, depth - 1, probs))
    if r < p_if + p_cmp:
        return ("cmp", rng.choice(CMP_OPS),
                random_tree(rng, depth - 1, probs),
                random_tree(rng, depth - 1, probs))
    if r < p_if + p_cmp + p_bin:
        return ("bin", rng.choice(BIN_OPS),
                random_tree(rng, depth - 1, probs),
                random_tree(rng, depth - 1, probs))
    return (("const", rng.choice(CONSTS)) if rng.random() < 0.4
            else ("var", rng.choice(VARS)))


def child_indices(node):
    kind = node[0]
    if kind in ("bin", "cmp"):
        return (2, 3)
    if kind == "if":
        return (1, 2, 3)
    return ()


def collect(node, path=()):
    """Wszystkie poddrzewa z pełnymi ścieżkami."""
    out = [(path, node)]
    for i in child_indices(node):
        out.extend(collect(node[i], path + (i,)))
    return out


def get_at(node, path):
    for i in path:
        node = node[i]
    return node


def set_at(node, path, new):
    if not path:
        return new
    lst = list(node)
    lst[path[0]] = set_at(node[path[0]], path[1:], new)
    return tuple(lst)


def depth_of(node):
    idx = child_indices(node)
    if not idx:
        return 1
    return 1 + max(depth_of(node[i]) for i in idx)


def size_of(node):
    return len(collect(node))


def render(node) -> str:
    """Drzewo → prawdziwe źródło Pythona."""
    kind = node[0]
    if kind == "const":
        return repr(node[1])
    if kind == "var":
        return node[1]
    if kind == "bin":
        return f"({render(node[2])} {node[1]} {render(node[3])})"
    if kind == "cmp":
        return f"(1.0 if ({render(node[2])} {node[1]} {render(node[3])}) else 0.0)"
    if kind == "if":
        return (f"({render(node[2])} if ({render(node[1])} >= 0.5) "
                f"else {render(node[3])})")
    raise ValueError(kind)


class Organism:
    """Organizm = drzewo + skompilowane, żywe źródło Pythona."""
    _next_id = 1

    def __init__(self, tree, born_op="genesis", parent_fit=None):
        self.id = Organism._next_id
        Organism._next_id += 1
        self.tree = tree
        self.src = render(tree)
        # AUTOPROGRAMOWANIE, poziom 1: organizm kompiluje własne ciało.
        self.code = compile(self.src, f"<organizm-{self.id}>", "eval")
        self.fitness = 0.0
        self.born_op = born_op
        self.parent_fit = parent_fit
        self.age = 0

    def decide(self, env: dict) -> int:
        """1 = kooperacja, 0 = zdrada."""
        try:
            val = eval(self.code, {"__builtins__": {}}, env)
            return 1 if float(val) >= 0.5 else 0
        except Exception:
            return 0

    def pretty(self) -> str:
        import textwrap
        head = (f"def strategia(t, last_opp, last_my, opp_coop,\n"
                f"              my_coop, streak, mood):\n")
        body = textwrap.fill(f"return {self.src}", width=60,
                             initial_indent="    ",
                             subsequent_indent="            ")
        return head + body


# ════════════════════════════════════════════════════════════════════
#  III. TEORIA GIER — iterowany dylemat więźnia
# ════════════════════════════════════════════════════════════════════

PAYOFF = {(1, 1): (3, 3), (1, 0): (0, 5), (0, 1): (5, 0), (0, 0): (1, 1)}
ROUNDS = 24


def duel(a: Organism, b: Organism, dice: QuantumDice):
    ha, hb = [], []
    sa = sb = 0
    mood_a, mood_b = dice.uniform(), dice.uniform()
    for t in range(ROUNDS):
        env_a = _env(t, ha, hb, mood_a)
        env_b = _env(t, hb, ha, mood_b)
        ma, mb = a.decide(env_a), b.decide(env_b)
        # szum kwantowy: 2% ruchów kolabsuje wbrew intencji
        if dice.uniform() < 0.02:
            ma = 1 - ma
        if dice.uniform() < 0.02:
            mb = 1 - mb
        pa, pb = PAYOFF[(ma, mb)]
        sa += pa
        sb += pb
        ha.append(ma)
        hb.append(mb)
    return sa / ROUNDS, sb / ROUNDS


def _env(t, my_hist, opp_hist, mood):
    n = len(opp_hist)
    streak = 0
    if n:
        last = opp_hist[-1]
        for m in reversed(opp_hist):
            if m == last:
                streak += 1
            else:
                break
    return {
        "t": t / ROUNDS,
        "last_opp": opp_hist[-1] if opp_hist else 0.5,
        "last_my": my_hist[-1] if my_hist else 0.5,
        "opp_coop": (sum(opp_hist) / n) if n else 0.5,
        "my_coop": (sum(my_hist) / len(my_hist)) if my_hist else 0.5,
        "streak": min(streak, 8) / 8.0,
        "mood": mood,
    }


# ════════════════════════════════════════════════════════════════════
#  IV. SILNIK EWOLUCJI — trzy pętle autoprogramowania
# ════════════════════════════════════════════════════════════════════
#  Pętla 1: organizmy przepisują własne źródło (mutacje AST).
#  Pętla 2: kostka przepisuje politykę mutacji (wagi operatorów
#           rosną tam, gdzie urodziły się lepsze dzieci).
#  Pętla 3: populacja przepisuje własną GRAMATYKĘ — struktura
#           najlepszych genomów zmienia prawdopodobieństwa,
#           z których rodzą się przyszłe genomy.
# ════════════════════════════════════════════════════════════════════

POP_SIZE = 24
ELITE = 2
OPPONENT_SAMPLE = 9


class Engine:
    def __init__(self, seed=None):
        self.dice = QuantumDice(seed)
        self.rng = random.Random(seed)
        self.gen = 0
        self.grammar = {"if": 0.28, "cmp": 0.22, "bin": 0.30}
        self.op_weights = {"punkt": 1.0, "poddrzewo": 1.0,
                           "fuzja": 1.0, "hoist": 0.6, "inwersja": 0.6}
        self.pop = [Organism(random_tree(self.rng, 4, self.grammar))
                    for _ in range(POP_SIZE)]
        self.best_hist, self.avg_hist = [], []
        self.log = []
        self.best = None
        self.last_best_src = ""
        self._evaluate()

    # ---------- log ----------
    def say(self, msg):
        self.log.append(f"[{self.gen:03d}] {msg}")
        if len(self.log) > 300:
            self.log = self.log[-300:]

    # ---------- ocena: turniej ----------
    def _evaluate(self):
        for o in self.pop:
            o.fitness = 0.0
        counts = {o.id: 0 for o in self.pop}
        for i, a in enumerate(self.pop):
            rivals = self.rng.sample(
                [x for x in self.pop if x is not a],
                min(OPPONENT_SAMPLE, POP_SIZE - 1))
            for b in rivals:
                fa, fb = duel(a, b, self.dice)
                a.fitness += fa
                b.fitness += fb
                counts[a.id] += 1
                counts[b.id] += 1
        for o in self.pop:
            o.fitness = o.fitness / max(1, counts[o.id])
            o.fitness -= 0.004 * size_of(o.tree)      # presja zwięzłości
        self.pop.sort(key=lambda o: o.fitness, reverse=True)
        self.best = self.pop[0]
        self.best_hist.append(self.best.fitness)
        self.avg_hist.append(sum(o.fitness for o in self.pop) / POP_SIZE)

    # ---------- operatory mutacji (Pętla 1) ----------
    def _mut_punkt(self, tree):
        nodes = collect(tree)
        path, node = self.rng.choice(nodes)
        kind = node[0]
        if kind == "const":
            new = ("const", self.rng.choice(CONSTS))
        elif kind == "var":
            new = ("var", self.rng.choice(VARS))
        elif kind == "bin":
            new = ("bin", self.rng.choice(BIN_OPS), node[2], node[3])
        elif kind == "cmp":
            new = ("cmp", self.rng.choice(CMP_OPS), node[2], node[3])
        else:
            new = ("if", node[1], node[3], node[2])   # zamiana gałęzi
        return set_at(tree, path, new)

    def _mut_poddrzewo(self, tree):
        nodes = collect(tree)
        path, _ = self.rng.choice(nodes)
        fresh = random_tree(self.rng, self.rng.randint(1, 3), self.grammar)
        return set_at(tree, path, fresh)

    def _mut_hoist(self, tree):
        nodes = [(p, n) for p, n in collect(tree) if p]
        if not nodes:
            return tree
        _, sub = self.rng.choice(nodes)
        return sub

    def _mut_inwersja(self, tree):
        cmps = [(p, n) for p, n in collect(tree) if n[0] == "cmp"]
        if not cmps:
            return self._mut_punkt(tree)
        path, node = self.rng.choice(cmps)
        flip = {">": "<", "<": ">", ">=": "<"}
        return set_at(tree, path, ("cmp", flip[node[1]], node[2], node[3]))

    def _fuzja(self, ta, tb):
        """ROOTWEAVE: fuzja korzeni — wymiana poddrzew dwóch rodziców."""
        pa, _ = self.rng.choice(collect(ta))
        pb, sub_b = self.rng.choice(collect(tb))
        return set_at(ta, pa, sub_b)

    def _prune(self, tree):
        while depth_of(tree) > MAX_DEPTH:
            tree = self._mut_hoist(tree)
        return tree

    # ---------- selekcja ----------
    def _tournament(self):
        cand = self.rng.sample(self.pop, 3)
        return max(cand, key=lambda o: o.fitness)

    # ---------- jedno pokolenie ----------
    def step(self):
        self.gen += 1
        newpop = list(self.pop[:ELITE])
        for e in newpop:
            e.age += 1

        while len(newpop) < POP_SIZE:
            # Pętla 2: kostka kolabsuje operator wg żywych wag
            op = self.dice.collapse(list(self.op_weights.items()))
            parent = self._tournament()
            if op == "fuzja":
                other = self._tournament()
                tree = self._fuzja(parent.tree, other.tree)
            elif op == "punkt":
                tree = self._mut_punkt(parent.tree)
            elif op == "poddrzewo":
                tree = self._mut_poddrzewo(parent.tree)
            elif op == "hoist":
                tree = self._mut_hoist(parent.tree)
            else:
                tree = self._mut_inwersja(parent.tree)
            tree = self._prune(tree)
            newpop.append(Organism(tree, born_op=op,
                                   parent_fit=parent.fitness))

        self.pop = newpop
        self._evaluate()
        self._reinforce_operators()
        self._rewrite_grammar()

        if self.best.src != self.last_best_src:
            self.say(f"NOWY LIDER #{self.best.id} "
                     f"(fit {self.best.fitness:.3f}, ur. przez '{self.best.born_op}')")
            self.last_best_src = self.best.src

    # ---------- Pętla 2: silnik przepisuje politykę mutacji ----------
    def _reinforce_operators(self):
        gains = {}
        for o in self.pop:
            if o.parent_fit is None or o.age > 0:
                continue
            d = o.fitness - o.parent_fit
            gains.setdefault(o.born_op, []).append(d)
        best_op, best_gain = None, -1e9
        for op, ds in gains.items():
            avg = sum(ds) / len(ds)
            w = self.op_weights[op] * (1.0 + 0.35 * max(-0.8, min(0.8, avg)))
            self.op_weights[op] = max(0.08, min(4.0, w))
            if avg > best_gain:
                best_gain, best_op = avg, op
        # renormalizacja: średnia wag = 1.0, liczą się relacje, nie skala
        mean_w = sum(self.op_weights.values()) / len(self.op_weights)
        if mean_w > 0:
            for op in self.op_weights:
                self.op_weights[op] = max(
                    0.08, min(4.0, self.op_weights[op] / mean_w))
        if best_op and best_gain > 0.15:
            self.say(f"kostka wzmacnia operator '{best_op}' "
                     f"(+{best_gain:.2f} śr. zysku)")

    # ---------- Pętla 3: populacja przepisuje własną gramatykę ----------
    def _rewrite_grammar(self):
        top = self.pop[:5]
        counts = {"if": 1.0, "cmp": 1.0, "bin": 1.0}
        total = 3.0
        for o in top:
            for _, n in collect(o.tree):
                if n[0] in counts:
                    counts[n[0]] += 1
                    total += 1
        old = dict(self.grammar)
        for k in self.grammar:
            target = 0.75 * counts[k] / total + 0.08
            self.grammar[k] = 0.9 * self.grammar[k] + 0.1 * target
        drift = sum(abs(self.grammar[k] - old[k]) for k in old)
        if drift > 0.012:
            self.say("gramatyka dryfuje: język przepisuje sam siebie "
                     f"(if {self.grammar['if']:.2f} / cmp {self.grammar['cmp']:.2f}"
                     f" / bin {self.grammar['bin']:.2f})")

    # ---------- burza kwantowa ----------
    def storm(self):
        for k in self.op_weights:
            self.op_weights[k] = 0.2 + 3.0 * self.dice.uniform()
        for i in range(POP_SIZE // 2, POP_SIZE):
            t = self._prune(self._mut_poddrzewo(self.pop[i].tree))
            self.pop[i] = Organism(t, born_op="burza")
        self._evaluate()
        self.say("⚡ BURZA KWANTOWA: polityka mutacji wylosowana od nowa, "
                 "połowa populacji przepisana")

    # ---------- opis polityki jako kod (metaźródło) ----------
    def policy_source(self) -> str:
        w = self.op_weights
        g = self.grammar
        return ("# metapoziom: kod, który decyduje, jak pisać kod\n"
                "POLITYKA_MUTACJI = {\n"
                + "".join(f"    '{k}': {v:.3f},\n" for k, v in w.items())
                + "}\n"
                "GRAMATYKA = {\n"
                + "".join(f"    '{k}': {v:.3f},\n" for k, v in g.items())
                + "}")


# ════════════════════════════════════════════════════════════════════
#  V. TRYB TERMINALOWY
# ════════════════════════════════════════════════════════════════════

def run_headless(generations: int):
    eng = Engine()
    print("CODEX VIVUS — tryb terminalowy\n" + "─" * 60)
    for _ in range(generations):
        eng.step()
        if eng.gen % 5 == 0 or eng.gen == 1:
            print(f"pok. {eng.gen:4d} | best {eng.best.fitness:6.3f} "
                  f"| avg {eng.avg_hist[-1]:6.3f} "
                  f"| entropia {eng.dice.entropy():4.2f} bit")
    print("─" * 60)
    print("NAJLEPSZY ORGANIZM — żywe źródło:\n")
    print(eng.best.pretty())
    print("\n" + eng.policy_source())
    print("\nOstatnie zdarzenia:")
    for line in eng.log[-8:]:
        print("  " + line)


# ════════════════════════════════════════════════════════════════════
#  VI. INTERFEJS GRAFICZNY (tkinter, ciemny)
# ════════════════════════════════════════════════════════════════════

BG = "#0b0e12"
PANEL = "#11161d"
EDGE = "#1e2733"
FG = "#c9d4e0"
DIM = "#5a6a7d"
AMBER = "#e8a33d"
GREEN = "#5dd39e"
RED = "#e05d5d"
CYAN = "#4db8c4"
MONO = ("Consolas", 10)
MONO_S = ("Consolas", 9)


def run_gui():
    import tkinter as tk

    eng = Engine()
    root = tk.Tk()
    root.title("CODEX VIVUS — organizm autoprogramujący")
    root.configure(bg=BG)
    root.geometry("1240x760")

    state = {"running": False, "delay": 120}

    # ── nagłówek ────────────────────────────────────────────────
    top = tk.Frame(root, bg=BG)
    top.pack(fill="x", padx=14, pady=(10, 4))
    tk.Label(top, text="CODEX VIVUS", bg=BG, fg=AMBER,
             font=("Consolas", 18, "bold")).pack(side="left")
    tk.Label(top, text="  quantum dice × rootweave-ga × teoria gier × autoprogramowanie",
             bg=BG, fg=DIM, font=MONO_S).pack(side="left", pady=(6, 0))
    gen_lbl = tk.Label(top, text="pokolenie 0", bg=BG, fg=FG,
                       font=("Consolas", 12, "bold"))
    gen_lbl.pack(side="right")

    body = tk.Frame(root, bg=BG)
    body.pack(fill="both", expand=True, padx=14, pady=6)
    body.columnconfigure(0, weight=5)
    body.columnconfigure(1, weight=4)
    body.rowconfigure(0, weight=5)
    body.rowconfigure(1, weight=3)

    def panel(parent, title):
        f = tk.Frame(parent, bg=PANEL, highlightbackground=EDGE,
                     highlightthickness=1)
        tk.Label(f, text=title, bg=PANEL, fg=DIM, anchor="w",
                 font=("Consolas", 9, "bold")).pack(fill="x", padx=8, pady=(6, 0))
        return f

    # ── lewy górny: żywe źródło ─────────────────────────────────
    p_code = panel(body, "ŻYWE ŹRÓDŁO — najlepszy organizm (kod pisze sam siebie)")
    p_code.grid(row=0, column=0, sticky="nsew", padx=(0, 6), pady=(0, 6))
    code_txt = tk.Text(p_code, bg="#0a0d10", fg=GREEN, insertbackground=GREEN,
                       font=MONO, relief="flat", wrap="none", height=14)
    code_txt.pack(fill="both", expand=True, padx=8, pady=8)
    code_txt.configure(state="disabled")

    # ── prawy górny: wykres fitness ─────────────────────────────
    p_fit = panel(body, "EWOLUCJA FITNESS — best (bursztyn) / avg (szary)")
    p_fit.grid(row=0, column=1, sticky="nsew", pady=(0, 6))
    fit_cv = tk.Canvas(p_fit, bg="#0a0d10", highlightthickness=0)
    fit_cv.pack(fill="both", expand=True, padx=8, pady=8)

    # ── lewy dolny: metapoziom + kostka ─────────────────────────
    p_meta = panel(body, "METAPOZIOM — polityka mutacji i gramatyka (silnik przepisuje sam siebie)")
    p_meta.grid(row=1, column=0, sticky="nsew", padx=(0, 6))
    meta_frame = tk.Frame(p_meta, bg=PANEL)
    meta_frame.pack(fill="both", expand=True, padx=8, pady=6)
    meta_cv = tk.Canvas(meta_frame, bg="#0a0d10", highlightthickness=0, width=340)
    meta_cv.pack(side="left", fill="both", expand=True)
    meta_txt = tk.Text(meta_frame, bg="#0a0d10", fg=CYAN, font=MONO_S,
                       relief="flat", width=40)
    meta_txt.pack(side="right", fill="both", padx=(8, 0))
    meta_txt.configure(state="disabled")

    # ── prawy dolny: populacja + log ────────────────────────────
    p_pop = panel(body, "POPULACJA (heatmapa fitness) · DZIENNIK ORGANIZMU")
    p_pop.grid(row=1, column=1, sticky="nsew")
    pop_cv = tk.Canvas(p_pop, bg="#0a0d10", highlightthickness=0, height=70)
    pop_cv.pack(fill="x", padx=8, pady=(6, 2))
    log_txt = tk.Text(p_pop, bg="#0a0d10", fg=FG, font=MONO_S,
                      relief="flat", height=8)
    log_txt.pack(fill="both", expand=True, padx=8, pady=(2, 8))
    log_txt.configure(state="disabled")

    # ── pasek sterowania ────────────────────────────────────────
    bar = tk.Frame(root, bg=BG)
    bar.pack(fill="x", padx=14, pady=(0, 10))

    def btn(txt, cmd, color=FG):
        return tk.Button(bar, text=txt, command=cmd, bg=PANEL, fg=color,
                         activebackground=EDGE, activeforeground=color,
                         relief="flat", font=("Consolas", 10, "bold"),
                         padx=14, pady=4, cursor="hand2")

    def toggle():
        state["running"] = not state["running"]
        b_run.config(text="⏸  PAUZA" if state["running"] else "▶  ŻYCIE")
        if state["running"]:
            loop()

    def pulse():
        eng.step()
        redraw()

    def storm():
        eng.storm()
        redraw()

    def reset():
        nonlocal eng
        state["running"] = False
        b_run.config(text="▶  ŻYCIE")
        eng = Engine()
        redraw()

    b_run = btn("▶  ŻYCIE", toggle, GREEN)
    b_run.pack(side="left", padx=(0, 6))
    btn("PULS (1 pokolenie)", pulse).pack(side="left", padx=6)
    btn("⚡ BURZA KWANTOWA", storm, AMBER).pack(side="left", padx=6)
    btn("RESET", reset, RED).pack(side="left", padx=6)

    tk.Label(bar, text="tempo", bg=BG, fg=DIM, font=MONO_S).pack(side="left", padx=(18, 4))
    import tkinter as _tk
    speed = _tk.Scale(bar, from_=30, to=600, orient="horizontal", bg=BG, fg=DIM,
                      troughcolor=PANEL, highlightthickness=0, length=160,
                      showvalue=False, command=lambda v: state.update(delay=int(v)))
    speed.set(state["delay"])
    speed.pack(side="left")

    ent_lbl = tk.Label(bar, text="", bg=BG, fg=CYAN, font=MONO_S)
    ent_lbl.pack(side="right")

    # ── rysowanie ───────────────────────────────────────────────
    def lerp_color(f):
        """fitness 0..3.2 → od ciemnego przez czerwień do bursztynu/zieleni."""
        f = max(0.0, min(1.0, f / 3.2))
        r = int(30 + 200 * min(1, f * 1.6))
        g = int(30 + 190 * f)
        b = int(40 + 40 * (1 - f))
        return f"#{r:02x}{g:02x}{b:02x}"

    def redraw():
        gen_lbl.config(text=f"pokolenie {eng.gen}")
        ent_lbl.config(text=f"entropia kostki: {eng.dice.entropy():.2f} bit "
                            f"· kolapsów: {eng.dice.total_collapses}")

        # źródło
        code_txt.configure(state="normal")
        code_txt.delete("1.0", "end")
        b = eng.best
        code_txt.insert("end",
                        f"# organizm #{b.id} · fitness {b.fitness:.3f} · "
                        f"rozmiar {size_of(b.tree)} · ur.: {b.born_op}\n\n")
        code_txt.insert("end", b.pretty())
        code_txt.configure(state="disabled")

        # wykres fitness
        fit_cv.delete("all")
        w = fit_cv.winfo_width() or 400
        h = fit_cv.winfo_height() or 220
        hist_b, hist_a = eng.best_hist[-160:], eng.avg_hist[-160:]
        if len(hist_b) >= 2:
            lo = min(min(hist_a), 0.0)
            hi = max(max(hist_b), 3.0)
            span = max(1e-6, hi - lo)

            def pts(hist):
                n = len(hist)
                return [c for i, v in enumerate(hist) for c in
                        (8 + i * (w - 16) / max(1, n - 1),
                         h - 8 - (v - lo) / span * (h - 16))]
            fit_cv.create_line(*pts(hist_a), fill=DIM, width=1)
            fit_cv.create_line(*pts(hist_b), fill=AMBER, width=2)
            fit_cv.create_text(w - 8, 12, anchor="e", fill=AMBER, font=MONO_S,
                               text=f"best {hist_b[-1]:.3f}")
            fit_cv.create_text(w - 8, 28, anchor="e", fill=DIM, font=MONO_S,
                               text=f"avg  {hist_a[-1]:.3f}")

        # metapoziom: słupki wag operatorów + gramatyki
        meta_cv.delete("all")
        mw = meta_cv.winfo_width() or 340
        mh = meta_cv.winfo_height() or 150
        items = list(eng.op_weights.items()) + [
            ("g:" + k, v * 4) for k, v in eng.grammar.items()]
        bh = max(10, (mh - 16) // len(items) - 4)
        maxv = max(v for _, v in items)
        y = 8
        for name, v in items:
            frac = v / maxv
            color = CYAN if name.startswith("g:") else AMBER
            meta_cv.create_rectangle(90, y, 90 + frac * (mw - 150), y + bh,
                                     fill=color, width=0)
            meta_cv.create_text(84, y + bh / 2, anchor="e", fill=FG,
                                font=MONO_S, text=name)
            meta_cv.create_text(mw - 8, y + bh / 2, anchor="e", fill=DIM,
                                font=MONO_S, text=f"{v:.2f}")
            y += bh + 4

        meta_txt.configure(state="normal")
        meta_txt.delete("1.0", "end")
        meta_txt.insert("end", eng.policy_source())
        meta_txt.configure(state="disabled")

        # populacja
        pop_cv.delete("all")
        pw = pop_cv.winfo_width() or 480
        cell = max(14, (pw - 16) // POP_SIZE)
        for i, o in enumerate(eng.pop):
            x = 8 + i * cell
            pop_cv.create_rectangle(x, 12, x + cell - 3, 12 + 40,
                                    fill=lerp_color(o.fitness),
                                    outline=AMBER if i < ELITE else "#000000")
        pop_cv.create_text(8, 62, anchor="w", fill=DIM, font=MONO_S,
                           text="← elita | każdy kwadrat to organizm; jaśniej = wyższy fitness")

        # log
        log_txt.configure(state="normal")
        log_txt.delete("1.0", "end")
        for line in eng.log[-14:]:
            log_txt.insert("end", line + "\n")
        log_txt.see("end")
        log_txt.configure(state="disabled")

    def loop():
        if not state["running"]:
            return
        eng.step()
        redraw()
        root.after(state["delay"], loop)

    root.after(150, redraw)
    root.mainloop()


# ════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    if "--headless" in sys.argv:
        idx = sys.argv.index("--headless")
        n = int(sys.argv[idx + 1]) if len(sys.argv) > idx + 1 else 40
        run_headless(n)
    else:
        run_gui()
