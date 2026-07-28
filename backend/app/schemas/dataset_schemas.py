"""
Dataset Marshmallow schemas.
"""

from marshmallow import Schema, fields, validate


class DatasetFetchSchema(Schema):
    """POST /datasets/fetch-openaq"""
    city      = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    country   = fields.Str(required=True, validate=validate.Length(min=2, max=3))
    date_from = fields.Date(required=True, format="%Y-%m-%d")
    date_to   = fields.Date(required=True, format="%Y-%m-%d")
    limit     = fields.Int(load_default=10000, validate=validate.Range(min=1, max=50000))


class DatasetUploadSchema(Schema):
    """Multipart form for POST /datasets/upload"""
    name        = fields.Str(required=True, validate=validate.Length(min=1, max=255))
    description = fields.Str(load_default="")
    location    = fields.Str(load_default="")
    is_public   = fields.Bool(load_default=False)
