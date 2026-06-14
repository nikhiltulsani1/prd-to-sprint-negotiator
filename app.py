import streamlit as st
import time
import json


def normalise_velocity(v: float, default_capacity: int = 40) -> float:
    """Accepts story points (32) or ratio (0.8). Always returns a ratio 0.1–1.0."""
    if v > 1:
        return min(v / default_capacity, 1.0)
    return max(0.1, min(v, 1.0))
try:
    import markdown as md
except Exception:
    md = None

st.set_page_config(
    page_title="PRD-to-Sprint Negotiator",
    page_icon="🤝",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Theme toggle — stored in session state, defaults to dark
if "theme" not in st.session_state:
    st.session_state.theme = "dark"

is_dark = st.session_state.theme == "dark"
bg        = "#0e0e16" if is_dark else "#f5f5f7"
card_bg   = "#1a1a2e" if is_dark else "#ffffff"
text      = "#e6eef6" if is_dark else "#1a1a2e"
muted     = "#7a8a9a" if is_dark else "#6b7280"
textarea_bg = "#0b0b0f" if is_dark else "#f9f9fb"

st.markdown(f"""
<style>
#MainMenu, footer, header {{visibility: hidden;}}
.block-container {{
    padding: 1rem 2rem 0.5rem 2rem !important;
    max-width: 100% !important;
}}
.stTabs [data-baseweb="tab-list"] {{ gap: 4px; }}
.stTabs [data-baseweb="tab"] {{ padding: 4px 12px; font-size: 13px; }}
div[data-testid="stVerticalBlock"] > div {{ padding-top: 0 !important; }}
body {{ background: {bg}; color: {text}; }}
.stApp {{ background: {bg}; }}
textarea, .stTextArea textarea {{ background: {textarea_bg}; color: {text}; }}
.main > div {{ padding-bottom: 0 !important; }}
[data-testid="stAppViewContainer"] {{ background: {bg}; }}
</style>
""", unsafe_allow_html=True)

# HEADER
col_title, col_status, col_theme = st.columns([5, 1, 1])
with col_title:
    st.markdown("## 🤝 PRD-to-Sprint Negotiator", unsafe_allow_html=True)
with col_status:
    status_placeholder = st.empty()
with col_theme:
    toggle_label = "☀️ Light" if is_dark else "🌙 Dark"
    if st.button(toggle_label, use_container_width=True):
        st.session_state.theme = "light" if is_dark else "dark"
        st.rerun()

st.divider()

# MAIN LAYOUT
left, right = st.columns([1, 1], gap="medium")

with left:
    input_mode = st.radio("", ["📝 Paste", "📁 Upload"], horizontal=True, label_visibility="collapsed")

    prd_text = ""
    uploaded = None
    if input_mode == "📝 Paste":
        prd_text = st.text_area("", height=160, placeholder="Paste PRD here...", label_visibility="collapsed")
    else:
        uploaded = st.file_uploader("", type=["txt", "md", "pdf", "docx"], label_visibility="collapsed")
        if uploaded:
            try:
                name = uploaded.name.lower()
                if name.endswith((".txt", ".md")):
                    prd_text = uploaded.read().decode("utf-8")
                elif name.endswith('.pdf'):
                    import fitz
                    doc = fitz.open(stream=uploaded.read(), filetype='pdf')
                    prd_text = "\n".join(page.get_text() for page in doc)
                elif name.endswith('.docx'):
                    from docx import Document
                    from io import BytesIO
                    doc = Document(BytesIO(uploaded.read()))
                    prd_text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
                st.caption(f"✅ {len(prd_text.split())} words from {uploaded.name}")
            except Exception as e:
                st.error(f"Failed to read file: {e}")

    # Sprint context
    c1, c2 = st.columns(2)
    with c1:
        sprint_num = st.number_input("Sprint", min_value=1, value=1, step=1)
        velocity_mode = st.radio(
            "Velocity input", ["📊 Story points", "📉 Ratio"],
            horizontal=True, label_visibility="collapsed"
        )
        if velocity_mode == "📊 Story points":
            velocity = float(st.number_input(
                "Story points completed last sprint",
                min_value=1, max_value=100, value=40,
                help="How many story points did your team ship last sprint? Default 40 = full capacity."
            ))
        else:
            velocity = st.slider(
                "Velocity ratio", min_value=0.1, max_value=1.0, value=1.0, step=0.1,
                help="0.8 = team completed 80% of committed points last sprint"
            )
    with c2:
        completed = st.text_input("Items Completed", placeholder="Auth, Login")
        blocked = st.text_input("Items Blocked", placeholder="Payments")

    c1, c2 = st.columns(2)
    with c1:
        project_key = st.text_input("Project key", value="PROJ")
    with c2:
        standards_file = st.file_uploader(
            "Standards (Company standard for Jira and ADO items) (optional)",
            type=["md", "txt"],
            label_visibility="visible",
        )

    run = st.button("🚀 Run the Room", use_container_width=True, type="primary")

    # Update header status
    if run:
        status_placeholder.warning("Counciling...")
    elif st.session_state.get("results"):
        status_placeholder.success("Sprint Ready")
    else:
        status_placeholder.caption("Waiting for input")

    with st.expander("⚡ Need faster results? Try the CLI"):
        st.code(
            "python main.py samples/sample_prd.txt --sprint 1\n\n"
            "python main.py samples/sample_prd.txt --sprint 2 \\\n"
            "  --completed \"User Authentication\" \\\n"
            "  --velocity 0.8",
            language="bash",
        )
        st.caption("CLI skips UI rendering overhead — typically 20–30% faster")

with right:
    tab_room, tab_backlog, tab_mcp, tab_summary = st.tabs(["🏛 The Room", "📋 Backlog", "🔧 MCP", "📊 Summary"])

    with tab_room:
        # Show intro only when no run is in progress and no results yet
        if "results" not in st.session_state and not run:
            st.markdown("**Five specialists. One sprint plan.**")
            st.markdown("""
- 👔 **Product Manager** — extracts features, priorities, acceptance criteria
- 👷 **Engineer** — estimates story points, flags technical risks
- 🔍 **QA Engineer** — writes specific test cases, blocks missing AC
- ⚖️ **Negotiator** — fits everything into sprint capacity, explains every cut
- 📝 **Scribe** — formats sprint backlog + MCP payload for Jira/ADO/Linear
            """)
            st.info("Upload or paste a PRD on the left, then click **Run the Room**.")

    with tab_backlog:
        backlog_ph = st.empty()

    with tab_mcp:
        mcp_ph = st.empty()

    with tab_summary:
        summary_ph = st.empty()

# Pipeline execution
if run:
    if not prd_text or not prd_text.strip():
        st.error("Paste or upload a PRD first.")
        st.stop()

    # Cache detection — same PRD + same sprint means we already have results
    if (
        st.session_state.get("results")
        and st.session_state.get("last_prd") == prd_text
        and st.session_state.get("last_sprint") == sprint_num
    ):
        st.warning(
            "⚠️ Same PRD and sprint as last run. Results are cached below. "
            "Change the PRD or sprint number to run again."
        )
        st.stop()

    standards_content = ""
    if standards_file:
        try:
            standards_content = standards_file.read().decode('utf-8')
        except Exception:
            standards_content = ""

    from agents.product_agent import ProductAgent
    from agents.engineer_agent import EngineerAgent
    from agents.qa_agent import QAAgent
    from agents.negotiator_agent import NegotiatorAgent
    from agents.output_agent import OutputAgent
    from agents.mcp_payload_generator import MCPPayloadGenerator

    velocity_ratio = normalise_velocity(velocity)
    velocity_display = f"{int(velocity)} pts" if velocity > 1 else f"{int(velocity * 100)}%"

    sprint_context = {
        "sprint":           sprint_num,
        "completed":        [s.strip() for s in completed.split(',') if s.strip()],
        "blocked":          [s.strip() for s in blocked.split(',') if s.strip()],
        "velocity":         velocity_ratio,
        "velocity_display": velocity_display,
        "standards": standards_content,
    }

    start = time.time()
    agent_rows = []

    # Live room — all content goes directly into tab_room
    with tab_room:
        progress = st.progress(0, "Starting...")
        p1 = st.empty()
        p2 = st.empty()
        p3 = st.empty()
        p4 = st.empty()
        p5 = st.empty()
        notes_placeholder = st.empty()

    # Agent 1
    p1.markdown("⏳ **👔 Product Manager** — reading PRD...")
    t0 = time.time()
    product_output = ProductAgent().run(prd_text, sprint_context)
    t1 = time.time()
    features = product_output.get('features', [])
    high = sum(1 for f in features if f.get('priority') == 'High')
    top = features[0]['name'] if features else 'N/A'
    row1 = f"✅ **👔 Product Manager** · {len(features)} features · {high} High · Top: {top} · `{t1-t0:.1f}s`"
    p1.markdown(row1)
    agent_rows.append(row1)
    progress.progress(20, "Engineer estimating...")

    # Agent 2
    p2.markdown("⏳ **👷 Engineer** — estimating complexity...")
    t0 = time.time()
    engineer_output = EngineerAgent().run(product_output, sprint_context)
    t1 = time.time()
    est = engineer_output.get('estimates', [])
    total_pts = engineer_output.get('total_points', 0)
    complex_f = max(est, key=lambda x: x.get('story_points', 0), default={})
    row2 = f"✅ **👷 Engineer** · {total_pts}pts total · Most complex: {complex_f.get('feature_name','N/A')} · `{t1-t0:.1f}s`"
    p2.markdown(row2)
    agent_rows.append(row2)
    progress.progress(40, "QA reviewing...")

    # Agent 3
    p3.markdown("⏳ **🔍 QA Engineer** — writing test cases (parallel)...")
    t0 = time.time()
    qa_output = QAAgent().run(product_output, engineer_output, sprint_context)
    t1 = time.time()
    flagged = qa_output.get('flagged_features', [])
    total_tests = sum(
        len(r.get('test_cases', [])) + len(r.get('edge_cases', []))
        for r in qa_output.get('qa_review', [])
    )
    row3 = f"✅ **🔍 QA Engineer** · Risk: {qa_output.get('overall_quality_risk','?')} · {len(flagged)} flagged · {total_tests} tests · `{t1-t0:.1f}s`"
    p3.markdown(row3)
    agent_rows.append(row3)
    progress.progress(60, "Negotiating...")

    # Agent 4
    p4.markdown("⏳ **⚖️ Negotiator** — resolving conflicts, fitting capacity...")
    t0 = time.time()
    negotiated = NegotiatorAgent().run(product_output, engineer_output, qa_output, sprint_context)
    t1 = time.time()
    included  = negotiated.get('included_features', [])
    excluded  = negotiated.get('excluded_features', [])
    committed = negotiated.get('total_committed_points', 0)
    capacity  = negotiated.get('effective_capacity', 40)
    goal      = negotiated.get('sprint_goal', '')
    notes     = negotiated.get('negotiation_notes', [])
    row4 = f"✅ **⚖️ Negotiator** · {len(included)} in · {len(excluded)} deferred · {committed}/{capacity}pts · `{t1-t0:.1f}s`"
    p4.markdown(row4)
    agent_rows.append(row4)
    if notes:
        with notes_placeholder.expander("📋 Negotiation notes"):
            for n in notes:
                st.markdown(f"- {n}")
    progress.progress(80, "Formatting...")

    # Agent 5
    p5.markdown("⏳ **📝 Scribe** — formatting backlog + MCP payload...")
    t0 = time.time()
    final_output = OutputAgent().run(
        negotiated, sprint_context,
        qa_output=qa_output,
        engineer_output=engineer_output,
    )
    sprint_context["engineer_output"] = engineer_output
    sprint_context["product_output"]  = product_output
    mcp_payload = MCPPayloadGenerator().generate(
        negotiated, qa_output, sprint_context, project_key=project_key
    )
    t1 = time.time()
    row5 = f"✅ **📝 Scribe** · Backlog ready · `{t1-t0:.1f}s`"
    p5.markdown(row5)
    agent_rows.append(row5)
    progress.progress(100, "Done!")

    elapsed = time.time() - start

    if md:
        try:
            output_html = md.markdown(final_output, extensions=["tables", "fenced_code"])
        except Exception:
            output_html = final_output.replace("\n", "<br>")
    else:
        output_html = final_output.replace("\n", "<br>")

    st.session_state.results = {
        "output":            final_output,
        "output_html":       output_html,
        "mcp_payload":       mcp_payload,
        "sprint_num":        sprint_num,
        "committed":         committed,
        "capacity":          capacity,
        "included":          included,
        "excluded":          excluded,
        "elapsed":           elapsed,
        "goal":              goal,
        "negotiation_notes": notes,
        "agent_rows":        agent_rows,
        "total_qa_tasks":    mcp_payload.get("summary", {}).get("total_qa_tasks", 0),
        "total_subtasks":    sum(len(story.get("subtasks", [])) for story in mcp_payload.get("stories", [])),
    }

    st.session_state.last_prd    = prd_text
    st.session_state.last_sprint = sprint_num

    progress.empty()
    st.rerun()

# Render tabs after run completes
if st.session_state.get("results"):
    r = st.session_state.results

    with tab_room:
        for row in r.get("agent_rows", []):
            st.markdown(row)
        if r.get("negotiation_notes"):
            with st.expander("📋 Negotiation notes"):
                for n in r["negotiation_notes"]:
                    st.markdown(f"- {n}")

    with tab_backlog:
        st.download_button(
            "⬇️ Download",
            data=r["output"],
            file_name=f"sprint_{r['sprint_num']}_backlog.md",
            mime="text/markdown",
        )
        output_html = r["output_html"]
        st.markdown(
            f'<div style="height:420px;overflow-y:auto;font-size:13px;line-height:1.4">{output_html}</div>',
            unsafe_allow_html=True,
        )

    with tab_mcp:
        payload = r["mcp_payload"]
        summary = payload.get("summary", {})
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Stories",  summary.get("total_stories", 0))
        m2.metric("Points",   summary.get("total_story_points", 0))
        m3.metric("Subtasks", summary.get("total_subtasks", 0))
        m4.metric("QA Tasks", summary.get("total_qa_tasks", 0))

        c1, c2, c3 = st.columns(3)
        c1.success("✅ Jira")
        c2.success("✅ Azure DevOps")
        c3.success("✅ Linear")

        epic = payload.get("epic", {})
        st.caption("EPIC")
        st.markdown(f"**{epic.get('params', {}).get('summary','')}**")

        for story in payload.get("stories", []):
            p = story.get("params", {})
            pts  = p.get("story_points", 0)
            name = p.get("summary", "")
            with st.expander(f"{name} · {pts}pts"):
                st.caption("Subtasks")
                for s in story.get("subtasks", []):
                    st.markdown(f"- {s['params']['summary']}")
                st.caption("QA Tasks")
                for q in story.get("qa_tasks", []):
                    st.markdown(f"- {q['params']['summary'].replace('QA: ', '')}")

        st.download_button(
            "⬇️ Download MCP JSON",
            data=json.dumps(payload, indent=2),
            file_name=f"sprint_{r['sprint_num']}_mcp_payload.json",
            mime="application/json",
        )

    with tab_summary:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Sprint",    r["sprint_num"])
        c2.metric("Committed", f"{r['committed']}pts")
        c3.metric("Capacity",  f"{int(r['committed']/r['capacity']*100)}%")
        c4.metric("Time",      f"{r['elapsed']:.0f}s")

        total_subtasks = sum(
            len(story.get("subtasks", []))
            for story in r["mcp_payload"].get("stories", [])
        )
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Committed User Stories", len(r["included"]))
        c2.metric("Deferred User Stories",  len(r["excluded"]))
        c3.metric("Engg Tasks",             total_subtasks)
        c4.metric("QA Tasks",               r["total_qa_tasks"])
        c5.metric("Agents",                 "5")

        st.success(f"**Goal:** {r['goal']}")

st.divider()
st.caption("Built with Azure AI Foundry · GitHub Copilot · Python")
