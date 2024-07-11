"""
this **data_store** package  may be merged with **solvis_store** eventually or generalised to its own repo.

It provides a hybrid class BinaryLargeObject which uses dynamodb for searching/indexing/identity** features
and s3 for the blob storage. The blob can be any binary object up to around 1GB.

Much larger file sizes can be supported by S3 but additional (multipart) download options will be needed.

Examples:

```
TODO

```
"""
