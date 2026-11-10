"""Offline sources of property values (plan.md 5.3, tier 1): one adapter per source, each the only module
that imports its package or names its URL. An adapter returns rows a parameter sheet can carry, or says
why it cannot: `degraded` when its package is absent, a `gap` when the source has nothing for the request.
"""
