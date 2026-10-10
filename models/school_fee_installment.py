# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class SchoolFeeInstallment(models.Model):
    _name = 'school.fee.installment'
    _description = 'Fee Installment'
    _order = 'student_id, due_date, id'

    name = fields.Char(string='Period', required=True)
    student_id = fields.Many2one(
        'school.student', string='Student', required=True,
        ondelete='cascade', index=True,
    )
    company_id = fields.Many2one(
        'res.company', string='Company',
        related='student_id.company_id', store=True, index=True,
    )
    currency_id = fields.Many2one(
        'res.currency', string='Currency',
        related='student_id.currency_id', store=True,
    )
    months = fields.Integer(string='Months Covered', default=1)
    due_date = fields.Date(string='Due Date')
    fee_amount = fields.Monetary(string='Fee', currency_field='currency_id')
    discount = fields.Monetary(string='Discount', currency_field='currency_id')
    net_fee = fields.Monetary(
        string='Net Fee', currency_field='currency_id',
        compute='_compute_net_fee', store=True,
    )
    payment_ids = fields.One2many(
        'school.fee.payment', 'installment_id', string='Payments',
    )
    payment_ref = fields.Char(string='Receipt', compute='_compute_payment_info')
    paid_date = fields.Date(string='Paid On', compute='_compute_payment_info')
    state = fields.Selection([
        ('unpaid', 'Unpaid'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
    ], string='Status', compute='_compute_state')

    @api.depends('fee_amount', 'discount')
    def _compute_net_fee(self):
        for rec in self:
            rec.net_fee = (rec.fee_amount or 0.0) - (rec.discount or 0.0)

    @api.depends('payment_ids.state', 'payment_ids.name', 'payment_ids.payment_date')
    def _compute_payment_info(self):
        for rec in self:
            paid = rec.payment_ids.filtered(lambda p: p.state == 'paid')
            rec.payment_ref = ', '.join(paid.mapped('name'))
            rec.paid_date = paid[:1].payment_date if paid else False

    @api.depends('payment_ids.state', 'due_date')
    def _compute_state(self):
        today = fields.Date.context_today(self)
        for rec in self:
            if rec.payment_ids.filtered(lambda p: p.state == 'paid'):
                rec.state = 'paid'
            elif rec.due_date and rec.due_date < today:
                rec.state = 'overdue'
            else:
                rec.state = 'unpaid'

    def action_pay(self):
        """Create (or reopen) the draft payment for this installment."""
        self.ensure_one()
        if self.state == 'paid':
            raise UserError(_("This installment is already paid."))
        payment = self.payment_ids.filtered(lambda p: p.state == 'draft')[:1]
        if not payment:
            structure = self.env['school.fee.structure'].search([
                ('class_id', '=', self.student_id.class_id.id),
                ('fee_type', '=', 'tuition'),
            ], limit=1)
            payment = self.env['school.fee.payment'].create({
                'student_id': self.student_id.id,
                'installment_id': self.id,
                'fee_structure_id': structure.id,
                'fee_amount': self.fee_amount,
                'discount': self.discount,
                'amount': self.net_fee,
                'currency_id': self.currency_id.id,
                'company_id': self.company_id.id,
                'note': self.name,
            })
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'school.fee.payment',
            'res_id': payment.id,
            'view_mode': 'form',
            'target': 'current',
        }