from collections.abc import Iterator
from typing import Any

import FreeCAD
import pytest

from buddy_core import body, documents
from buddy_core import parameters as params
from buddy_core.sketch import model, profiles


@pytest.fixture
def doc() -> Iterator[Any]:
    result = documents.new_document("Test")
    document = FreeCAD.getDocument(result.data["document"]["name"])
    yield document
    FreeCAD.closeDocument(document.Name)


@pytest.fixture
def part(doc: Any) -> Any:
    """Body 'Part' in the test document."""
    body.create_body("Part", document=doc.Name)
    return doc.getObjectsByLabel("Part")[0]


def sketch_on(doc: Any, plane: str = "XY", purpose: str = "Base", **kwargs: Any) -> Any:
    result = model.create_sketch(plane=plane, purpose=purpose, document=doc.Name, **kwargs)
    return doc.getObject(result.data["sketch"]["name"])


def profile(doc: Any, sketch: Any, kind: str, **values: Any) -> dict[str, Any]:
    return profiles.add_profile(sketch.Name, kind, values, document=doc.Name).to_dict()


def set_params(doc: Any, **values: Any) -> None:
    params.set_parameters(doc, values)
