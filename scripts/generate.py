import random

with open("templates/hooks.txt") as f:
    hooks = f.readlines()

with open("facts/facts.txt") as f:
    facts = f.readlines()

hook = random.choice(hooks).strip()
fact = random.choice(facts).strip()

script = f"{hook} {fact} Follow for more."

with open("output.txt", "w") as f:
    f.write(script)

print(script)

