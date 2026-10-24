import json, copy, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT = os.path.join(ROOT, "config", "default.json")
USER = os.path.join(ROOT, "config", "user.json")   # sobrescrituras (p.ej. HSV calibrado)

def _merge(a, b):
    for k, v in b.items():
        if isinstance(v, dict) and isinstance(a.get(k), dict):
            _merge(a[k], v)
        else:
            a[k] = v
    return a

def load():
    with open(DEFAULT) as f:
        cfg = json.load(f)
    if os.path.exists(USER):
        with open(USER) as f:
            _merge(cfg, json.load(f))
    return cfg

def save_user(section, values):
    data = {}
    if os.path.exists(USER):
        with open(USER) as f:
            data = json.load(f)
    data[section] = values
    with open(USER, "w") as f:
        json.dump(data, f, indent=2)
