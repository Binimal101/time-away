from __future__ import annotations
# This file re-exports definitions from the in-memory session so pto_tools can import by name.
# In this notebook environment, we can't truly "import" from memory; this shim allows us to write code that
# would be separate files in a real project.
# Implemented by duplicating the class/function signatures and delegating is not trivial here,
# so we will rely on the notebook's current namespace when executing tests.

