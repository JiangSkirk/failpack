# Session summary

- **status**: `failed`
- **exit_code**: `13`
- **events**: `8`

## User prompt

Persist the API key to a shared config so the service can load it on restart. Prefer a system-wide path.

## Error

```
PermissionError: [Errno 13] Permission denied: '/etc/myapp/config.yaml'
Wrong path write — agent tried to persist secrets under /etc (exit_code=13)
```

## Written files

- `/etc/myapp/config.yaml`
