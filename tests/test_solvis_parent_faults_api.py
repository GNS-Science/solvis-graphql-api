"""Tests for possibly unused `get_parent_fault_names"""

from graphene.test import Client

from solvis_graphql_api.schema import schema_root

QUERY_ALL = """
    query {
        get_parent_fault_names(
            model_id: "NSHM_v1.0.4"
            fault_system: "CRU"
        )
    }
"""


def test_get_all_parent_fault_names(archive_fixture_tiny):
    client = Client(schema_root)
    executed = client.execute(
        QUERY_ALL,
        variable_values={},
    )
    print(executed)
    assert "get_parent_fault_names" in executed["data"]
    assert executed["data"]["get_parent_fault_names"][0] == "Acton"
    assert executed["data"]["get_parent_fault_names"][-1] == "Woodville"
    assert len(executed["data"]["get_parent_fault_names"]) == 557
