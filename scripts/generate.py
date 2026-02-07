import random
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

hooks_path = os.path.join(BASE_DIR, "templates", "hooks.txt")
facts_path = os.path.join(BASE_DIR, "facts", "facts.txt")

with open(hooks_path, "r") as f:
    hooks = [line.strip() for line in f if line.strip()]

with open(facts_path, "r") as f:
    facts = [line.strip() for line in f if line.strip()]

hook = random.choice(hooks)
fact = random.choice(facts)

script = f"{hook} {fact} Follow for more."

with open(os.path.join(BASE_DIR, "output.txt"), "w") as f:
    f.write(script)

print(script)
