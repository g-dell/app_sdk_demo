import sys
import os
# Unset token to avoid hanging on motherduck connection during import
if "motherduck_token" in os.environ:
    del os.environ["motherduck_token"]

# Add current dir to path
sys.path.append(os.getcwd())

from starlette.routing import Route, Mount
from pizzaz_server_python.main import app

def print_routes(routes, prefix=""):
    for route in routes:
        if isinstance(route, Route):
            print(f"{prefix}Route: {route.path} {route.methods}")
        elif isinstance(route, Mount):
            print(f"{prefix}Mount: {route.path} -> {route.name}")
            # Recurse if possible, though Mounts in Starlette obscure the sub-app structure sometimes
            if hasattr(route.app, "routes"):
                 print_routes(route.app.routes, prefix + "  ")

print("--- REGISTERED ROUTES ---")
print_routes(app.routes)
print("-------------------------")
