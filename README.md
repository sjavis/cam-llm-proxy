# Proxy script for using Cambridge LLM models with Claude Code

The LiteLLM/vLLM service cannot handle thinking blocks sent (back) from Claude Code.
This proxy script strips them out when sending messages.

To install the dependencies and run the proxy:
```bash
python -m venv claude-proxy-venv
source claude-proxy-venv/bin/activate
pip install -r requirements.txt
python claude_proxy.py
```

This requires setting the `CAMLLM_API_KEY` environment variable.
It is setup to run on the 127.0.0.1:18787 port,
so make sure this is set in `~/.claude/settings.json`:
```
  "env": {
    "ANTHROPIC_BASE_URL": "http://127.0.0.1:18787",
  }
```

## Updating Cambridge LLM models
There is also a script to automatically detect the list of models on llm.hpc.cam.ac.uk and update `~/.claude/settings.json` to make these available:
```
python update-cam-llm-models.py
```
