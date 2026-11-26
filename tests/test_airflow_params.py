"""Offline checks without importing the application or connecting to its database."""

import ast
from datetime import datetime
from enum import Enum
import json
import logging
from pathlib import Path
import re
from types import SimpleNamespace
from typing import Any, Dict, List, Optional, Tuple
import unittest
from unittest.mock import Mock

from pydantic import BaseModel


ROOT = Path(__file__).resolve().parents[1]


def load_definitions(path, names, namespace, class_name=None):
    tree = ast.parse((ROOT / path).read_text())
    body = tree.body
    if class_name:
        body = next(node.body for node in body if isinstance(node, ast.ClassDef) and node.name == class_name)
    definitions = [node for node in body if getattr(node, "name", None) in names]
    for node in definitions:
        node.decorator_list = []
    exec(compile(ast.Module(body=definitions, type_ignores=[]), path, "exec"), namespace)


namespace = dict(
    Enum=Enum, BaseModel=BaseModel, Any=Any, Optional=Optional, List=List,
    Dict=Dict, Tuple=Tuple, json=json, logger=logging.getLogger(__name__),
)
load_definitions("helpdesk/libs/types.py", {"ParamType", "Param"}, namespace)
namespace["AirflowProvider"] = SimpleNamespace(EXTRA_INFO_RE=re.compile(r".*```helpdesk(.+)```.*", re.DOTALL))
load_definitions("helpdesk/models/provider/airflow.py", {"airflow_schema_to_helpdesk"}, namespace, "AirflowProvider")
convert = namespace["airflow_schema_to_helpdesk"]


class AirflowSchemaTest(unittest.TestCase):
    def test_defaults_keep_json_types(self):
        fields = {
            name: {"value": value, "schema": {"type": ["null", field_type]}}
            for name, field_type, value in (
                ("nologin", "boolean", False), ("timeout", "integer", 0),
                ("tags", "array", ["test"]), ("name", "string", "test"),
            )
        }
        params, _, _ = convert(fields)
        for name, definition in fields.items():
            with self.subTest(name=name):
                self.assertEqual(params[name].default, definition["value"])
                self.assertIs(type(params[name].default), type(definition["value"]))

    def test_enum_hides_null_and_accepts_either_type_order(self):
        for types in (["null", "string"], ["string", "null"]):
            field = {"value": None, "schema": {"type": types, "enum": [None, "test"]}}
            params, _, _ = convert({"tag": field})
            self.assertEqual(params["tag"].enum, ["test"])
            self.assertFalse(params["tag"].required)
            self.assertEqual(field["schema"]["enum"], [None, "test"])

    def test_required_field_and_helpdesk_metadata(self):
        metadata = {
            "immutable": True,
            "schema": {"oneOf": [{"required": ["name"]}]},
            "pretty_task_log_formatter": {"task": "formatter"},
        }
        params, schema, extra = convert({
            "name": {"value": None, "schema": {"type": "string"}},
            "helpdesk_ticket_callback_url": {
                "value": None,
                "schema": {"type": ["null", "string"], "description_md":
                           "Callback\n```helpdesk\n" + json.dumps(metadata) + "\n```"},
            },
        })
        self.assertTrue(params["name"].required)
        self.assertTrue(params["helpdesk_ticket_callback_url"].immutable)
        self.assertEqual(schema["oneOf"], metadata["schema"]["oneOf"])
        self.assertEqual(extra["pretty_task_log_formatter"], {"task": "formatter"})


class TicketCaptured(Exception):
    pass


class ActionParamsTest(unittest.IsolatedAsyncioTestCase):
    async def run_until_ticket(self, definitions, form):
        ticket = Mock(side_effect=TicketCaptured)
        ns = dict(
            logger=logging.getLogger(__name__), TICKET_CALLBACK_PARAMS=[],
            PARAM_FILLUP={}, PREPROCESS_TICKET=[], Ticket=ticket, datetime=datetime,
        )
        load_definitions("helpdesk/models/action.py", {"run"}, ns, "Action")
        action = SimpleNamespace(parameters=lambda provider, user: definitions, name="test", target_object="test")
        try:
            result = await ns["run"](action, SimpleNamespace(provider_type="airflow"), form,
                                     SimpleNamespace(name="test-user"))
        except TicketCaptured:
            return ticket.call_args.kwargs["params"], None
        return result

    async def test_required_false_and_zero_reach_ticket(self):
        definitions = {
            "flag": {"required": True, "default": None, "type": "boolean"},
            "count": {"required": True, "default": None, "type": "integer"},
        }
        params, _ = await self.run_until_ticket(definitions, {"flag": False, "count": 0})
        self.assertIs(params["flag"], False)
        self.assertIs(type(params["count"]), int)
        self.assertEqual(params["count"], 0)

    async def test_empty_optional_string_is_omitted(self):
        params, _ = await self.run_until_ticket({"tag": {"required": False}}, {"tag": ""})
        self.assertEqual(params, {})

    async def test_required_missing_or_empty_still_rejected(self):
        for form in ({}, {"name": ""}, {"name": None}, {"name": []}):
            with self.subTest(form=form):
                params, error = await self.run_until_ticket({"name": {"required": True}}, form)
                self.assertIsNone(params)
                self.assertIn("required", error)


if __name__ == "__main__":
    unittest.main()
