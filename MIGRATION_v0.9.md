# 0.9.0 Migration notes

## Migration to new DynamoDB/S3 blob store

Since version v0.9.x this API uses a dynamoDB/S3 data_store for the CompositeRupture zip archive, rather than bundling this file in the deployment.

### Datastore setup

Below is the one-time script output from the cli which creates the table and pushes up the archive file.

```
% AWS_PROFILE=chrisbc S3_BUCKET_NAME=nzshm22-solvis-graphql-api-prod REGION=ap-southeast-2 DEPLOYMENT_STAGE=prod poetry run cli -T -R ~/Downloads/NSHM_v1.0.4_CompositeSolution.zip NSHM_v1.0.4
WARNING: optional `toshi` dependencies are not installed.
Running without `toshi` options
WARNING: geometry.section_distance() uses the optional dependency pyvista.
2025-10-07 14:42:17 INFO     congiguring BinaryLargeObjectModel with IS_OFFLINE: False TESTING: False
2025-10-07 14:42:17 INFO     Found credentials in shared credentials file: ~/.aws/credentials
archive: /Users/chrisbc/Downloads/NSHM_v1.0.4_CompositeSolution.zip
model : NSHM_v1.0.4
2025-10-07 14:42:17 INFO     Found credentials in shared credentials file: ~/.aws/credentials
2025-10-07 14:42:18 INFO     put the blob
2025-10-07 14:42:18 INFO     Found credentials in shared credentials file: ~/.aws/credentials
2025-10-07 14:42:28 INFO     <class 'solvis_graphql_api.data_store.model.BinaryLargeObject'>.get() called
2025-10-07 14:42:28 INFO     get object_blob from bucket <solvis_graphql_api.data_store.model.BinaryLargeObject object at 0x113c69be0>
compared blob OK for NSHM_v1.0.4,
solvis_graphql_api cli uploaded solvis composite solution <solvis_graphql_api.data_store.model.BinaryLargeObject object at 0x10a4716a0>
```

### API A/B testing

And below is the A/B test showing that Prod/Test APIs are working and agree.

```
chrisbc@MLX01 solvis-graphql-api % poetry run cli_ab_test WORK/ab.toml -A prod -B test -v
WARNING: optional `toshi` dependencies are not installed.
Running without `toshi` options
config `WORK/ab.toml` has service keys: dict_keys(['prod', 'test', 'dev'])
using a-key: `prod`, b-key: `test`
2025-10-07 14:46:04 INFO     function: check_locations_by_id, a/b tests PASS
2025-10-07 14:46:04 INFO     function: check_composite_rupture_detail, a/b tests PASS
2025-10-07 14:46:04 INFO     function: check_about, a/b tests PASS
2025-10-07 14:46:05 INFO     function: check_filter_ruptures, a/b tests PASS
2025-10-07 14:46:05 INFO     function: check_filter_rupture_sections, a/b tests PASS
2025-10-07 14:46:05 INFO     function: check_get_radii_set, a/b tests PASS
2025-10-07 14:46:06 INFO     function: check_get_location_list, a/b tests PASS
2025-10-07 14:46:06 INFO     function: check_get_parent_fault_names, a/b tests PASS
2025-10-07 14:46:06 INFO     function: check_color_scale, a/b tests PASS
```