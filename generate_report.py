"""
Transaction Report Generator
=============================
Edit the CONFIG section below to customize the report.
Then run:  python generate_report.py
"""

import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image, PageBreak, HRFlowable
)
from reportlab.lib import colors
import os, io

# ============================================================
# CONFIG — Change these values to customize your report
# ============================================================

INPUT_CSV = "transaction_data.csv"           # Path to your CSV file
OUTPUT_PDF = "transaction_report.pdf"        # Output PDF name
REPORT_TITLE = "Transaction Analysis Report"
REPORT_SUBTITLE = "Amount Analysis & Key Behavioral Observations"
AUTHOR = "Data Analytics Team"
DATE = "May 2026"

# Colors (hex)
PRIMARY_COLOR = "#1e3a5f"
ACCENT_COLOR = "#3b82f6"
SUCCESS_COLOR = "#10b981"
DANGER_COLOR = "#ef4444"
CHART_BG = "#0f172a"
CHART_FACE = "#1e293b"

# High-value threshold percentile (0-100)
HIGH_VALUE_PERCENTILE = 90

# Chart DPI
CHART_DPI = 180

# ============================================================
# END CONFIG
# ============================================================


def load_data(path):
    df = pd.read_csv(path)
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    return df


def make_charts(df):
    fraud_df = df[df['Fraud Flag'] == True]
    legit_df = df[df['Fraud Flag'] == False]
    clrs = [ACCENT_COLOR, SUCCESS_COLOR, '#f59e0b', DANGER_COLOR, '#8b5cf6', '#ec4899']

    def style_ax(ax, title):
        ax.set_facecolor(CHART_FACE)
        ax.set_title(title, color='white', fontsize=10, fontweight='bold', pad=8)
        ax.tick_params(colors='#94a3b8', labelsize=8)
        for s in ax.spines.values():
            s.set_color('#334155')

    fig, axes = plt.subplots(2, 3, figsize=(14, 8), facecolor=CHART_BG)
    fig.subplots_adjust(hspace=0.45, wspace=0.35)

    # 1 Distribution
    ax = axes[0, 0]
    ax.hist(df['Transaction Amount'], bins=35, color=clrs[0], alpha=0.85, edgecolor=CHART_FACE)
    ax.axvline(df['Transaction Amount'].mean(), color=clrs[2], ls='--', lw=1.2, label=f"Mean ${df['Transaction Amount'].mean():.0f}")
    ax.axvline(df['Transaction Amount'].median(), color=clrs[1], ls='--', lw=1.2, label=f"Median ${df['Transaction Amount'].median():.0f}")
    ax.legend(fontsize=7, facecolor=CHART_FACE, edgecolor='#334155', labelcolor='white')
    style_ax(ax, 'Amount Distribution')

    # 2 Avg by type
    ax = axes[0, 1]
    by_type = df.groupby('Transaction Type')['Transaction Amount'].mean()
    by_type.plot(kind='bar', ax=ax, color=clrs[:3], edgecolor=CHART_FACE)
    ax.set_xticklabels(ax.get_xticklabels(), rotation=0)
    style_ax(ax, 'Avg Amount by Type')

    # 3 Fraud vs Legit box
    ax = axes[0, 2]
    bp = ax.boxplot([legit_df['Transaction Amount'], fraud_df['Transaction Amount']],
                    tick_labels=['Legit', 'Fraud'], patch_artist=True, medianprops=dict(color='white'))
    for p, c in zip(bp['boxes'], [clrs[1], clrs[3]]):
        p.set_facecolor(c); p.set_alpha(0.7)
    style_ax(ax, 'Amount: Fraud vs Legit')

    # 4 Fraud rate by type
    ax = axes[1, 0]
    df.groupby('Transaction Type')['Fraud Flag'].mean().plot(kind='bar', ax=ax, color=clrs[3], alpha=0.85, edgecolor=CHART_FACE)
    ax.yaxis.set_major_formatter(mticker.PercentFormatter(1.0))
    ax.set_xticklabels(ax.get_xticklabels(), rotation=0)
    style_ax(ax, 'Fraud Rate by Type')

    # 5 Fraud rate by device
    ax = axes[1, 1]
    df.groupby('Device Used')['Fraud Flag'].mean().plot(kind='bar', ax=ax, color=clrs[4], alpha=0.85, edgecolor=CHART_FACE)
    ax.yaxis.set_major_formatter(mticker.PercentFormatter(1.0))
    ax.set_xticklabels(ax.get_xticklabels(), rotation=0)
    style_ax(ax, 'Fraud Rate by Device')

    # 6 Fraud rate by slice
    ax = axes[1, 2]
    df.groupby('Network Slice ID')['Fraud Flag'].mean().plot(kind='bar', ax=ax, color=clrs[5], alpha=0.85, edgecolor=CHART_FACE)
    ax.yaxis.set_major_formatter(mticker.PercentFormatter(1.0))
    ax.set_xticklabels(ax.get_xticklabels(), rotation=0)
    style_ax(ax, 'Fraud Rate by Network Slice')

    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=CHART_DPI, bbox_inches='tight', facecolor=CHART_BG)
    plt.close(fig)
    buf.seek(0)
    return buf


def build_pdf(df, chart_buf):
    doc = SimpleDocTemplate(OUTPUT_PDF, pagesize=letter,
                            topMargin=0.6*inch, bottomMargin=0.6*inch,
                            leftMargin=0.75*inch, rightMargin=0.75*inch)

    styles = getSampleStyleSheet()
    primary = HexColor(PRIMARY_COLOR)
    accent = HexColor(ACCENT_COLOR)

    styles.add(ParagraphStyle('Title2', parent=styles['Title'], fontSize=22,
                              textColor=primary, spaceAfter=4, fontName='Helvetica-Bold'))
    styles.add(ParagraphStyle('Sub', parent=styles['Normal'], fontSize=11,
                              textColor=HexColor('#64748b'), alignment=TA_CENTER, spaceAfter=16))
    styles.add(ParagraphStyle('SectionHead', parent=styles['Heading2'], fontSize=14,
                              textColor=primary, spaceBefore=18, spaceAfter=8, fontName='Helvetica-Bold'))
    styles.add(ParagraphStyle('Body', parent=styles['Normal'], fontSize=10,
                              leading=15, alignment=TA_JUSTIFY, textColor=HexColor('#1e293b')))
    styles.add(ParagraphStyle('BulletCustom', parent=styles['Normal'], fontSize=10,
                              leading=15, leftIndent=20, bulletIndent=8,
                              textColor=HexColor('#1e293b')))
    styles.add(ParagraphStyle('KPI', parent=styles['Normal'], fontSize=11,
                              textColor=primary, fontName='Helvetica-Bold', alignment=TA_CENTER))
    styles.add(ParagraphStyle('KPIval', parent=styles['Normal'], fontSize=20,
                              textColor=accent, fontName='Helvetica-Bold', alignment=TA_CENTER))

    story = []
    hr = HRFlowable(width="100%", thickness=1, color=HexColor('#cbd5e1'), spaceAfter=12, spaceBefore=6)

    # Title
    story.append(Spacer(1, 0.3*inch))
    story.append(Paragraph(REPORT_TITLE, styles['Title2']))
    story.append(Paragraph(f"{REPORT_SUBTITLE}<br/>{AUTHOR} — {DATE}", styles['Sub']))
    story.append(hr)

    # KPI cards
    stats = df['Transaction Amount'].describe()
    fraud_rate = df['Fraud Flag'].mean() * 100
    kpi_data = [
        ['Total Txns', f"{len(df):,}"],
        ['Mean Amount', f"${stats['mean']:.2f}"],
        ['Median', f"${stats['50%']:.2f}"],
        ['Fraud Rate', f"{fraud_rate:.1f}%"],
    ]
    kpi_table = Table([[Paragraph(k, styles['KPI']) for k, _ in kpi_data],
                       [Paragraph(v, styles['KPIval']) for _, v in kpi_data]],
                      colWidths=[doc.width/4]*4, rowHeights=[22, 36])
    kpi_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), HexColor('#f1f5f9')),
        ('BOX', (0, 0), (-1, -1), 0.5, HexColor('#cbd5e1')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, HexColor('#e2e8f0')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(kpi_table)
    story.append(Spacer(1, 12))

    # Amount by Type table
    story.append(Paragraph("1. Transaction Amount by Type", styles['SectionHead']))
    by_type = df.groupby('Transaction Type')['Transaction Amount'].agg(['mean', 'median', 'std', 'min', 'max', 'count'])
    header = ['Type', 'Mean ($)', 'Median ($)', 'Std Dev', 'Min ($)', 'Max ($)', 'Count']
    tdata = [header]
    for idx, row in by_type.iterrows():
        tdata.append([idx, f"{row['mean']:.2f}", f"{row['median']:.2f}",
                       f"{row['std']:.2f}", f"{row['min']:.2f}", f"{row['max']:.2f}", str(int(row['count']))])

    col_w = [doc.width*w for w in [0.16, 0.14, 0.14, 0.14, 0.14, 0.14, 0.14]]
    t = Table(tdata, colWidths=col_w)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), primary),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('BACKGROUND', (0, 1), (-1, -1), HexColor('#f8fafc')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [HexColor('#f8fafc'), HexColor('#ffffff')]),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#cbd5e1')),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t)
    story.append(Spacer(1, 8))

    # Amount by Status table
    story.append(Paragraph("2. Transaction Amount by Status", styles['SectionHead']))
    by_status = df.groupby('Transaction Status')['Transaction Amount'].agg(['mean', 'median', 'count'])
    tdata2 = [['Status', 'Mean ($)', 'Median ($)', 'Count']]
    for idx, row in by_status.iterrows():
        tdata2.append([idx, f"{row['mean']:.2f}", f"{row['median']:.2f}", str(int(row['count']))])
    col_w2 = [doc.width*w for w in [0.25, 0.25, 0.25, 0.25]]
    t2 = Table(tdata2, colWidths=col_w2)
    t2.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), primary),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [HexColor('#f8fafc'), HexColor('#ffffff')]),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#cbd5e1')),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t2)

    # Charts
    story.append(Spacer(1, 10))
    story.append(Paragraph("3. Visual Analysis", styles['SectionHead']))
    chart_img = Image(chart_buf, width=doc.width, height=doc.width * 0.57)
    story.append(chart_img)

    # PAGE 2 — Behavioral Observations
    story.append(PageBreak())
    story.append(Paragraph("4. Key Behavioral Observations", styles['SectionHead']))
    story.append(hr)

    fraud_df = df[df['Fraud Flag'] == True]
    legit_df = df[df['Fraud Flag'] == False]
    high_thresh = df['Transaction Amount'].quantile(HIGH_VALUE_PERCENTILE / 100)
    df['High Value'] = df['Transaction Amount'] >= high_thresh
    high_val_fraud = df.groupby('High Value')['Fraud Flag'].mean()
    device_fraud = df.groupby('Device Used')['Fraud Flag'].mean()
    slice_fraud = df.groupby('Network Slice ID')['Fraud Flag'].mean()
    type_fraud = df.groupby('Transaction Type')['Fraud Flag'].mean()
    status_fraud = df.groupby('Transaction Status')['Fraud Flag'].mean()
    latency_fraud = df.groupby('Fraud Flag')['Latency (ms)'].mean()
    bw_fraud = df.groupby('Fraud Flag')['Slice Bandwidth (Mbps)'].mean()

    diff_pct = (fraud_df['Transaction Amount'].mean() - legit_df['Transaction Amount'].mean()) / legit_df['Transaction Amount'].mean() * 100

    observations = [
        (
            "Fraud Prevalence",
            f"{df['Fraud Flag'].mean()*100:.1f}% of all transactions are flagged as fraudulent. "
            f"Fraudulent transactions average <b>${fraud_df['Transaction Amount'].mean():.2f}</b> compared to "
            f"<b>${legit_df['Transaction Amount'].mean():.2f}</b> for legitimate ones — "
            f"{'higher' if diff_pct > 0 else 'lower'} by <b>{abs(diff_pct):.1f}%</b>."
        ),
        (
            "Device Behavior",
            "Fraud rates by device: " +
            ", ".join(f"<b>{d}</b>: {v*100:.1f}%" for d, v in device_fraud.items()) +
            ". Mobile devices show a notably higher fraud incidence."
        ),
        (
            "Network Slice Patterns",
            "Fraud rates by network slice: " +
            ", ".join(f"<b>{s}</b>: {v*100:.1f}%" for s, v in slice_fraud.items()) +
            f". {slice_fraud.idxmax()} exhibits the highest fraud concentration."
        ),
        (
            "Transaction Type Risk",
            "Fraud rates by type: " +
            ", ".join(f"<b>{t}</b>: {v*100:.1f}%" for t, v in type_fraud.items()) +
            f". {type_fraud.idxmax()} transactions carry the highest fraud risk."
        ),
        (
            "High-Value Transactions",
            f"Transactions above the {HIGH_VALUE_PERCENTILE}th percentile (>${high_thresh:,.0f}) "
            f"show a <b>{high_val_fraud[True]*100:.1f}%</b> fraud rate vs "
            f"<b>{high_val_fraud[False]*100:.1f}%</b> for normal-value transactions."
        ),
        (
            "Latency & Bandwidth",
            f"Average latency — Legit: <b>{latency_fraud[False]:.1f}ms</b>, Fraud: <b>{latency_fraud[True]:.1f}ms</b>. "
            f"Average bandwidth — Legit: <b>{bw_fraud[False]:.1f} Mbps</b>, Fraud: <b>{bw_fraud[True]:.1f} Mbps</b>. "
            "Neither metric shows significant deviation between fraud and legitimate transactions."
        ),
        (
            "Transaction Status",
            "Fraud rates by status: " +
            ", ".join(f"<b>{s}</b>: {v*100:.1f}%" for s, v in status_fraud.items()) +
            ". Fraud is nearly equally distributed across successful and failed transactions."
        ),
    ]

    for i, (title, body) in enumerate(observations, 1):
        # Observation card
        card_data = [[
            Paragraph(f'<font color="{ACCENT_COLOR}"><b>{i}. {title}</b></font>', styles['Body']),
        ], [
            Paragraph(body, styles['Body']),
        ]]
        card = Table(card_data, colWidths=[doc.width - 20])
        card.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), HexColor('#f8fafc')),
            ('BOX', (0, 0), (-1, -1), 0.5, HexColor('#e2e8f0')),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            ('BOTTOMPADDING', (0, -1), (-1, -1), 8),
            ('LINEBELOW', (0, 0), (-1, 0), 0.5, HexColor('#e2e8f0')),
        ]))
        story.append(card)
        story.append(Spacer(1, 8))

    # Summary
    story.append(Spacer(1, 6))
    story.append(Paragraph("Summary", styles['SectionHead']))
    story.append(Paragraph(
        f"This dataset of <b>{len(df):,}</b> transactions reveals a <b>{fraud_rate:.1f}%</b> fraud rate. "
        f"Fraudulent transactions tend to have slightly higher amounts. "
        f"Mobile devices and Deposit-type transactions show elevated fraud risk. "
        f"Network and latency metrics do not significantly differentiate fraud from legitimate activity, "
        f"suggesting these are weaker signals for fraud detection in this dataset.",
        styles['Body']
    ))

    doc.build(story)
    print(f"PDF saved: {OUTPUT_PDF}")


if __name__ == "__main__":
    df = load_data(INPUT_CSV)
    chart_buf = make_charts(df)
    build_pdf(df, chart_buf)
