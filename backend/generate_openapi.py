from main import app
import json

openapi_schema = app.openapi()
with open("openapi.json", "w") as f:
    json.dump(openapi_schema, f, indent=2)

print("OpenAPI schema generated: openapi.json")
