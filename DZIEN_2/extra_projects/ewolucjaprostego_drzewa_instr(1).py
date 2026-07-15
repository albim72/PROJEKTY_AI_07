import random

POP_SIZE = 10
GENERATIONS = 20
MUTATION_RATE = 0.3

ATOMS = ["x", "1", "2", "3", "4", "5"]
OPS = ["+", "-", "*"]


def random_atom():
    return random.choice(ATOMS)


def random_program():
    # program typu: (a op b) op c
    a = random_atom()
    b = random_atom()
    c = random_atom()
    op1 = random.choice(OPS)
    op2 = random.choice(OPS)
    return f"({a} {op1} {b}) {op2} {c}"


def fitness(program):
    x = 4
    target = 20
    try:
        value = eval(program, {"__builtins__": {}}, {"x": x})
        return -abs(target - value)
    except:
        return -999


def mutate(program):
    tokens = program.replace("(", "").replace(")", "").split()

    # tokens: a op1 b op2 c
    if random.random() < MUTATION_RATE:
        tokens[0] = random_atom()
    if random.random() < MUTATION_RATE:
        tokens[1] = random.choice(OPS)
    if random.random() < MUTATION_RATE:
        tokens[2] = random_atom()
    if random.random() < MUTATION_RATE:
        tokens[3] = random.choice(OPS)
    if random.random() < MUTATION_RATE:
        tokens[4] = random_atom()

    return f"({tokens[0]} {tokens[1]} {tokens[2]}) {tokens[3]} {tokens[4]}"


def crossover(parent1, parent2):
    t1 = parent1.replace("(", "").replace(")", "").split()
    t2 = parent2.replace("(", "").replace(")", "").split()

    child1 = f"({t1[0]} {t1[1]} {t2[2]}) {t2[3]} {t1[4]}"
    child2 = f"({t2[0]} {t2[1]} {t1[2]}) {t1[3]} {t2[4]}"
    return child1, child2


def select(population):
    population = sorted(population, key=fitness, reverse=True)
    return population[:2]


population = [random_program() for _ in range(POP_SIZE)]

for generation in range(GENERATIONS):
    parent1, parent2 = select(population)
    new_population = [parent1, parent2]

    while len(new_population) < POP_SIZE:
        child1, child2 = crossover(parent1, parent2)
        child1 = mutate(child1)
        child2 = mutate(child2)
        new_population.extend([child1, child2])

    population = new_population[:POP_SIZE]

    best = max(population, key=fitness)
    print(f"Pokolenie {generation+1}: {best} -> fitness = {fitness(best)}")
