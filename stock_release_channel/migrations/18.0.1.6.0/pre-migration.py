# Copyright 2025 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>

from odoo.tools.sql import column_exists, create_column


def migrate(cr, version):
    if not column_exists(cr, "stock_picking", "delivery_date"):
        create_column(cr, "stock_picking", "delivery_date", "date")
