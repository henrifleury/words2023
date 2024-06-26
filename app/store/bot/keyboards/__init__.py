import os
print(os.path.dirname(os.path.realpath(__file__)))
kb_path = os.path.dirname(os.path.realpath(__file__))

with open(os.path.join(kb_path, "keyboard_main.json"), 'r', encoding='UTF-8') as f:
    keyboard_main = f.read()

with open(os.path.join(kb_path, "keyboard_empty.json"), 'r', encoding='UTF-8') as f:
    keyboard_empty = f.read()

with open(os.path.join(kb_path, "keyboard_start.json"), 'r', encoding='UTF-8') as f:
    keyboard_start = f.read()

test_kb_path=os.path.join(kb_path, "keyboard_test.json")
if os.path.isfile(test_kb_path):
    with open(test_kb_path, 'r', encoding='UTF-8') as f:
        keyboard_test = f.read()
