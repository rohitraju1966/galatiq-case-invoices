"""Streamlit view layer. Turns the structured Timeline into the polished,
finance-friendly UI."""

from __future__ import annotations

import streamlit as st

from ui.dashboard import RecentRow
from ui.humanize import FriendlyFlag, StatusBadge
from ui.timeline import InvoiceSummary, TimelineStep

_TONE: dict[str, tuple[str, str]] = {
    "success": ("#E1F5EE", "#0F6E56"),
    "danger": ("#FCEBEB", "#A32D2D"),
    "warning": ("#FAEEDA", "#854F0B"),
    "accent": ("#EEEDFE", "#534AB7"),
    "neutral": ("#F1EFE8", "#5F5E5A"),
}
_SOLID: dict[str, str] = {"success": "#1D9E75", "danger": "#E24B4A", "warning": "#EF9F27", "accent": "#7F77DD"}
_SEVERITY_TONE: dict[str, str] = {"danger": "danger", "warning": "warning", "info": "accent"}
_STEP_ICON: dict[str, str] = {
    "extraction": "📄",
    "validation": "✓",
    "escalation": "↑",
    "auditor": "🛡",
    "vp_initial": "○",
    "vp_final": "✓",
    "payment": "$",
}

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500&display=swap');
html, body, [class*="css"], .stMarkdown, .stButton button { font-family: 'Inter', sans-serif; }
#MainMenu, footer { visibility: hidden; }
.block-container { padding-top: 2rem; }
.badge { display:inline-block; padding:3px 11px; border-radius:8px; font-size:0.78rem; font-weight:500; }
.inv-card { background:#F4F3FF; border:0.5px solid #E0DEF8; border-radius:12px; padding:16px 20px; margin-bottom:18px; }
.inv-sub { font-size:0.78rem; color:#7A78A8; }
.inv-merchant { font-size:1.15rem; font-weight:500; color:#2A2750; }
.inv-facts { display:flex; gap:44px; margin-top:14px; flex-wrap:wrap; }
.inv-flabel { font-size:0.74rem; color:#8A8A99; text-transform:uppercase; letter-spacing:0.04em; }
.inv-fval { font-size:1.5rem; font-weight:500; color:#1A1A2E; }
.inv-fval2 { font-size:0.95rem; margin-top:7px; color:#1A1A2E; }
.timeline { position:relative; margin:4px 0 2px; }
.tl-step { position:relative; padding-left:42px; margin-bottom:14px; }
.tl-step::before { content:''; position:absolute; left:15px; top:8px; bottom:-14px; width:2px; background:#E3E3EC; }
.tl-step:last-child::before { display:none; }
.tl-step.nested { margin-left:26px; }
.tl-dot { position:absolute; left:5px; top:6px; width:22px; height:22px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:12px; z-index:1; }
.step-card { border:0.5px solid #E6E6EE; border-radius:12px; padding:13px 18px; background:#FFFFFF; }
.step-who { font-size:0.72rem; color:#8A8A99; text-transform:uppercase; letter-spacing:0.04em; }
.step-title { font-size:0.95rem; font-weight:500; color:#1A1A2E; }
.step-note { font-size:0.88rem; color:#44444B; line-height:1.6; margin-top:4px; }
.flag { border-radius:8px; padding:9px 12px; margin:8px 0 0; }
.flag-title { font-size:0.85rem; font-weight:500; }
.flag-detail { font-size:0.82rem; line-height:1.5; opacity:0.9; }
.kpi-row { display:grid; grid-template-columns:repeat(4,1fr); gap:14px; margin-bottom:8px; }
.kpi { background:#F6F6FA; border:0.5px solid #ECECF2; border-radius:12px; padding:16px 18px; }
.kpi-label { font-size:0.78rem; color:#8A8A99; }
.kpi-value { font-size:1.8rem; font-weight:500; color:#1A1A2E; margin-top:4px; }
.otc-bar { display:flex; height:16px; border-radius:8px; overflow:hidden; margin:6px 0 10px; }
.otc-legend { display:flex; gap:20px; flex-wrap:wrap; font-size:0.82rem; color:#5F5E5A; }
.rtable { width:100%; border-collapse:collapse; font-size:0.86rem; }
.rtable th { text-align:left; color:#8A8A99; font-weight:500; font-size:0.72rem; text-transform:uppercase; letter-spacing:0.04em; border-bottom:0.5px solid #E6E6EE; padding:9px 12px; }
.rtable td { padding:11px 12px; border-bottom:0.5px solid #F0F0F4; vertical-align:top; }
.live-wrap { text-align:center; padding:48px 0 36px; }
.live-title { font-size:0.8rem; color:#8A8A99; text-transform:uppercase; letter-spacing:0.06em; margin-bottom:22px; }
.live-row { display:inline-flex; align-items:center; gap:9px; flex-wrap:wrap; justify-content:center; }
.live-chip { padding:9px 17px; border-radius:10px; font-size:0.9rem; font-weight:500; }
.live-chip.done { background:#E1F5EE; color:#0F6E56; }
.live-chip.active { background:#EEEDFE; color:#534AB7; animation:apulse 1.2s ease-in-out infinite; }
.live-arrow { color:#CFCFD8; font-size:1rem; }
@keyframes apulse { 0%,100%{opacity:1} 50%{opacity:0.4} }
.brand { display:flex; align-items:center; gap:12px; margin:2px 0 8px; }
.brand-badge { width:42px; height:42px; border-radius:12px; background:#4F46E5; display:flex; align-items:center; justify-content:center; flex-shrink:0; }
.brand-name { font-size:1.4rem; font-weight:500; color:#1A1A2E; line-height:1.05; letter-spacing:-0.01em; }
.brand-tag { font-size:0.76rem; color:#8A8A99; margin-top:3px; line-height:1.35; }
.hero { text-align:center; padding:15vh 0 18px; }
.hero-badge { width:66px; height:66px; border-radius:18px; background:#4F46E5; display:inline-flex; align-items:center; justify-content:center; margin-bottom:16px; }
.hero-name { font-size:2.5rem; font-weight:500; color:#1A1A2E; letter-spacing:-0.02em; }
.hero-tag { font-size:1.1rem; color:#8A8A99; margin-top:8px; }
.land-desc { text-align:center; font-size:1.05rem; color:#5F5E5A; margin:0 auto 30px; line-height:1.65; }
.land-steps { display:flex; justify-content:center; align-items:flex-start; gap:12px; flex-wrap:wrap; margin-bottom:10px; }
.land-step { display:flex; flex-direction:column; align-items:center; gap:8px; width:78px; }
.land-ico { width:44px; height:44px; border-radius:13px; background:#EEEDFE; color:#534AB7; display:flex; align-items:center; justify-content:center; font-size:1rem; font-weight:500; }
.land-lbl { font-size:0.85rem; color:#44444B; }
.land-arrow { color:#CFCFD8; font-size:1rem; margin-top:17px; }
</style>
"""

_LAND_STEPS = [("1", "Read"), ("2", "Check"), ("3", "Review"), ("4", "Pay")]


def render_landing() -> None:
    chips = '<span class="land-arrow">→</span>'.join(
        f'<div class="land-step"><div class="land-ico">{n}</div><div class="land-lbl">{label}</div></div>'
        for n, label in _LAND_STEPS
    )
    st.markdown(
        '<div class="hero">'
        '<div class="hero-badge">'
        '<svg width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" '
        'stroke-linecap="round" stroke-linejoin="round"><path d="M22 2 11 13"/><path d="M22 2 15 22 11 13 2 9z"/></svg>'
        "</div>"
        '<div class="hero-name">Pay<span style="color:#4F46E5">Pilot</span></div>'
        '<div class="hero-tag">Your accounts-payable desk, on autopilot.</div>'
        "</div>"
        '<div class="land-desc">PayPilot reads every invoice, checks it against your records, '
        "runs it through finance review, and pays the approved ones automatically.</div>"
        f'<div class="land-steps">{chips}</div>',
        unsafe_allow_html=True,
    )


def brand_header() -> None:
    st.markdown(
        '<div class="brand">'
        '<div class="brand-badge">'
        '<svg width="21" height="21" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" '
        'stroke-linecap="round" stroke-linejoin="round"><path d="M22 2 11 13"/><path d="M22 2 15 22 11 13 2 9z"/></svg>'
        "</div>"
        '<div><div class="brand-name">Pay<span style="color:#4F46E5">Pilot</span></div>'
        '<div class="brand-tag">Your accounts-payable desk, on autopilot.</div></div>'
        "</div>",
        unsafe_allow_html=True,
    )


def inject_theme() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)


def _badge_html(badge: StatusBadge) -> str:
    bg, fg = _TONE.get(badge.tone, _TONE["neutral"])
    return f'<span class="badge" style="background:{bg};color:{fg}">{badge.label}</span>'


def pill(label: str, tone: str) -> str:
    return _badge_html(StatusBadge(label, tone))


def _flag_html(flag: FriendlyFlag) -> str:
    bg, fg = _TONE[_SEVERITY_TONE.get(flag.severity, "warning")]
    return (
        f'<div class="flag" style="background:{bg}">'
        f'<div class="flag-title" style="color:{fg}">{flag.title}</div>'
        f'<div class="flag-detail" style="color:{fg}">{flag.detail}</div></div>'
    )


def invoice_header(summary: InvoiceSummary, verdict_label: str | None = None, verdict_tone: str = "neutral") -> None:
    total = f"${summary.total:,.0f}" if summary.total is not None else "—"
    verdict_fact = ""
    if verdict_label:
        verdict_fact = (
            f'<div><div class="inv-flabel">Verdict</div>'
            f'<div style="margin-top:6px">{pill(verdict_label, verdict_tone)}</div></div>'
        )
    st.markdown(
        f'<div class="inv-card">'
        f'<div class="inv-sub">Invoice {summary.invoice_number}</div>'
        f'<div class="inv-merchant">{summary.merchant_name}</div>'
        f'<div class="inv-facts">'
        f'<div><div class="inv-flabel">Total</div><div class="inv-fval">{total}</div></div>'
        f'<div><div class="inv-flabel">Due date</div><div class="inv-fval2">{summary.due_date}</div></div>'
        f'<div><div class="inv-flabel">Items</div><div class="inv-fval2">{summary.item_count}</div></div>'
        f'<div><div class="inv-flabel">Currency</div><div class="inv-fval2">{summary.currency}</div></div>'
        f"{verdict_fact}"
        f"</div></div>",
        unsafe_allow_html=True,
    )


def render_pipeline(steps: list[TimelineStep]) -> None:
    parts = ['<div class="timeline">']
    for step in steps:
        tone = step.badge.tone if step.badge else "accent"
        dot_bg, dot_fg = _TONE.get(tone, _TONE["accent"])
        badge_markup = f"&nbsp;&nbsp;{_badge_html(step.badge)}" if step.badge else ""
        flags_markup = "".join(_flag_html(f) for f in step.flags)
        note = step.note.replace("\n", "<br>")
        nested = " nested" if step.nested else ""
        parts.append(
            f'<div class="tl-step{nested}">'
            f'<div class="tl-dot" style="background:{dot_bg};color:{dot_fg}">{_STEP_ICON.get(step.key, "•")}</div>'
            f'<div class="step-card">'
            f'<div class="step-who">{step.reviewer}</div>'
            f'<div class="step-title">{step.title}{badge_markup}</div>'
            f'<div class="step-note">{note}</div>{flags_markup}</div></div>'
        )
    parts.append("</div>")
    st.markdown("".join(parts), unsafe_allow_html=True)


def kpi_cards(items: list[tuple[str, str]]) -> None:
    cards = "".join(
        f'<div class="kpi"><div class="kpi-label">{label}</div><div class="kpi-value">{value}</div></div>'
        for label, value in items
    )
    st.markdown(f'<div class="kpi-row">{cards}</div>', unsafe_allow_html=True)


def outcomes_bar(outcomes: dict[str, int], tone_by_label: dict[str, str]) -> None:
    total = sum(outcomes.values()) or 1
    segments = "".join(
        f'<div style="width:{count / total * 100:.1f}%;background:{_SOLID.get(tone_by_label.get(label, "neutral"), "#888")}" title="{label}"></div>'
        for label, count in outcomes.items()
    )
    legend = "".join(
        f'<span><span style="display:inline-block;width:9px;height:9px;border-radius:2px;'
        f'background:{_SOLID.get(tone_by_label.get(label, "neutral"), "#888")};margin-right:6px"></span>{label} {count}</span>'
        for label, count in outcomes.items()
    )
    st.markdown(f'<div class="otc-bar">{segments}</div><div class="otc-legend">{legend}</div>', unsafe_allow_html=True)


def live_stepper_html(done_labels: list[str], finished: bool = False) -> str:
    chips = [f'<span class="live-chip done">{label}&nbsp;✓</span>' for label in done_labels]
    if not finished:
        chips.append('<span class="live-chip active">working…</span>')
    row = '<span class="live-arrow">→</span>'.join(chips)
    title = "Done" if finished else "Processing invoice"
    return f'<div class="live-wrap"><div class="live-title">{title}</div><div class="live-row">{row}</div></div>'


def recent_table(rows: list[RecentRow]) -> None:
    head = "<tr><th>Invoice</th><th>Supplier</th><th>Amount</th><th>Status</th></tr>"
    body = "".join(
        f"<tr><td style='font-weight:500'>{r.invoice_number}</td><td>{r.merchant}</td>"
        f"<td style='text-align:right'>{('$' + format(r.total, ',.0f')) if r.total is not None else '—'}</td>"
        f"<td>{pill(r.status_label, r.tone)}</td></tr>"
        for r in rows
    )
    st.markdown(f'<table class="rtable"><thead>{head}</thead><tbody>{body}</tbody></table>', unsafe_allow_html=True)
