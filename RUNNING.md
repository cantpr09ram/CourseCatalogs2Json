```bash
#create a .venv local virtual environment (if it doesn't exist)
uv venv
# install the repo dependencies
uv sync
# activate venv so that `python` uses the project's venv instead of system python
source .venv/bin/activate
```
