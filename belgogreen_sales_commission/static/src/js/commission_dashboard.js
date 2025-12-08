/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, onWillStart, onMounted, useState, useRef } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { loadJS } from "@web/core/assets";

export class CommissionDashboard extends Component {
    static template = "commission.dashboard";
    static props = ["*"];

    setup() {
        // Use refs for DOM access
        this.root = useRef("root");

        // Try to access services safely
        try {
            this.rpc = useService("rpc");
            this.orm = useService("orm");
            this.actionService = useService("action");
        } catch (e) {
            console.log("Services not available, will use fallback:", e.message);
            // Services might not be available yet, we'll use fallback
            this.rpc = null;
        }

        this.state = useState({
            data: null,
            loading: true,
            chartLoaded: false,
            error: null,
        });

        onWillStart(async () => {
            try {
                // Load Chart.js library
                await this.loadChartJS();
                console.log("Chart.js loaded successfully");
            } catch (error) {
                console.error("Error loading Chart.js:", error);
                this.state.error = error.message;
            }
        });

        onMounted(async () => {
            console.log("Component mounted, loading dashboard data...");

            // Refresh button click handler
            const refreshBtn = this.root.el?.querySelector('.dashboard_refresh');
            if (refreshBtn) {
                refreshBtn.addEventListener('click', () => this.onRefreshClick());
            }

            // Load data after DOM is ready
            try {
                if (this.rpc) {
                    await this.loadDashboardData();
                } else {
                    // If RPC not available, try alternative approach
                    await this.loadDashboardDataFallback();
                }
            } catch (error) {
                console.error("Error loading dashboard data:", error);
                this.state.error = error.message;
                this.state.loading = false;
            }
        });
    }

    async loadDashboardDataFallback() {
        // Fallback: use fetch API directly
        console.log("Using fallback method to load data...");
        try {
            const response = await fetch('/commission/dashboard/data', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    jsonrpc: "2.0",
                    method: "call",
                    params: {}
                })
            });

            console.log("Fetch response status:", response.status);

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            console.log("Raw response:", result);

            const data = result.result;

            if (!data) {
                throw new Error("No data received from server");
            }

            console.log("Dashboard data received:", data);
            this.state.data = data;

            // Add null checks before accessing nested properties
            if (data && data.kpis) {
                console.log("Updating KPIs...", data.kpis);
                this.updateKPIs(data.kpis);
            }
            if (data && data.charts) {
                console.log("Updating charts...", data.charts);
                this.updateCharts(data.charts);
            }
            if (data && data.recent && data.team) {
                console.log("Updating tables...");
                this.updateTables(data.recent, data.team);
            }

            console.log("Dashboard updated successfully!");
        } catch (error) {
            console.error('Error loading dashboard data (fallback):', error);
            this.state.error = error.message;
        } finally {
            this.state.loading = false;
        }
    }

    async loadChartJS() {
        try {
            // Load Chart.js from CDN
            if (typeof Chart === 'undefined') {
                await loadJS("https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js");
            }
            this.state.chartLoaded = true;
        } catch (error) {
            console.error('Error loading Chart.js:', error);
            this.state.chartLoaded = false;
        }
    }

    async loadDashboardData() {
        this.state.loading = true;
        try {
            const data = await this.rpc('/commission/dashboard/data', {});
            this.state.data = data;

            // Add null checks before accessing nested properties
            if (data && data.kpis) {
                this.updateKPIs(data.kpis);
            }
            if (data && data.charts) {
                this.updateCharts(data.charts);
            }
            if (data && data.recent && data.team) {
                this.updateTables(data.recent, data.team);
            }
        } catch (error) {
            console.error('Error loading dashboard data:', error);
            this.state.error = error.message;
        } finally {
            this.state.loading = false;
        }
    }

    updateKPIs(kpis) {
        // Update KPI values
        this.updateElement('#my_total', this.formatCurrency(kpis.my_total));
        this.updateElement('#my_pending', this.formatCurrency(kpis.my_pending));
        this.updateElement('#my_count', kpis.my_count);

        this.updateElement('#month_total', this.formatCurrency(kpis.my_month_total));
        this.updateElement('#month_count', kpis.my_month_count);

        this.updateElement('#team_total', this.formatCurrency(kpis.team_total));
        this.updateElement('#team_pending', this.formatCurrency(kpis.team_pending));
        this.updateElement('#team_members', kpis.team_members);

        this.updateElement('#pending_claims', kpis.pending_claims);
    }

    updateCharts(charts) {
        if (!this.state.chartLoaded || typeof Chart === 'undefined') {
            console.warn('Chart.js not loaded yet');
            return;
        }

        // Monthly Trend Chart
        this.createTrendChart(charts.monthly_trend);

        // Status Distribution Chart
        this.createStatusChart(charts.state_distribution);

        // Team Performance Chart
        this.createTeamChart(charts.team_performance);
    }

    createTrendChart(data) {
        const ctx = document.getElementById('trend_chart');
        if (!ctx || typeof Chart === 'undefined') return;

        if (window.trendChart) {
            window.trendChart.destroy();
        }

        window.trendChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.map(d => d.month),
                datasets: [{
                    label: 'Commission Amount',
                    data: data.map(d => d.amount),
                    borderColor: '#017e84',
                    backgroundColor: 'rgba(1, 126, 132, 0.1)',
                    tension: 0.4,
                    fill: true,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: (context) => {
                                return 'Amount: ' + this.formatCurrency(context.parsed.y);
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: (value) => this.formatCurrency(value)
                        }
                    }
                }
            }
        });
    }

    createStatusChart(data) {
        const ctx = document.getElementById('status_chart');
        if (!ctx || typeof Chart === 'undefined') return;

        if (window.statusChart) {
            window.statusChart.destroy();
        }

        const colors = {
            pending: '#ffc107',
            approved: '#17a2b8',
            paid: '#28a745',
            cancelled: '#dc3545'
        };

        window.statusChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: Object.keys(data).map(k => k.charAt(0).toUpperCase() + k.slice(1)),
                datasets: [{
                    data: Object.values(data),
                    backgroundColor: Object.keys(data).map(k => colors[k]),
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        position: 'bottom'
                    },
                    tooltip: {
                        callbacks: {
                            label: (context) => {
                                const label = context.label || '';
                                const value = this.formatCurrency(context.parsed);
                                return label + ': ' + value;
                            }
                        }
                    }
                }
            }
        });
    }

    createTeamChart(data) {
        const ctx = document.getElementById('team_chart');
        if (!ctx || !data || data.length === 0 || typeof Chart === 'undefined') return;

        if (window.teamChart) {
            window.teamChart.destroy();
        }

        window.teamChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.map(d => d.name),
                datasets: [{
                    label: 'Commission Amount',
                    data: data.map(d => d.amount),
                    backgroundColor: '#017e84',
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: (context) => {
                                return 'Amount: ' + this.formatCurrency(context.parsed.y);
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: (value) => this.formatCurrency(value)
                        }
                    }
                }
            }
        });
    }

    updateTables(recent, team) {
        // Update Recent Commissions Table
        const commissionsTable = document.querySelector('#recent_commissions_table tbody');
        if (commissionsTable) {
            commissionsTable.innerHTML = '';
            recent.commissions.forEach(comm => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${comm.date}</td>
                    <td>${comm.order}</td>
                    <td>${this.formatCurrency(comm.amount)}</td>
                    <td><span class="badge badge-${this.getStatusBadge(comm.state)}">${comm.state}</span></td>
                `;
                row.style.cursor = 'pointer';
                row.addEventListener('click', () => this.openCommission(comm.id));
                commissionsTable.appendChild(row);
            });
        }

        // Update Team Members Table
        const teamTable = document.querySelector('#team_members_table tbody');
        if (teamTable) {
            teamTable.innerHTML = '';
            team.members.forEach(member => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${member.name}</td>
                    <td>${member.role}</td>
                    <td>${this.formatCurrency(member.unpaid_total)}</td>
                    <td>${member.commission_count}</td>
                `;
                row.style.cursor = 'pointer';
                row.addEventListener('click', () => this.openUser(member.id));
                teamTable.appendChild(row);
            });
        }
    }

    updateElement(selector, value) {
        const element = document.querySelector(selector);
        if (element) {
            element.textContent = value;
        }
    }

    formatCurrency(value) {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD'
        }).format(value || 0);
    }

    getStatusBadge(state) {
        const badges = {
            pending: 'warning',
            approved: 'info',
            paid: 'success',
            cancelled: 'danger'
        };
        return badges[state] || 'secondary';
    }

    async onRefreshClick() {
        if (this.rpc) {
            await this.loadDashboardData();
        } else {
            await this.loadDashboardDataFallback();
        }
    }

    async openCommission(id) {
        if (this.actionService) {
            await this.actionService.doAction({
                type: 'ir.actions.act_window',
                res_model: 'sale.commission',
                res_id: id,
                views: [[false, 'form']],
                target: 'current',
            });
        }
    }

    async openUser(id) {
        if (this.actionService) {
            await this.actionService.doAction({
                type: 'ir.actions.act_window',
                res_model: 'res.users',
                res_id: id,
                views: [[false, 'form']],
                target: 'current',
            });
        }
    }
}

registry.category("actions").add("commission_dashboard", CommissionDashboard);
