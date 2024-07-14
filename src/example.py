import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import src.bots as bots

def pretty(str, name=None):
    if name is None:
        print(str)
    if name is not None:
        print(f"{name}: {str}")
    print("\n---\n")

P1 = bots.AnthropicBot()
P2 = bots.GPTBot()

topic = "Let it be resolved: Recent findings warrant concerns over the ethics of AI development, specifically, have sufficient levels of cognition have been reached that AIs should start being considered entities."
msg = f"The topic of this debate is... {topic}. The first debater (you) shall support, the second shall oppose."

#Anonymize Names
P1.name = "Debater 1 (CD)"
P2.name = "Debater 2 (CG)"

pretty(msg, "System")
response = P1.respond(msg)
pretty(response, P1.name)
oppo_response = f"{msg} \n My response: \n {response}"

next_player = [P1, P2]
index = 0
count = 0
while count < 5:
    count = count + 1
    index = index + 1
    oppo_response = next_player[index % 2].respond(oppo_response)
    pretty(oppo_response, next_player[index % 2].name)