import tomli

with open('pyproject.toml', 'rb') as f:
    data = tomli.load(f)
deps = data['project']['dependencies']
with open('requirements.txt', 'w') as f:
    f.write('\n'.join(deps))