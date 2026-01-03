# ADR-0008: CORS Configuration

## Status
Accepted

## Context
We have a frontend (Next.js) running on `localhost:3000` and a backend (FastAPI) running on `localhost:8000`. 

Browsers enforce the Same-Origin Policy, which blocks requests from:
- Different protocol (http vs https)
- Different domain (localhost vs 127.0.0.1)
- Different port (3000 vs 8000)

Without CORS configuration:
- Frontend cannot make API calls to backend
- Browser shows `strict-origin-when-cross-origin` error
- Development workflow is broken

## Decision
We implemented CORS middleware in FastAPI using `CORSMiddleware`:

1. **Middleware Configuration**: Added to `app/main.py`
2. **Allowed Origins**: Development URLs (`localhost:3000`, `localhost:3001`, `127.0.0.1:3000`, `127.0.0.1:3001`)
3. **Credentials**: Enabled for cookie/session support
4. **Methods**: All HTTP methods allowed (`*`)
5. **Headers**: All headers allowed (`*`)
6. **Expose Headers**: All headers exposed (`*`)

### Implementation:
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)
```

## Consequences

### Positive:
- ✅ Frontend can communicate with backend
- ✅ Development workflow works smoothly
- ✅ Supports multiple development ports
- ✅ Easy to configure
- ✅ Standard FastAPI approach

### Negative:
- ⚠️ Permissive configuration (all methods/headers) - OK for development
- ⚠️ Need to restrict in production
- ⚠️ Need to add production origins when deploying

## Production Considerations

For production, we should:
1. **Restrict Origins**: Only allow actual frontend domain(s)
2. **Restrict Methods**: Only allow needed methods (GET, POST, OPTIONS)
3. **Restrict Headers**: Only allow needed headers
4. **Environment-Based**: Use environment variables for origins
5. **HTTPS Only**: Enforce HTTPS in production

### Example Production Configuration:
```python
import os

ALLOWED_ORIGINS = os.getenv(
    "CORS_ALLOWED_ORIGINS",
    "http://localhost:3000,http://localhost:3001"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
    expose_headers=["X-Correlation-ID"],
)
```

## Security Considerations

- **Credentials**: Only enable if needed (cookies, auth headers)
- **Wildcard Origins**: Never use `["*"]` with `allow_credentials=True`
- **Headers**: Restrict to minimum needed
- **Methods**: Restrict to minimum needed

## Alternatives Considered

1. **No CORS**: Use same origin (proxy) - Limits flexibility
2. **Custom Middleware**: More control but more code
3. **Nginx CORS**: Handle at reverse proxy - Adds infrastructure complexity
4. **CORS Headers Manually**: More error-prone

## Future Enhancements

- Add environment-based configuration
- Add production origins configuration
- Add CORS preflight caching
- Add CORS metrics/logging

## References
- [FastAPI CORS](https://fastapi.tiangolo.com/tutorial/cors/)
- [MDN CORS](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS)
- [OWASP CORS Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/HTML5_Security_Cheat_Sheet.html#cross-origin-resource-sharing)

