from contextvars import ContextVar
from typing import Optional
from pydantic import BaseModel

# Stores the request context for the current request
request_context: ContextVar[Optional["RequestContext"]] = ContextVar("request_context", default=None)

class RequestContext(BaseModel):
    requestId: str
    widgetSessionId: Optional[str] = None
