"""PayPilot UI"""

from __future__ import annotations

import logging
import tempfile
from pathlib import Path

import streamlit as st

from agents.tools.db import InvoiceDB
from ui.dashboard import load_dashboard
from ui.render import (
    brand_header,
    inject_theme,
    invoice_header,
    kpi_cards,
    live_stepper_html,
    outcomes_bar,
    recent_table,
    render_landing,
    render_pipeline,
)
from ui.timeline import build_timeline
from agents.graph import graph

logging.basicConfig(level=logging.INFO)

SAMPLE_DIR = Path("data/invoices")
SUPPORTED = ("txt", "json", "csv", "xml", "pdf")
_STAGE_LABEL = {
    "extraction": "Reading",
    "validation": "Checking",
    "vp": "VP review",
    "auditor": "Senior review",
    "payment": "Payment",
}
_OUTCOME_TONE = {"Paid": "success", "Approved": "success", "Rejected": "danger", "Held": "warning", "In review": "accent"}
_VERDICT = {
    "paid": ("Paid", "success"),
    "approved": ("Approved", "success"),
    "rejected": ("Rejected", "danger"),
    "fx_review_hold": ("On hold", "warning"),
    "auditor_review": ("In review", "accent"),
}

st.set_page_config(page_title="PayPilot", page_icon="✈️", layout="wide")
inject_theme()


def _clear_result() -> None:
    # drop the previous invoice's result.
    st.session_state.pop("last_trn_id", None)


def _resolve_path(key_prefix: str) -> Path | None:
    samples = sorted(p.name for p in SAMPLE_DIR.glob("*") if p.suffix.lower().lstrip(".") in SUPPORTED)
    choice = st.selectbox(
        "Pick a sample invoice",
        samples,
        index=0,
        key=f"{key_prefix}_choice",
        on_change=_clear_result,
    )
    uploaded = st.file_uploader(
        "OR upload your own", type=list(SUPPORTED), key=f"{key_prefix}_upload", on_change=_clear_result
    )
    if uploaded is not None:
        suffix = Path(uploaded.name).suffix
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        tmp.write(uploaded.getvalue())
        tmp.close()
        return Path(tmp.name)
    if choice:
        return SAMPLE_DIR / choice
    return None


def _run_pipeline(path: Path) -> int | None:
    trn_id: int | None = None
    seen: list[str] = []
    placeholder = st.empty()
    placeholder.markdown(live_stepper_html(seen), unsafe_allow_html=True)  
    try:
        for chunk in graph.stream({"invoice_path": str(path)}, stream_mode="updates"):
            for node, update in chunk.items():
                if isinstance(update, dict) and update.get("trn_id"):
                    trn_id = int(update["trn_id"])
                label = _STAGE_LABEL.get(node)
                if label:
                    seen.append(label)
                    placeholder.markdown(live_stepper_html(seen), unsafe_allow_html=True)
        placeholder.empty()
    except Exception as exc:  
        placeholder.empty()
        st.error(f"We couldn't process this invoice: {exc}")
    return trn_id


def _show_extracted(db: InvoiceDB, trn_id: int) -> None:
    inv = db.get_invoice(trn_id)
    if inv is None:
        return
    st.write(
        {
            "Invoice number": inv.invoice_number,
            "Supplier": inv.merchant_name,
            "Invoice date": str(inv.invoice_date),
            "Due date": str(inv.due_date),
            "Subtotal": inv.subtotal,
            "Tax": inv.tax,
            "Total": inv.total,
            "Currency": inv.currency,
        }
    )
    items = [
        {"Item": i.item_name, "Qty": i.quantity, "Unit price": i.unit_price, "Line total": i.line_total}
        for i in db.get_items(trn_id)
    ]
    if items:
        st.dataframe(items, width="stretch", hide_index=True)


def _render_result(db: InvoiceDB, trn_id: int) -> None:
    timeline = build_timeline(db, trn_id)
    label, tone = _VERDICT.get(timeline.final_status, ("In review", "accent"))
    if timeline.summary:
        invoice_header(timeline.summary, verdict_label=label, verdict_tone=tone)
        with st.expander("View what we extracted"):
            _show_extracted(db, trn_id)
    st.divider()
    render_pipeline(timeline.steps)


def _render_dashboard() -> None:
    data = load_dashboard(InvoiceDB())
    if not data.processed:
        st.info("No invoices processed yet. Run one from the Process invoice tab.")
        return
    kpi_cards(
        [
            ("Invoices processed", str(data.processed)),
            ("Total paid", f"${data.total_paid:,.0f}"),
            ("Approval rate", f"{data.approval_rate}%"),
            ("Needs attention", str(data.needs_attention)),
        ]
    )
    st.markdown("##### Outcomes")
    outcomes_bar(data.outcomes, _OUTCOME_TONE)
    note = (
        f'<span style="font-size:0.78rem;color:#8A8A99">Showing {len(data.recent)} most recent of {data.processed}</span>'
        if data.processed > len(data.recent)
        else ""
    )
    st.markdown(
        '<div style="display:flex;align-items:baseline;justify-content:space-between;margin:10px 0 8px">'
        '<span style="font-size:1.05rem;font-weight:500;color:#1A1A2E">Recent invoices</span>'
        f"{note}</div>",
        unsafe_allow_html=True,
    )
    recent_table(data.recent)


started = st.session_state.get("started", False)
path: Path | None = None
go = False
if started:
    with st.sidebar:
        brand_header()
        st.divider()
        path = _resolve_path("side")
        go = st.button("Process", type="primary", disabled=path is None, width="stretch")

process_tab, dashboard_tab = st.tabs(["Process invoice", "Dashboard"])

with process_tab:
    if not started:
        _, center, _ = st.columns([1, 1.8, 1])
        with center:
            render_landing()
            btn = st.columns([1, 2, 1])[1]
            if btn.button("Get started", type="primary", width="stretch"):
                st.session_state["started"] = True
                st.rerun()
    else:
        mid = st.columns([1, 2, 1])[1]
        with mid:
            slot = st.empty()
            if go and path is not None:
                st.session_state["pending_path"] = str(path)

            pending = st.session_state.pop("pending_path", None)
            if pending is not None:
                with slot.container():
                    trn_id = _run_pipeline(Path(pending))
                if trn_id is not None:
                    st.session_state["last_trn_id"] = trn_id

            last = st.session_state.get("last_trn_id")
            if last is not None:
                with slot.container():
                    _render_result(InvoiceDB(), int(last))
            elif pending is None:
                with slot.container():
                    st.info("Pick or upload an invoice in the sidebar, then press Process.")

with dashboard_tab:
    _render_dashboard()
