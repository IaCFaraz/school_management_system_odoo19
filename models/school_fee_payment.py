# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class SchoolFeePayment(models.Model):
    _name = 'school.fee.payment'
    _description = 'Fee Payment'
    _order = 'payment_date desc'

    name = fields.Char(string='Receipt Number', readonly=True, copy=False, default='New')
    student_id = fields.Many2one('school.student', string='Student', required=True)
    fee_structure_id = fields.Many2one('school.fee.structure', string='Fee Structure')
    installment_id = fields.Many2one(
        'school.fee.installment', string='Installment', copy=False,
        ondelete='set null', index=True,
    )
    fee_amount = fields.Monetary(string='Fee', currency_field='currency_id')
    discount = fields.Monetary(string='Discount', currency_field='currency_id')
    net_fee = fields.Monetary(
        string='Net Fee',
        currency_field='currency_id',
        compute='_compute_net_fee',
        store=True,
    )
    amount = fields.Monetary(string='Amount', currency_field='currency_id')
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id,
    )
    payment_date = fields.Date(string='Payment Date', default=fields.Date.today)
    payment_method = fields.Selection([
        ('cash', 'Cash'),
        ('bank_transfer', 'Bank Transfer'),
        ('cheque', 'Cheque'),
        ('online', 'Online'),
    ], string='Payment Method', default='cash')
    reference = fields.Char(string='Reference')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft')
    note = fields.Char(string='Notes')

    @api.depends('fee_amount', 'discount')
    def _compute_net_fee(self):
        for rec in self:
            rec.net_fee = (rec.fee_amount or 0.0) - (rec.discount or 0.0)

    @api.constrains('fee_amount', 'discount')
    def _check_discount(self):
        for rec in self:
            if rec.discount < 0:
                raise ValidationError(_("Discount cannot be negative."))
            if rec.discount > rec.fee_amount:
                raise ValidationError(_("Discount cannot be greater than the fee."))

    @api.constrains('installment_id', 'student_id')
    def _check_installment_student(self):
        for rec in self:
            if rec.installment_id and rec.installment_id.student_id != rec.student_id:
                raise ValidationError(_("The installment belongs to a different student."))

    @api.onchange('installment_id')
    def _onchange_installment(self):
        inst = self.installment_id
        if not inst:
            return
        self.student_id = inst.student_id
        self.fee_amount = inst.fee_amount
        self.discount = inst.discount
        self.amount = inst.net_fee
        self.currency_id = inst.currency_id

    @api.onchange('fee_structure_id', 'student_id')
    def _onchange_fee_structure(self):
        structure = self.fee_structure_id
        if not structure or self.installment_id:
            return
        self.fee_amount = structure.amount
        self.currency_id = structure.currency_id
        discount = 0.0
        # Student's special discount applies to the tuition fee.
        if (self.student_id and self.student_id.special_discount
                and structure.fee_type == 'tuition'):
            discount = min(self.student_id.special_discount, structure.amount)
        self.discount = discount
        self.amount = self.fee_amount - self.discount

    @api.onchange('fee_amount', 'discount')
    def _onchange_fee_discount(self):
        self.amount = (self.fee_amount or 0.0) - (self.discount or 0.0)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('school.fee.payment') or 'New'
        return super().create(vals_list)

    def action_pay(self):
        for record in self:
            if record.state != 'draft':
                raise UserError(_('Only draft payments can be confirmed.'))
            if record.installment_id:
                already = self.search([
                    ('installment_id', '=', record.installment_id.id),
                    ('state', '=', 'paid'),
                    ('id', '!=', record.id),
                ], limit=1)
                if already:
                    raise UserError(_(
                        "This installment (%s) is already paid by receipt %s."
                    ) % (record.installment_id.name, already.name))
            record.state = 'paid'

    def action_cancel(self):
        for record in self:
            if record.state == 'cancelled':
                raise UserError(_('Payment is already cancelled.'))
            record.state = 'cancelled'

    def action_reset_draft(self):
        for record in self:
            if record.state != 'cancelled':
                raise UserError(_('Only cancelled payments can be reset to draft.'))
            record.state = 'draft'