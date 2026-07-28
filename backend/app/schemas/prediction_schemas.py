"""
Prediction Marshmallow schemas.
"""

from marshmallow import Schema, fields, validate, validates, ValidationError


class PredictionInputSchema(Schema):
    """POST /predictions/"""
    # Required pollutants
    pm25 = fields.Float(required=True,  validate=validate.Range(min=0, max=1000))
    pm10 = fields.Float(required=True,  validate=validate.Range(min=0, max=2000))
    no2  = fields.Float(required=True,  validate=validate.Range(min=0, max=2000))
    so2  = fields.Float(required=True,  validate=validate.Range(min=0, max=1500))
    co   = fields.Float(required=True,  validate=validate.Range(min=0, max=100))
    o3   = fields.Float(required=True,  validate=validate.Range(min=0, max=500))

    # Optional pollutants
    nh3  = fields.Float(load_default=None, validate=validate.Range(min=0, max=500))

    # Optional weather
    temperature    = fields.Float(load_default=None, validate=validate.Range(min=-80, max=60))
    humidity       = fields.Float(load_default=None, validate=validate.Range(min=0,  max=100))
    wind_speed     = fields.Float(load_default=None, validate=validate.Range(min=0,  max=200))
    wind_direction = fields.Float(load_default=None, validate=validate.Range(min=0,  max=360))
    pressure       = fields.Float(load_default=None, validate=validate.Range(min=800, max=1100))

    # Optional metadata
    city = fields.Str(load_default=None, validate=validate.Length(max=100))


class BatchPredictionSchema(Schema):
    """POST /predictions/batch"""
    records = fields.List(
        fields.Dict(),
        required=True,
        validate=validate.Length(min=1, max=500,
                                 error="Records must contain 1-500 items.")
    )


class ExplainSchema(Schema):
    """POST /predictions/explain"""
    features = fields.Dict(required=True)
    methods  = fields.List(
        fields.Str(validate=validate.OneOf(["shap", "lime"])),
        load_default=["shap", "lime"]
    )
