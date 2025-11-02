# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Contracts Management',
    'version': '1.0',
    'category': 'Document Management',
    'summary': 'Manage contract templates and contracts',
    'description': """
        Contracts Management
        ====================
        Simple contract templates and contracts management system.
    """,
    'author': 'Your Company',
    'license': 'LGPL-3',
    'depends': ['base', 'web'],
    'data': [
        'security/ir.model.access.csv',
        'views/contract_template_views.xml',
        'views/menu_views.xml',
        'data/contract_data.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
