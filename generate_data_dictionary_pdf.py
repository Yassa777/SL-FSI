#!/usr/bin/env python3
"""
Generate PDF Data Dictionary for Reserve Adequacy Analysis

Creates a clean, reference-style PDF with:
- Overview metrics
- Benchmarks & formulas
- Column definitions
- Data coverage table

Run: python generate_data_dictionary_pdf.py
"""

from fpdf import FPDF
from pathlib import Path
import pandas as pd
from datetime import datetime

# Paths
OUTPUT_PATH = Path("DOCS/DATA_DICTIONARY_RESERVE_ADEQUACY.pdf")
DATA_DIR = Path("data/external")


class DataDictionaryPDF(FPDF):
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=15)

    def header(self):
        self.set_font('Helvetica', 'B', 9)
        self.set_text_color(100, 100, 100)
        self.cell(0, 8, 'SL-FSI Reserve Adequacy - Data Dictionary', align='L')
        self.cell(0, 8, 'January 2026', align='R', ln=True)
        self.set_draw_color(200, 200, 200)
        self.line(10, 15, 200, 15)
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', '', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Page {self.page_no()}', align='C')

    def section_title(self, title):
        self.set_font('Helvetica', 'B', 14)
        self.set_text_color(0, 51, 102)
        self.cell(0, 10, title, ln=True)
        self.ln(2)

    def subsection_title(self, title):
        self.set_font('Helvetica', 'B', 11)
        self.set_text_color(51, 51, 51)
        self.cell(0, 8, title, ln=True)
        self.ln(1)

    def body_text(self, text):
        self.set_font('Helvetica', '', 10)
        self.set_text_color(0, 0, 0)
        self.multi_cell(0, 5, text)
        self.ln(2)

    def code_block(self, text):
        self.set_font('Courier', '', 9)
        self.set_fill_color(245, 245, 245)
        self.set_text_color(51, 51, 51)
        self.multi_cell(0, 5, text, fill=True)
        self.ln(3)

    def add_table(self, headers, data, col_widths=None):
        """Add a table with headers and data rows."""
        if col_widths is None:
            col_widths = [190 / len(headers)] * len(headers)

        # Header row
        self.set_font('Helvetica', 'B', 9)
        self.set_fill_color(240, 240, 240)
        self.set_text_color(0, 0, 0)
        for i, header in enumerate(headers):
            self.cell(col_widths[i], 7, header, border=1, fill=True)
        self.ln()

        # Data rows
        self.set_font('Helvetica', '', 8)
        for row in data:
            for i, cell in enumerate(row):
                self.cell(col_widths[i], 6, str(cell)[:50], border=1)
            self.ln()
        self.ln(3)


def generate_pdf():
    pdf = DataDictionaryPDF()
    pdf.add_page()

    # =========================================================================
    # TITLE
    # =========================================================================
    pdf.set_font('Helvetica', 'B', 20)
    pdf.set_text_color(0, 51, 102)
    pdf.cell(0, 15, 'Data Dictionary', ln=True, align='C')
    pdf.set_font('Helvetica', '', 12)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 8, 'Reserve Adequacy Threshold Analysis', ln=True, align='C')
    pdf.ln(10)

    # =========================================================================
    # OVERVIEW
    # =========================================================================
    pdf.section_title('1. Overview')

    # Key metrics table
    overview_data = [
        ['Primary Source', 'Central Bank of Sri Lanka (CBSL)'],
        ['Data Range', '1995 - 2025 (varies by series)'],
        ['Key Event', 'April 12, 2022 - Sovereign Default'],
        ['Research Question', 'Reserve threshold signaling crisis inevitability'],
    ]
    pdf.add_table(['Parameter', 'Value'], overview_data, [50, 140])

    # Crisis timeline
    pdf.subsection_title('Crisis Timeline')
    timeline_data = [
        ['2019-04-21', 'Easter Sunday bombings'],
        ['2020-03-01', 'COVID-19 pandemic begins'],
        ['2021-03-01', 'PBOC swap activated ($1.5B)'],
        ['2021-08-01', 'NFA turns negative'],
        ['2022-04-12', 'Sovereign default announced'],
        ['2023-03-20', 'IMF EFF approved'],
    ]
    pdf.add_table(['Date', 'Event'], timeline_data, [35, 155])

    # =========================================================================
    # BENCHMARKS & METRICS
    # =========================================================================
    pdf.section_title('2. Benchmarks & Metrics')

    # Import Cover
    pdf.subsection_title('2.1 Import Cover Ratio')
    pdf.code_block('Import Cover (months) = Gross Reserves (USD) / Monthly Imports (USD)')
    threshold_data = [
        ['Comfortable', '>= 6 months', 'Adequate buffer'],
        ['IMF Minimum', '>= 3 months', 'Minimum acceptable'],
        ['Warning', '< 2 months', 'Elevated risk'],
        ['Critical', '< 1 month', 'Imminent crisis'],
    ]
    pdf.add_table(['Level', 'Threshold', 'Interpretation'], threshold_data, [35, 40, 115])

    # Greenspan-Guidotti
    pdf.subsection_title('2.2 Greenspan-Guidotti Ratio')
    pdf.code_block('GG Ratio = Gross Reserves (USD) / Short-term External Debt (USD)')
    gg_data = [
        ['Adequate', '>= 1.0', 'Can cover all ST debt'],
        ['Near-breach', '1.0 - 1.5', 'Elevated rollover risk'],
        ['Breach', '< 1.0', 'Cannot cover ST debt'],
    ]
    pdf.add_table(['Level', 'Threshold', 'Interpretation'], gg_data, [35, 40, 115])

    # IMF ARA
    pdf.subsection_title('2.3 IMF ARA Metric')
    pdf.code_block('ARA = 5% x Exports + 5% x M2(USD) + 30% x ST Debt + 15% x Portfolio Liab.')
    ara_components = [
        ['Annual Exports', '5%', 'Sum quarterly x 4'],
        ['Broad Money M2', '5%', 'Convert LKR to USD'],
        ['Short-term Debt', '30%', 'Direct (quarterly)'],
        ['Portfolio Liabilities', '15%', 'Equity + Debt from IIP'],
    ]
    pdf.add_table(['Component', 'Weight', 'Transformation'], ara_components, [50, 25, 115])

    ara_threshold = [
        ['Comfortable', '>= 150%'],
        ['Adequate', '100-150%'],
        ['Breach', '< 100%'],
    ]
    pdf.add_table(['Level', 'ARA Ratio'], ara_threshold, [50, 140])

    # Net Usable Reserves
    pdf.subsection_title('2.4 Net Usable Reserves')
    pdf.code_block('Net Usable = Gross Reserves - PBOC Swap ($1.5B) - Predetermined Drains')

    # =========================================================================
    # COLUMN DEFINITIONS
    # =========================================================================
    pdf.add_page()
    pdf.section_title('3. Column Definitions')

    # Reserve Assets
    pdf.subsection_title('3.1 Reserve Assets (reserve_assets_monthly_cbsl.csv)')
    reserve_cols = [
        ['gross_reserves_usd_m', 'Total official reserve assets', 'USD mn'],
        ['fx_reserves_usd_m', 'Foreign currency reserves', 'USD mn'],
        ['imf_position_usd_m', 'Reserve position in IMF', 'USD mn'],
        ['sdrs_usd_m', 'Special Drawing Rights', 'USD mn'],
        ['gold_usd_m', 'Monetary gold holdings', 'USD mn'],
        ['other_reserves_usd_m', 'Other reserve assets', 'USD mn'],
    ]
    pdf.add_table(['Column', 'Definition', 'Unit'], reserve_cols, [55, 100, 35])

    # External Debt
    pdf.subsection_title('3.2 External Debt (external_debt_usd_quarterly.csv)')
    debt_cols = [
        ['govt_total_usd_m', 'Total government external debt', 'USD mn'],
        ['govt_short_term_usd_m', 'Government ST external debt (GG denom.)', 'USD mn'],
        ['govt_long_term_usd_m', 'Government LT external debt', 'USD mn'],
        ['central_bank_usd_m', 'Central bank external debt', 'USD mn'],
        ['total_short_term_usd_m', 'Combined ST external debt', 'USD mn'],
    ]
    pdf.add_table(['Column', 'Definition', 'Unit'], debt_cols, [55, 100, 35])

    # Trade
    pdf.subsection_title('3.3 Trade & External Flows')
    trade_cols = [
        ['imports_usd_m', 'Monthly merchandise imports (CIF)', 'USD mn'],
        ['exports_usd_m', 'Monthly merchandise exports (FOB)', 'USD mn'],
        ['tourism_earnings_usd_m', 'Monthly tourism receipts', 'USD mn'],
        ['remittances_usd_m', 'Workers remittance inflows', 'USD mn'],
        ['cse_net_usd_m', 'Net CSE portfolio flows', 'USD mn'],
    ]
    pdf.add_table(['Column', 'Definition', 'Unit'], trade_cols, [55, 100, 35])

    # Monetary
    pdf.subsection_title('3.4 Monetary Aggregates')
    monetary_cols = [
        ['reserve_money_m0_lkr_m', 'Reserve money (M0)', 'LKR mn'],
        ['broad_money_m2_lkr_m', 'Broad money (M2) - for ARA calc', 'LKR mn'],
        ['money_multiplier_m1', 'M1 money multiplier', 'Ratio'],
    ]
    pdf.add_table(['Column', 'Definition', 'Unit'], monetary_cols, [55, 100, 35])

    # NFA
    pdf.subsection_title('3.5 Net Foreign Assets')
    nfa_cols = [
        ['nfa_monetary_auth_lkr_b', 'NFA of Monetary Authorities (CBSL)', 'LKR bn'],
        ['nfa_comm_banks_total_lkr_b', 'NFA of Commercial Banks (Total)', 'LKR bn'],
        ['nfa_comm_banks_dbu_lkr_b', 'NFA of Commercial Banks (DBUs)', 'LKR bn'],
        ['nfa_comm_banks_obu_lkr_b', 'NFA of Commercial Banks (OBUs)', 'LKR bn'],
    ]
    pdf.add_table(['Column', 'Definition', 'Unit'], nfa_cols, [55, 100, 35])
    pdf.body_text('NFA = Foreign Assets - Foreign Liabilities. Negative NFA indicates liabilities exceed assets.')

    # =========================================================================
    # DATA COVERAGE
    # =========================================================================
    pdf.add_page()
    pdf.section_title('4. Data Coverage')

    coverage_data = [
        ['Reserve Assets', 'Monthly', 'Nov 2013', 'Dec 2025', 'reserve_assets_monthly_cbsl.csv'],
        ['Central Govt Debt', 'Quarterly', 'Dec 2000', 'Q3 2025', 'central_govt_debt_quarterly.csv'],
        ['External Debt (USD)', 'Quarterly', 'Q4 2012', 'Q3 2025', 'external_debt_usd_quarterly.csv'],
        ['IIP', 'Quarterly', 'Q4 2012', 'Q3 2025', 'iip_quarterly_2025.csv'],
        ['Monetary Aggregates', 'Monthly', 'Dec 1995', 'Sep 2025', 'monetary_aggregates_monthly.csv'],
        ['Monthly Imports', 'Monthly', 'Jan 2007', 'Nov 2025', 'monthly_imports_usd.csv'],
        ['Monthly Exports', 'Monthly', 'Jan 2007', 'Nov 2025', 'monthly_exports_usd.csv'],
        ['Tourism Earnings', 'Monthly', 'Jan 2009', 'Nov 2025', 'tourism_earnings_monthly.csv'],
        ['Remittances', 'Monthly', 'Jan 2009', 'Nov 2025', 'remittances_monthly.csv'],
        ['CSE Flows', 'Monthly', 'Jan 2012', 'Dec 2025', 'cse_flows_monthly.csv'],
        ['NFA (Money Supply)', 'Monthly', 'Jan 2005', 'Dec 2017', 'money_supply_monthly_clean.csv'],
        ['NFA + REER', 'Monthly', 'Jan 2021', 'Feb 2024', 'D14_reer_nfa.csv'],
    ]
    pdf.add_table(
        ['Dataset', 'Freq', 'Start', 'End', 'File'],
        coverage_data,
        [38, 20, 22, 22, 88]
    )

    # Data gaps
    pdf.subsection_title('Known Data Gaps')
    gaps_data = [
        ['Gross Reserves pre-2013', 'Use IIP quarterly or CBSL Annual Reports'],
        ['NFA breakdown pre-2021', 'Use aggregate NFA from money supply'],
        ['Quarterly vs Monthly debt', 'Interpolate or quarterly-only analysis'],
    ]
    pdf.add_table(['Gap', 'Mitigation'], gaps_data, [60, 130])

    # =========================================================================
    # REFERENCES
    # =========================================================================
    pdf.section_title('5. CBSL Table References')

    refs_data = [
        ['Table 2.02', 'Monthly Exports'],
        ['Table 2.04', 'Monthly Imports'],
        ['Table 2.12', 'Outstanding External Debt'],
        ['Table 2.14.1', 'Tourism Earnings'],
        ['Table 2.14.2', 'Workers Remittances'],
        ['Table 2.14.3', 'CSE Portfolio Flows'],
        ['Table 2.15.2', 'Reserve Data Template (Historical)'],
        ['Table 4.02', 'Monetary Aggregates'],
        ['Table 4.11', 'Reserve Money, Multipliers, Velocity'],
    ]
    pdf.add_table(['Table', 'Description'], refs_data, [35, 155])

    pdf.body_text('Source: https://www.cbsl.gov.lk/en/statistics/statistical-tables')

    # =========================================================================
    # SAVE
    # =========================================================================
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(OUTPUT_PATH))
    print(f"✓ PDF generated: {OUTPUT_PATH}")


if __name__ == "__main__":
    generate_pdf()
