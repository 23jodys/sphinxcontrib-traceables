
import os
import ast
from xml.etree import ElementTree
from nose.tools import assert_raises
from utils import with_app, pretty_print_xml
from sphinxcontrib.traceables.filter import (FilterVisitor, FilterError,
                                             ExpressionMatcher)
from sphinxcontrib.traceables.infrastructure import Traceable, TraceablesFilter


#=============================================================================
# Tests for filter expression handling

def test_filter_syntax():
    identifier_values = {
        "color": "red",
        "version": 1.2,
    }
    def match(expression_input):
        matcher = ExpressionMatcher(expression_input)
        return matcher.matches(identifier_values)

    assert_raises(FilterError, match, "invalid syntax")
    assert_raises(FilterError, match, "")
    assert_raises(FilterError, match, "color\nversion")
    assert_raises(FilterError, match, "color + version")
    assert_raises(FilterError, match, "color, version")
    assert_raises(FilterError, match, "unknown_identifier")


def test_filter_operators():
    identifier_values = {
        "color": "red",
        "version": 1.2,
    }
    def match(expression_input):
        matcher = ExpressionMatcher(expression_input)
        return matcher.matches(identifier_values)

    # Operator "=="
    assert True  == match("color == 'red'")
    assert False == match("color == 'blue'")
    assert True  == match("'red' == color")
    assert False == match("'blue' == color")
    assert True  == match("'red' == 'red'")
    assert False == match("'blue' == 'red'")
    assert False == match("'blue' == 4.2")

    # Operator "!="
    assert False == match("color != 'red'")
    assert True  == match("color != 'blue'")

    # Operator ">"
    assert False == match("version > 2")
    assert True  == match("version > 1.1")

    # Operator ">="
    assert False == match("version >= 2")
    assert True  == match("version >= 1.2")

    # Operator "<"
    assert True  == match("version < 2")
    assert False == match("version < 1.1")

    # Operator "<="
    assert True  == match("version <= 1.2")
    assert False == match("version <= 1.1")

    # Operator "in"
    assert False == match("version in []")
    assert True  == match("version in [1.1, 1.2, -4]")

    # Operator "not in"
    assert True  == match("version not in []")
    assert False == match("version not in [1.1, 1.2, -4]")

    # Valid but unsupported operator
    assert_raises(FilterError, match, "version is 1.2")
    assert_raises(FilterError, match, "1.0 < version <= 1.2")

    # Invalid operator, syntax error
    assert_raises(FilterError, match, "version INVALID 1.2")


#=============================================================================
# Tests for filtering of traceables

class FilterTester(object):

    def __init__(self, traceables_input):
        self.traceables = []
        for tag, attributes in traceables_input:
            self.traceables.append(Traceable(None, tag))
            self.traceables[-1].attributes = attributes
        self.filter = TraceablesFilter(self.traceables)

    def verify(self, expression, expected_tags):
        matches = self.filter.filter(expression)
        matched_tags = [traceable.tag for traceable in matches]
        unexpected_tags = [tag for tag in matched_tags
                           if tag not in expected_tags]
        missing_tags = [tag for tag in expected_tags
                        if tag not in matched_tags]
        message_parts = []
        if unexpected_tags:
            message_parts.append("Unexpected but matched tag(s): {0}"
                                 .format(", ".join(unexpected_tags)))
        if missing_tags:
            message_parts.append("Expected but not matched tag(s): {0}"
                                 .format(", ".join(missing_tags)))
        if message_parts:
            message_parts.insert(0, "Filter expression {0!r}"
                                    .format(expression))
            raise Exception("; ".join(message_parts))


def test_filter_traceables():
    traceables_input = [
        ("SAGITTA",    {"title": "Sagitta", "color": "blue",
                        "version": 1.0}),
        ("AQUILA",     {"title": "Aquila", "parent": "SAGITTA",
                        "color": "red", "version": 0.8}),
    ]
    tester = FilterTester(traceables_input)
    tester.verify("color == 'blue'", ["SAGITTA"])
    tester.verify("color == 'red'", ["AQUILA"])
    tester.verify("color >= 'blue'", ["SAGITTA", "AQUILA"])
    tester.verify("version > -1", ["SAGITTA", "AQUILA"])
    tester.verify("version > 0.8", ["SAGITTA"])
    tester.verify("version > 1", [])
    tester.verify("version >= -1", ["SAGITTA", "AQUILA"])
    tester.verify("version >= 0.8", ["SAGITTA", "AQUILA"])
    tester.verify("version >= 1", ["SAGITTA"])
    tester.verify("version < 4", ["SAGITTA", "AQUILA"])
    tester.verify("version < 1", ["AQUILA"])
    tester.verify("version < -0.1", [])
    tester.verify("color in ['blue',' green']", ["SAGITTA"])
