content = open('backend.py', 'r', encoding='utf-8').read()

content = content.replace(
    'print(f"SHEETS ERROR: {e}")\n            print(traceback.format_exc())',
    'print(f"SHEETS ERROR: {e}", flush=True)\n            print(traceback.format_exc(), flush=True)'
)

open('backend.py', 'w', encoding='utf-8').write(content)
print('PATCH OK')