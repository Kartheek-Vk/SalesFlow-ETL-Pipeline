---
name: Python Spark runtime
description: Environment requirements for running the SalesFlow PySpark pipeline
---

PySpark requires a Java runtime in this workspace; the Python package alone is not sufficient. Keep Pandas below 3.0 for the current PySpark release because Pandas 3.x emits compatibility warnings and may not support all conversion paths.

**Why:** The first real pipeline run failed before creating a Spark session without Java, and PySpark explicitly warned that Pandas 3.x is not fully supported.

**How to apply:** When extending or recreating this pipeline, verify Java is installed and keep the Python dependency constraint aligned with the PySpark-supported Pandas range.