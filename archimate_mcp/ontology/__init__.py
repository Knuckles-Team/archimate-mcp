"""ArchiMate modeling ontology contribution (CONCEPT:KG-2.325).

Data-only subpackage: it carries ``archimate.ttl`` (the ``owl:Ontology``
``http://knuckles.team/kg/archimate`` module — ArchiMate elements, layers and
their modeling relationships) which the agent-utilities hub federates in via the
``agent_utilities.ontology_providers`` entry-point. It holds no business logic
and no heavy imports so the hub can resolve it cheaply.
"""
