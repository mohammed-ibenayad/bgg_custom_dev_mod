# -*- coding: utf-8 -*-

import logging
from odoo import api, models

_logger = logging.getLogger(__name__)


class MailActivity(models.Model):
    _inherit = 'mail.activity'

    def write(self, vals):
        """Override write to trigger automation when activity is marked as done"""
        result = super(MailActivity, self).write(vals)

        # Check if state was changed to 'done'
        if 'state' in vals:
            for record in self:
                self._add_tag_on_completion(record)

        return result

    def _add_tag_on_completion(self, record):
        """
        Add Tag on Activity Completion - Automation Rule
        Adds "Call2" tag to calendar event when Call2 activity is marked as done
        """
        try:
            if record.activity_type_id.name == 'Call2' and record.state == 'done':
                _logger.info("Processing Call2 activity completion for activity ID %s", record.id)

                # Get or create call2 tag
                Call2_tag = self.env['calendar.event.type'].search([('name', '=', 'Call2')], limit=1)

                if not Call2_tag:
                    Call2_tag = self.env['calendar.event.type'].create({'name': 'Call2'})
                    _logger.info("Created new Call2 tag (ID: %s)", Call2_tag.id)

                # Add tag to the calendar event
                calendar_event = record.calendar_event_id

                if calendar_event:
                    # Check if tag is already added to avoid duplicate
                    if Call2_tag.id not in calendar_event.categ_ids.ids:
                        calendar_event.write({'categ_ids': [(4, Call2_tag.id)]})
                        _logger.info("Added Call2 tag to calendar event ID %s", calendar_event.id)
                    else:
                        _logger.info("Call2 tag already exists on calendar event ID %s", calendar_event.id)
                else:
                    _logger.warning("No calendar event linked to Call2 activity ID %s", record.id)

        except Exception as e:
            _logger.error("Add Call2 Tag on Activity Completion - Error processing activity ID %s: %s",
                        record.id, str(e), exc_info=True)
