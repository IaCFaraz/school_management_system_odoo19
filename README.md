# School Management System (Odoo 19)

Original module: School Management System by leapai.ai
Source: apps.odoo.com (License: LGPL-3)

## Contributor
- Muhammad Faraz Bashir: Odoo 19 fixes and new fee features

## Fixes made for Odoo 19
- Fixed external ID prefix (leapai_school_management -> school_management)
- Fixed XML syntax error in views/school_menu.xml (root menuitem)
- Academic year name is now unique per company (was unique globally)

## New features

### 1. Student special discount and class fee
- Class (monthly Tuition) fee is picked up automatically from the class fee structure
- Special discount can be set per student, Net Fee is calculated automatically
- Fee payment and receipt show Fee, Discount and Net Amount

### 2. Multi-company support
- company_id added to all school models
- Record rules so each company only sees its own records

### 3. Installment plans
- Payment plan per student: Monthly, Quarterly, Half-Yearly, Yearly
- Generate Installments builds the periods from the monthly fee and discount
- Pay button on each installment creates the payment, and the installment becomes Paid
- Installments show Unpaid / Paid / Overdue, receipt number and paid date
- Fees Due is calculated from unpaid installments
- Receipt shows the paid period

## Known limitations
- Only Tuition fee is split into installments (not transport or hostel)
- Student ID and receipt sequences are shared between companies
- No partial payments yet

## Installation
1. Clone this repo into your Odoo custom addons folder with the folder name school_management
2. Restart Odoo, then Apps -> Update Apps List
3. Install "School Management System"