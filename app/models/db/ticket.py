# coding: utf-8

from app.models import db


class Ticket(db.Model):
    __tablename__ = 'ticket'

    id = db.Column(db.Integer, primary_key=True)
    provider_type = db.Column(db.String(length=16))
    provider_object = db.Column(db.String(length=64))
    params = db.Column(db.JSON)
    extra_params = db.Column(db.JSON)
    submitter = db.Column(db.String(length=32))
    reason = db.Column(db.String(length=128))
    is_approved = db.Column(db.Boolean)
    is_rejected = db.Column(db.Boolean)
    approved_by = db.Column(db.String(length=32))
    annotation = db.Column(db.JSON)
    created_at = db.Column(db.DateTime)
    approved_at = db.Column(db.DateTime)
    executed_at = db.Column(db.DateTime)
