# -*- coding: utf-8 -*-
"""Multi-company support: adds company_id to every school model.

Each class below only extends an existing model with a company field,
so none of the existing model files need to be edited.
"""
from odoo import fields, models


def _company_field():
    return fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        index=True,
        default=lambda self: self.env.company,
    )


class SchoolAcademicYear(models.Model):
    _inherit = 'school.academic.year'
    company_id = _company_field()

    _name_company_uniq = models.Constraint(
        'UNIQUE(name, company_id)',
        'Academic year name must be unique per company!',
    )


class SchoolAttendance(models.Model):
    _inherit = 'school.attendance'
    company_id = _company_field()


class SchoolClass(models.Model):
    _inherit = 'school.class'
    company_id = _company_field()


class SchoolClassRoom(models.Model):
    _inherit = 'school.class.room'
    company_id = _company_field()


class SchoolExam(models.Model):
    _inherit = 'school.exam'
    company_id = _company_field()


class SchoolExamResult(models.Model):
    _inherit = 'school.exam.result'
    company_id = _company_field()


class SchoolFeePayment(models.Model):
    _inherit = 'school.fee.payment'
    company_id = _company_field()


class SchoolFeeStructure(models.Model):
    _inherit = 'school.fee.structure'
    company_id = _company_field()


class SchoolHostel(models.Model):
    _inherit = 'school.hostel'
    company_id = _company_field()


class SchoolHostelRoom(models.Model):
    _inherit = 'school.hostel.room'
    company_id = _company_field()


class SchoolHostelAllocation(models.Model):
    _inherit = 'school.hostel.allocation'
    company_id = _company_field()


class SchoolStudent(models.Model):
    _inherit = 'school.student'
    company_id = _company_field()


class SchoolSubject(models.Model):
    _inherit = 'school.subject'
    company_id = _company_field()


class SchoolTeacher(models.Model):
    _inherit = 'school.teacher'
    company_id = _company_field()


class SchoolTransportVehicle(models.Model):
    _inherit = 'school.transport.vehicle'
    company_id = _company_field()


class SchoolTransportRoute(models.Model):
    _inherit = 'school.transport.route'
    company_id = _company_field()