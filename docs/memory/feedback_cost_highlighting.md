---
name: Always highlight Azure resource costs
description: User wants every Azure resource annotated with its cost tier; prefer free/serverless; flag anything that costs money
type: feedback
---

Always highlight the cost of any Azure resource (or any resource) that is not free. Keep costs minimal — prefer free tiers, serverless, and scale-to-zero options. Annotate every resource recommendation with its pricing tier and approximate monthly cost.

**Why:** User explicitly requested this to stay cost-aware during development and the showcase.

**How to apply:** In design docs, ADRs, and code comments referencing Azure resources, always note: free / $X/month / pay-per-use. Flag any resource that has a minimum always-on cost.
