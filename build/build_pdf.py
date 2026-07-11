#!/usr/bin/env python3
"""
Build polished PDFs from markdown documents using Chrome headless rendering.

Usage:
    python3 build_pdf.py [doc_key]
    python3 build_pdf.py all
    python3 build_pdf.py son

Each doc has a curated cover-page configuration so the first impression is premium.
"""

import re
import subprocess
import sys
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "build"
OUT = ROOT / "pdf"
THEME_CSS = BUILD / "theme.css"

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
BRAND = "PadelMind"

# ---------- Document registry ----------
# Each entry: source markdown, output filename stem, cover-page metadata

DOCS = {
    "son": {
        "src": "SON_TECHNICAL_REVIEW.md",
        "stem": "01_Technical_Review_Request_for_Son",
        "doctitle": "Technical Review Request",
        "title": "A Technical Conversation",
        "subtitle": "Padel AI Coaching Platform — a conversation between father and son, asking for your brain on the architecture and the moat thesis.",
        "doctype": "For Family Eyes — Technical Review",
        "meta": [
            ("Prepared for", "[Son's name]"),
            ("Reading time", "20–50 minutes"),
            ("Required response", "4 lines on §Q5 and §Q7"),
            ("Authored", "Manoj Maheshwari · 2026-07-01"),
        ],
    },
    "baseclub": {
        "src": "BASE_CLUB_OFFER.md",
        "stem": "02_Base_Club_Founding_Pilot_Proposal",
        "doctitle": "Founding-Club Pilot Proposal",
        "title": "A 60-Day AI Coaching Pilot",
        "subtitle": "Bringing personalised, expert-coach-grade match analysis to every member of your club — at zero cost during the trial.",
        "doctype": "For [Club Name] Committee",
        "meta": [
            ("Prepared for", "[Club Name] Committee"),
            ("Pilot duration", "60 days, fully covered by us"),
            ("Member cost", "Zero during pilot"),
            ("Authored", "Manoj Maheshwari · 2026-07-01"),
        ],
    },
    "nsci": {
        "src": "NSCI_PROPOSAL.md",
        "stem": "08_NSCI_Proposal",
        "doctitle": "Proposal to the NSCI Committee",
        "title": "An AI Vision-Based Player Grading &amp; Improvement System for the NSCI Padel Courts",
        "subtitle": "A proposal to install video capture equipment on both NSCI padel courts — a 90-day training phase at no cost to the club, followed by a 2-year commercial phase with a 30% share of gross member revenue remitted to NSCI. No audio. No third-party access.",
        "doctype": "For the NSCI Padel Committee",
        "meta": [
            ("Prepared for", "The Padel Committee, NSCI, Worli, Mumbai"),
            ("Applicant", "Anchor Fastener Mfg Corporation"),
            ("Product line", "PadelMind by AutomationXpert"),
            ("Club economics", "Zero cost. 30% of gross member revenue in commercial phase."),
            ("Authored", "Manoj Maheshwari · 2026-07-02"),
        ],
    },
    "technical": {
        "src": "TECHNICAL_FEASIBILITY_REPORT.md",
        "stem": "03_Technical_Feasibility_Report",
        "doctitle": "Technical Feasibility Report",
        "title": "Technical Feasibility Report",
        "subtitle": "End-to-end architecture, computer-vision pipeline, hardware specification, ML approach, multi-sport extensibility, and edge-inference roadmap.",
        "doctype": "Engineering & Investor Diligence",
        "meta": [
            ("Document version", "1.0"),
            ("Classification", "Internal + diligence-ready"),
            ("Authored", "Manoj Maheshwari + AI drafting · 2026-07-01"),
            ("Reviewers (pending)", "Coach, CTO, Apple AI advisor"),
        ],
    },
    "commercial": {
        "src": "COMMERCIAL_REPORT.md",
        "stem": "04_Commercial_Report",
        "doctitle": "Commercial Report",
        "title": "Commercial Report",
        "subtitle": "Market opportunity, customer segments, pricing, marketing engine, multi-sport expansion, financial projections, and exit scenarios.",
        "doctype": "For Founders, Advisors, and Backers",
        "meta": [
            ("Document version", "1.0"),
            ("Audience", "Founders + investors"),
            ("Authored", "Manoj Maheshwari + AI drafting · 2026-07-01"),
            ("Companion docs", "Strategy · Execution · Feasibility"),
        ],
    },
    "execution": {
        "src": "PROJECT_REPORT.md",
        "stem": "05_Execution_Project_Report",
        "doctitle": "Project Report — Execution",
        "title": "Project Report",
        "subtitle": "30-day punch list, six-month deliverables, resource plan, budget, risk register, governance, and the backer pitch playbook.",
        "doctype": "Execution Document",
        "meta": [
            ("Document version", "0.1"),
            ("Purpose", "What we do, when, with whom, for how much"),
            ("Authored", "Manoj Maheshwari + AI drafting · 2026-07-01"),
            ("Refresh cadence", "Weekly during build"),
        ],
    },
    "venture": {
        "src": "PADEL_AI_VENTURE_PLAN.md",
        "stem": "06_Strategic_Venture_Plan",
        "doctitle": "Strategic Venture Plan",
        "title": "Strategic Venture Plan",
        "subtitle": "Mission, market analysis, competitive landscape, moat thesis, product strategy, capital plan, and the path from India to Asia to the world.",
        "doctype": "Master Strategy Document",
        "meta": [
            ("Document version", "0.2"),
            ("Last major update", "China + moat sharpening 2026-07-01"),
            ("Authored", "Manoj Maheshwari + AI drafting · 2026-07-01"),
            ("Single Point of Truth", "Yes — read this before refining anywhere"),
        ],
    },
    "joao": {
        "src": "JOAO_OUTREACH_EMAIL.md",
        "stem": "07_Outreach_Joao_Silva",
        "doctitle": "Outreach — João Silva",
        "title": "Outreach to João Silva",
        "subtitle": "Author of padel_analytics — opening a collaboration dialogue for the India + Middle East venture, with copy-paste-ready email and a follow-up cadence playbook.",
        "doctype": "Founder Outreach Brief",
        "meta": [
            ("Target", "João Silva — padel_analytics"),
            ("Email", "jsilvawasd@hotmail.com"),
            ("Repo", "github.com/Joao-M-Silva/padel_analytics"),
            ("Prepared", "2026-07-01"),
        ],
    },
    "sonbrief": {
        "src": "TECH_BRIEFING_FOR_SON.md",
        "stem": "09_Tech_Briefing_For_Son",
        "doctitle": "Technical Briefing — Second Pass",
        "title": "Technical Briefing — Round 2",
        "subtitle": "Plain-language walk-through of the pipeline, the Ultralytics licensing decision, and four specific questions where a technical opinion would change the plan.",
        "doctype": "For Family Eyes — Technical Judgement Call",
        "meta": [
            ("Prepared for", "[Son's name]"),
            ("Reading time", "20–25 minutes"),
            ("Required response", "Four two-liner answers to the questions in §5"),
            ("Authored", "Manoj Maheshwari · 2026-07-03"),
        ],
    },
    "plan60": {
        "src": "60_DAY_EXPANDED_PLAN.md",
        "stem": "10_60_Day_Expanded_Execution_Plan",
        "doctitle": "60-Day Expanded Execution Plan",
        "title": "60-Day Expanded Execution Plan",
        "subtitle": "Nine parallel workstreams, six milestone gates, ten-person team roster, and per-workstream owner, scope, day-by-day tasks, deliverables, handoffs, risk, and budget.",
        "doctype": "Operational Source of Truth",
        "meta": [
            ("Document version", "2.0"),
            ("Companion", "TECH_BRIEFING_FOR_SON · TECHNICAL_FEASIBILITY_REPORT · NSCI_PROPOSAL"),
            ("Target outcome", "Working V1 by Day 60; commercial launch Day 91"),
            ("Authored", "Manoj Maheshwari · 2026-07-03"),
        ],
    },
    "joaov2": {
        "src": "JOAO_OUTREACH_EMAIL_v2.md",
        "stem": "11_Outreach_Joao_Silva_v2_Humble",
        "doctitle": "Outreach — João Silva (v2)",
        "title": "Outreach to João Silva — Round 2",
        "subtitle": "Humble, exploratory positioning. Non-technical player asking for a 30-minute Google Meet. No equity offer, no team invite, no expectations beyond the conversation itself.",
        "doctype": "Founder Outreach Brief — Finalised for Send",
        "meta": [
            ("Target", "João Silva — padel_analytics"),
            ("Email", "jsilvawasd@hotmail.com"),
            ("Ask", "30-min Google Meet, on his time"),
            ("Prepared", "2026-07-03"),
        ],
    },
    "teambrief": {
        "src": "TEAM_BRIEF_MARKET_AND_OPPORTUNITY.md",
        "stem": "12_Team_Brief_Market_and_Opportunity",
        "doctitle": "Team Brief — Market & Opportunity",
        "title": "The Padel AI Opportunity",
        "subtitle": "Mumbai market read, current statistics, economic playbook, competitive landscape, tie-up prospects, and the technical partner shortlist — brief for the founding team.",
        "doctype": "Team Briefing — Founding Group",
        "meta": [
            ("Prepared for", "Manoj · Aayush · Tanisha"),
            ("Companion", "Scope Reset — Technical Deltas (follows separately)"),
            ("Reading time", "20–25 minutes"),
            ("Authored", "Manoj Maheshwari + AI research · 2026-07-04"),
        ],
    },
    "sasank": {
        "src": "SASANK_SOW_PHASE1.md",
        "stem": "13_Phase1_Scope_of_Work_Sasank",
        "doctitle": "Phase 1 — Scope of Work",
        "title": "Phase 1 Development Brief",
        "subtitle": "Post-match highlight reel and court heatmap delivery — complete scope of work for development partner, with division of responsibilities, integration contracts, and acceptance criteria per component.",
        "doctype": "Development Partner Brief — For Quotation",
        "meta": [
            ("Prepared by", "Manoj Maheshwari · PadelMind"),
            ("Phase", "Phase 1 — Highlights + Heatmap (no shot classifier)"),
            ("Target delivery", "12 weeks from engagement"),
            ("Authored", "2026-07-09"),
        ],
    },
    "sonphase": {
        "src": "SON_PHASE_PLAN_REVIEW.md",
        "stem": "14_Phase_Plan_Technical_Review",
        "doctitle": "Phase Plan — Technical Review",
        "title": "A Technical Conversation",
        "subtitle": "PadelMind — the full three-phase build plan, architecture, contractor situation, and seven technical questions where your opinion would change the call.",
        "doctype": "For Family Eyes — Technical Review",
        "meta": [
            ("Prepared for", "Arjun Maheshwari"),
            ("Reading time", "20–30 minutes"),
            ("Required response", "Seven technical questions — §7"),
            ("Authored", "Manoj Maheshwari · 2026-07-09"),
        ],
    },
}

# ---------- Helpers ----------

def md_to_html(md_text: str) -> str:
    """Convert markdown to HTML with the extensions we need."""
    return markdown.markdown(
        md_text,
        extensions=[
            "extra",       # tables, fenced code, attr lists, definition lists, etc.
            "sane_lists",
            "toc",
            "smarty",
            "admonition",
        ],
        output_format="html5",
    )


def render_cover(cfg: dict) -> str:
    """Render the cover-page HTML for a document."""
    meta_rows = "\n".join(
        f'<div><div class="cover-meta-label">{label}</div>'
        f'<div class="cover-meta-value">{value}</div></div>'
        for label, value in cfg["meta"]
    )
    return f"""
<div class="cover">
  <div>
    <div class="cover-brand">{BRAND}<span class="cover-brand-accent"></span></div>
    <div class="cover-tagline">AI Coaching for Racket Sports</div>
  </div>
  <div class="cover-main">
    <div class="cover-doctype">{cfg["doctype"]}</div>
    <h1 class="cover-title">{cfg["title"]}</h1>
    <p class="cover-subtitle">{cfg["subtitle"]}</p>
  </div>
  <div class="cover-meta">
    {meta_rows}
  </div>
</div>
"""


def build_html(cfg: dict, theme_css: str) -> str:
    src = ROOT / cfg["src"]
    md_text = src.read_text(encoding="utf-8")

    # Strip top H1 from MD since cover handles title
    md_text = re.sub(r"^# .+\n+", "", md_text, count=1)

    body_html = md_to_html(md_text)
    cover_html = render_cover(cfg)

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>{cfg['doctitle']} — {BRAND}</title>
  <style>
{theme_css}
  </style>
</head>
<body>
{cover_html}
<div class="body" data-doctitle="{cfg['doctitle']}" data-brand="{BRAND}">
{body_html}
<div class="doc-footer">
  Companion document set: Strategic Venture Plan · Project Report · Technical Feasibility · Commercial Report · Base Club Offer · Technical Review Request.<br/>
  Single source of truth maintained in <code>~/Documents/padel-clone/</code>.
</div>
</div>
</body>
</html>
"""


def build_one(key: str) -> Path:
    if key not in DOCS:
        raise SystemExit(f"Unknown doc key: {key}")
    cfg = DOCS[key]
    theme = THEME_CSS.read_text(encoding="utf-8")
    html = build_html(cfg, theme)

    html_path = OUT / f"{cfg['stem']}.html"
    pdf_path = OUT / f"{cfg['stem']}.pdf"
    html_path.write_text(html, encoding="utf-8")
    print(f"  → HTML written: {html_path.name}")

    # Puppeteer PDF render — true zero-margin, full-bleed cover
    node_script = BUILD / "pdf_render.js"
    cmd = ["node", str(node_script), str(html_path), str(pdf_path)]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0 or not pdf_path.exists() or pdf_path.stat().st_size < 1000:
        print(f"  ⚠ Node stderr: {res.stderr[:400]}")
        raise SystemExit(f"PDF build failed for {key}")
    size_kb = pdf_path.stat().st_size // 1024
    print(f"  → PDF written: {pdf_path.name} ({size_kb} KB)")
    return pdf_path


# ---------- Entrypoint ----------
def main():
    if len(sys.argv) < 2:
        print("Usage: python3 build_pdf.py [son|baseclub|technical|commercial|execution|venture|all]")
        return

    targets = sys.argv[1:]
    if "all" in targets:
        targets = list(DOCS.keys())

    OUT.mkdir(exist_ok=True)
    for k in targets:
        print(f"\n▶ Building {k.upper()}")
        build_one(k)

    print("\n✓ All requested PDFs in:", OUT)


if __name__ == "__main__":
    main()
