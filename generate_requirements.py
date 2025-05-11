#!/usr/bin/env python3
import os, sys, ast

# for Python ≥3.8 use importlib.metadata, else pip‑install importlib_metadata
try:
    from importlib.metadata import distributions
except ImportError:
    from importlib_metadata import distributions

def find_py_files(root):
    for dirpath, _, files in os.walk(root):
        for fn in files:
            if fn.endswith('.py'):
                yield os.path.join(dirpath, fn)

def extract_imports(path):
    imports = set()
    try:
        src = open(path, encoding='utf-8').read()
        tree = ast.parse(src, filename=path)
    except Exception:
        return imports
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                imports.add(a.name.split('.')[0])
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0 and node.module:
                imports.add(node.module.split('.')[0])
    return imports

def build_dist_map():
    """Map top‑level module name → distribution name."""
    mod2dist = {}
    for dist in distributions():
        name = dist.metadata["Name"]
        # some dists lack top_level.txt
        try:
            top = dist.read_text('top_level.txt') or ''
        except Exception:
            continue
        for mod in top.split():
            mod2dist[mod.lower()] = name
    return mod2dist

def main(root):
    # 1) Gather all imports
    all_imps = set()
    for py in find_py_files(root):
        all_imps |= extract_imports(py)

    # 2) Exclude stdlib
    std = set(getattr(sys, 'stdlib_module_names', ())) \
          | set(sys.builtin_module_names)
    std = {m.lower() for m in std}

    # 3) Exclude your own modules (by filename)
    local = {os.path.splitext(os.path.basename(p))[0].lower()
             for p in find_py_files(root)}

    # 4) Build real module → dist map
    mod2dist = build_dist_map()

    # 5) Filter imports → only those in mod2dist, not in std or local
    reqs = {
        mod2dist[imp.lower()]
        for imp in all_imps
        if imp.lower() in mod2dist
        and imp.lower() not in std
        and imp.lower() not in local
    }

    # 6) Write sorted list
    with open('requirements.txt', 'w', encoding='utf-8') as f:
        for pkg in sorted(reqs):
            f.write(pkg + '\n')
    print(f"Wrote {len(reqs)} packages to requirements.txt")

if __name__ == '__main__':
    root = sys.argv[1] if len(sys.argv) > 1 else '.'
    main(root)
