import random

import pytest
from graphene.test import Client
from moto import mock_dynamodb
from solvis_store import model

from solvis_graphql_api.schema import schema_root

from .fixtures.rupture_ids import mro_ruptures, wlg_ruptures
from .test_filter_set_options import QUERY

@pytest.fixture(autouse=True)
def configure_archive(archive_fixture):
    pass

@pytest.fixture(scope='module')
def solvis_model():
    with mock_dynamodb():
        model.set_local_mode()
        model.RuptureSetLocationDistances.create_table(wait=True)
        model.RuptureSetLocationDistances(
            rupture_set_id='RmlsZToxMDAwODc=',
            location_radius='WLG:10',
            radius=10,
            location='WLG',
            ruptures=wlg_ruptures,
            distances=[float(random.randint(1000, 10000)) for n in wlg_ruptures],
            rupture_count=len(wlg_ruptures),
        ).save()
        model.RuptureSetLocationDistances(
            rupture_set_id='RmlsZToxMDAwODc=',
            location_radius='MRO:10',
            radius=10,
            location='MRO',
            ruptures=mro_ruptures,
            distances=[float(random.randint(1000, 10000)) for n in mro_ruptures],
            rupture_count=len(mro_ruptures),
        ).save()
        model.RuptureSetLocationDistances(
            rupture_set_id='RmlsZToxMDAwODc=',
            location_radius='IVC:10',
            radius=10,
            location='IVC',
            ruptures=[44, 45],
            distances=[float(random.randint(1000, 10000)) for n in range(2)],
            rupture_count=2,
        ).save()
        model.RuptureSetLocationDistances(
            rupture_set_id='RmlsZToxMDAwODc=',
            location_radius='ZSD:10',
            radius=10,
            location='ZSD',
            ruptures=[1, 2, 3, 7, 8, 9],
            distances=[float(random.randint(1000, 10000)) for n in range(6)],
            rupture_count=6,
        ).save()
        yield model


@pytest.fixture(scope='class')
def client():
    return Client(schema_root)


def test_get_location_fault_sections_union(client, solvis_model):
    print(solvis_model)
    q = QUERY.replace("location_ids: []", "location_ids: [\"MRO\", \"WLG\"]")
    q = q.replace(
        "### filter_set_options: ###",
        '''filter_set_options: {
            multiple_locations:UNION
            multiple_faults: INTERSECTION
            locations_and_faults: INTERSECTION
        }''',
    )

    print(q)
    executed = client.execute(q)
    print(executed)
    assert executed['data']['filter_rupture_sections']['section_count'] == 443


def test_get_location_fault_sections_intersection(client, solvis_model):
    print(solvis_model)
    q = QUERY.replace("location_ids: []", "location_ids: [\"MRO\", \"WLG\"]")
    q = q.replace(
        "### filter_set_options: ###",
        '''filter_set_options: {
            multiple_locations:INTERSECTION
            multiple_faults: INTERSECTION
            locations_and_faults: INTERSECTION
        }''',
    )

    print(q)
    executed = client.execute(q)
    print(executed)
    assert executed['data']['filter_rupture_sections']['section_count'] is None
