# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import date
from dateutil.relativedelta import relativedelta


class SchoolStudent(models.Model):
    _name = 'school.student'
    _description = 'School Student'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    name = fields.Char(string='Student Name', required=True, tracking=True)
    code = fields.Char(string='Student ID', readonly=True, copy=False, default='New')
    class_id = fields.Many2one('school.class', string='Class', required=True, tracking=True)
    academic_year_id = fields.Many2one(
        'school.academic.year',
        string='Academic Year',
        related='class_id.academic_year_id',
        store=True,
    )
    partner_id = fields.Many2one('res.partner', string='Contact')
    date_of_birth = fields.Date(string='Date of Birth')
    age = fields.Integer(string='Age', compute='_compute_age', store=False)
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ], string='Gender')
    blood_group = fields.Selection([
        ('A+', 'A+'), ('A-', 'A-'),
        ('B+', 'B+'), ('B-', 'B-'),
        ('O+', 'O+'), ('O-', 'O-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'),
    ], string='Blood Group')
    nationality = fields.Many2one('res.country', string='Nationality')
    religion = fields.Char(string='Religion')
    phone = fields.Char(string='Phone')
    email = fields.Char(string='Email')
    address = fields.Text(string='Address')
    image = fields.Binary(string='Photo')
    father_name = fields.Char(string="Father's Name")
    father_phone = fields.Char(string="Father's Phone")
    father_occupation = fields.Char(string="Father's Occupation")
    mother_name = fields.Char(string="Mother's Name")
    mother_phone = fields.Char(string="Mother's Phone")
    guardian_name = fields.Char(string='Guardian Name')
    guardian_phone = fields.Char(string='Guardian Phone')
    guardian_relation = fields.Char(string='Guardian Relation')
    admission_date = fields.Date(string='Admission Date', default=fields.Date.today)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('enrolled', 'Enrolled'),
        ('active', 'Active'),
        ('graduated', 'Graduated'),
        ('expelled', 'Expelled'),
    ], string='Status', default='draft', tracking=True)
    fee_payment_ids = fields.One2many('school.fee.payment', 'student_id', string='Fee Payments')
    exam_result_ids = fields.One2many('school.exam.result', 'student_id', string='Exam Results')
    attendance_ids = fields.One2many('school.attendance', 'student_id', string='Attendance')
    hostel_allocation_id = fields.Many2one('school.hostel.allocation', string='Hostel Allocation')
    transport_route_id = fields.Many2one('school.transport.route', string='Transport Route')
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id,
    )
    class_fee = fields.Monetary(
        string='Monthly Fee',
        compute='_compute_class_fee',
        currency_field='currency_id',
        store=False,
    )
    special_discount = fields.Monetary(
        string='Monthly Special Discount',
        currency_field='currency_id',
        tracking=True,
    )
    net_fee = fields.Monetary(
        string='Monthly Net Fee',
        compute='_compute_net_fee',
        currency_field='currency_id',
        store=False,
    )
    payment_plan = fields.Selection([
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly (3 months)'),
        ('half_yearly', 'Half-Yearly (6 months)'),
        ('yearly', 'Yearly'),
    ], string='Payment Plan', default='monthly', tracking=True)
    installment_ids = fields.One2many(
        'school.fee.installment', 'student_id', string='Installments',
    )
    fee_paid = fields.Monetary(
        string='Total Fees Paid',
        compute='_compute_fees',
        currency_field='currency_id',
        store=False,
    )
    fee_due = fields.Monetary(
        string='Fees Due',
        compute='_compute_fees',
        currency_field='currency_id',
        store=False,
    )
    note = fields.Text(string='Notes')

    @api.depends('date_of_birth')
    def _compute_age(self):
        today = date.today()
        for record in self:
            if record.date_of_birth:
                dob = record.date_of_birth
                record.age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            else:
                record.age = 0

    @api.depends('class_id')
    def _compute_class_fee(self):
        Structure = self.env['school.fee.structure']
        for record in self:
            structure = Structure
            if record.class_id:
                structure = Structure.search([
                    ('class_id', '=', record.class_id.id),
                    ('fee_type', '=', 'tuition'),
                ], limit=1)
            record.class_fee = structure.amount if structure else 0.0

    @api.depends('class_fee', 'special_discount')
    def _compute_net_fee(self):
        for record in self:
            record.net_fee = (record.class_fee or 0.0) - (record.special_discount or 0.0)

    @api.constrains('special_discount', 'class_id')
    def _check_special_discount(self):
        for record in self:
            if record.special_discount < 0:
                raise ValidationError(_("Special discount cannot be negative."))
            if record.special_discount > record.class_fee:
                raise ValidationError(_("Special discount cannot be greater than the class fee."))

    @api.depends('fee_payment_ids', 'fee_payment_ids.amount', 'fee_payment_ids.state',
                 'class_id', 'special_discount',
                 'installment_ids.net_fee', 'installment_ids.state')
    def _compute_fees(self):
        for record in self:
            paid_payments = record.fee_payment_ids.filtered(lambda p: p.state == 'paid')
            record.fee_paid = sum(paid_payments.mapped('amount'))
            if record.installment_ids:
                record.fee_due = sum(
                    inst.net_fee for inst in record.installment_ids
                    if inst.state != 'paid'
                )
            else:
                all_structures = self.env['school.fee.structure'].search([
                    ('class_id', '=', record.class_id.id),
                ])
                total_due = sum(all_structures.mapped('amount')) - (record.special_discount or 0.0)
                record.fee_due = max(0, total_due - record.fee_paid)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('code', 'New') == 'New':
                vals['code'] = self.env['ir.sequence'].next_by_code('school.student') or 'New'
        return super().create(vals_list)

    def action_enroll(self):
        for record in self:
            if record.state != 'draft':
                raise UserError(_('Only draft students can be enrolled.'))
            record.state = 'enrolled'

    def action_activate(self):
        for record in self:
            if record.state != 'enrolled':
                raise UserError(_('Only enrolled students can be activated.'))
            record.state = 'active'

    def action_graduate(self):
        for record in self:
            if record.state not in ('active', 'enrolled'):
                raise UserError(_('Only active or enrolled students can be graduated.'))
            record.state = 'graduated'

    def action_expel(self):
        for record in self:
            if record.state == 'expelled':
                raise UserError(_('Student is already expelled.'))
            record.state = 'expelled'

    def action_reset(self):
        for record in self:
            record.state = 'draft'

    def action_generate_installments(self):
        """Build the installments of the selected Payment Plan.

        The class fee is a MONTHLY fee. A plan simply groups months:
        monthly = 12 x 1 month, quarterly = 4 x 3, half-yearly = 2 x 6,
        yearly = 1 x 12. Fee and special discount are multiplied by the
        months each installment covers.
        """
        months_by_plan = {
            'monthly': 1, 'quarterly': 3, 'half_yearly': 6, 'yearly': 12,
        }
        Installment = self.env['school.fee.installment'].sudo()
        for record in self:
            if not record.class_fee:
                raise UserError(_(
                    "No Tuition fee found for this student's class. Create a "
                    "Tuition fee structure for the class first."
                ))
            if record.installment_ids.filtered(lambda i: i.state == 'paid'):
                raise UserError(_(
                    "Some installments are already paid, so the plan cannot "
                    "be regenerated."
                ))
            step = months_by_plan[record.payment_plan]
            start = (
                record.academic_year_id.date_start
                or record.admission_date
                or fields.Date.today()
            )
            record.installment_ids.sudo().unlink()
            vals_list = []
            for index in range(12 // step):
                period_start = start + relativedelta(months=index * step)
                period_end = period_start + relativedelta(months=step - 1)
                if step == 1:
                    label = period_start.strftime('%b %Y')
                else:
                    label = '%s - %s' % (
                        period_start.strftime('%b %Y'),
                        period_end.strftime('%b %Y'),
                    )
                vals_list.append({
                    'name': label,
                    'student_id': record.id,
                    'months': step,
                    'due_date': period_start,
                    'fee_amount': record.class_fee * step,
                    'discount': (record.special_discount or 0.0) * step,
                })
            Installment.create(vals_list)
        return True

    def action_view_exams(self):
        return {
            'name': _('Exam Results'),
            'type': 'ir.actions.act_window',
            'res_model': 'school.exam.result',
            'view_mode': 'list,form',
            'domain': [('student_id', '=', self.id)],
        }

    def action_view_fees(self):
        return {
            'name': _('Fee Payments'),
            'type': 'ir.actions.act_window',
            'res_model': 'school.fee.payment',
            'view_mode': 'list,form',
            'domain': [('student_id', '=', self.id)],
        }

    def action_view_attendance(self):
        return {
            'name': _('Attendance'),
            'type': 'ir.actions.act_window',
            'res_model': 'school.attendance',
            'view_mode': 'list,form',
            'domain': [('student_id', '=', self.id)],
        }