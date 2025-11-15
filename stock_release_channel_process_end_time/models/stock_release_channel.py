# Copyright 2023 ACSONE SA/NV
# Copyright 2024 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from datetime import timedelta

from odoo import api, fields, models
from odoo.osv.expression import AND

from odoo.addons.base.models.res_partner import _tz_get

from ..utils import float_to_time, time_to_datetime


class StockReleaseChannel(models.Model):
    _inherit = "stock.release.channel"
    _order = "process_end_date, sequence, id"

    process_end_time = fields.Float(
        help="Fill in this to indicates when this channel release process would "
        "be ended. This information will be used to compute the channel pickings "
        "scheduled date at channel awaking.",
    )
    # TODO: move this field to stock_release_channel, make stored and rename to tz
    process_end_time_tz = fields.Selection(
        selection=_tz_get,
        compute="_compute_process_end_time_tz",
        help="Technical field to compute the timezone for the process end time.",
    )
    process_end_time_can_edit = fields.Boolean(
        compute="_compute_process_end_time_can_edit",
        help="Technical field in order to know if user can edit the end date in views",
    )
    process_end_date = fields.Datetime(
        compute="_compute_process_end_date",
        store=True,
        readonly=False,
        help="This is the end date for this window of opened channel.",
    )

    @api.depends_context("uid")
    def _compute_process_end_time_can_edit(self):
        if self.env.user.has_group("stock.group_stock_manager"):
            self.update({"process_end_time_can_edit": True})
        else:
            self.update({"process_end_time_can_edit": False})

    @api.depends("state", "process_end_time")
    def _compute_process_end_date(self):
        for channel in self:
            if channel.state == "asleep":
                channel.process_end_date = False
            # otherwise we check if a date is not already set (manually)
            elif channel.process_end_date:
                continue
            elif channel.process_end_time:
                end = time_to_datetime(
                    float_to_time(
                        channel.process_end_time,
                    ),
                    tz=channel.process_end_time_tz,
                )
                while end < fields.Datetime.now():
                    end += timedelta(days=1)
                channel.process_end_date = end
            else:
                channel.process_end_date = False

    @api.depends("warehouse_id.partner_id.tz")
    @api.depends_context("company")
    def _compute_process_end_time_tz(self):
        # As the time is timezone-agnostic, we use the channel warehouse adress timezone
        # or the company one, either it will be considered as UTC
        company_tz = self.env.company.partner_id.tz
        for channel in self:
            channel.process_end_time_tz = (
                channel.warehouse_id.partner_id.tz or company_tz or "UTC"
            )

    @property
    def _field_picking_domain_release_ready_extra(self):
        domain = super()._field_picking_domain_release_ready_extra
        if len(self) != 1:
            domain_scheduled_date = [
                "scheduled_date_prior_to_channel_end_date_search",
                "=",
                True,
            ]
            domain = AND([domain, domain_scheduled_date])
        elif self.process_end_date:
            wh_tz = self.process_end_time_tz
            end_date_tz = self._localize(self.process_end_date, tz=wh_tz)
            end_date_tomorrow_tz = fields.Datetime.add(end_date_tz, days=1)
            end_date_tomorrow = self._naive(end_date_tomorrow_tz, reset_time=True)
            domain_scheduled_date = [
                ("scheduled_date", "<", end_date_tomorrow),
            ]
            domain = AND([domain, domain_scheduled_date])
        return domain

    def _get_expected_date(self):
        # Use channel process end date
        self.ensure_one()
        enabled_update_scheduled_date = bool(
            self.env["ir.config_parameter"]
            .sudo()
            .get_param(
                "stock_release_channel_process_end_time.stock_release_use_channel_end_date"
            )
        )
        if enabled_update_scheduled_date:
            return self.process_end_date
        return super()._get_expected_date()
