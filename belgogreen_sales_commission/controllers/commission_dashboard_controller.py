# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import json


class CommissionDashboardController(http.Controller):

    @http.route('/commission/dashboard/data', type='json', auth='user')
    def get_dashboard_data(self):
        """API endpoint to get dashboard data"""
        dashboard = request.env['commission.dashboard']
        return dashboard.get_dashboard_data()

    @http.route('/commission/dashboard/refresh', type='json', auth='user')
    def refresh_dashboard(self):
        """Refresh dashboard data"""
        dashboard = request.env['commission.dashboard']
        return dashboard.get_dashboard_data()
