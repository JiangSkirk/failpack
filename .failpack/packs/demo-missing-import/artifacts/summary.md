# Session summary

- **status**: `failed`
- **exit_code**: `1`
- **events**: `11`

## User prompt

Add a /health endpoint to the FastAPI app that returns {"status": "ok"}. Keep tests green.

## Error

```
NameError: name 'health_payload' is not defined
Import missing in app/main.py — tests failed with exit_code=1
```

## Written files

- `app/health.py`
- `app/main.py`
