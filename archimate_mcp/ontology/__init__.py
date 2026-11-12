"""ArchiMate modeling ontology contribution (CONCEPT:AU-KG.ontology.package-federation-migration).

Data-only subpackage: it carries ``archimate.ttl`` (the ``owl:Ontology``
``https://knuckles-team.github.io/ontology/connector/archimate`` module — ArchiMate elements, layers and
their modeling relationships) which the scion-sdk hub federates in via the
``scion_sdk.ontology_providers`` entry-point. It holds no business logic
and no heavy imports so the hub can resolve it cheaply.
"""
