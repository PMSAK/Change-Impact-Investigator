import streamlit as st


def load_styles():
    st.markdown(
        """
        <style>
        :root {
            --bg: #08111f;
            --bg-deep: #060c16;
            --surface: rgba(15, 28, 47, 0.82);
            --surface-strong: #101d31;
            --surface-soft: rgba(255,255,255,0.035);
            --surface-hover: rgba(255,255,255,0.055);
            --border: rgba(148, 190, 220, 0.14);
            --border-soft: rgba(148, 190, 220, 0.085);
            --text: #edf6fb;
            --muted: #91a6b8;
            --muted-2: #64798b;
            --accent: #62dfca;
            --accent-2: #71c7ff;
            --accent-deep: #299f9a;
            --green: #67e2aa;
            --yellow: #f2cf72;
            --red: #ff7f8d;
        }

        * { box-sizing: border-box; }

        .stApp {
            min-height: 100vh;
            background:
                radial-gradient(circle at 78% -8%, rgba(98,223,202,.13), transparent 28%),
                radial-gradient(circle at 8% 8%, rgba(113,199,255,.10), transparent 25%),
                radial-gradient(circle at 50% 55%, rgba(36,83,117,.07), transparent 35%),
                linear-gradient(180deg, #091321 0%, var(--bg) 48%, var(--bg-deep) 100%);
            color: var(--text);
        }

        .stApp::before {
            content: "";
            position: fixed;
            inset: 0;
            pointer-events: none;
            opacity: .38;
            background-image:
                linear-gradient(rgba(148,190,220,.022) 1px, transparent 1px),
                linear-gradient(90deg, rgba(148,190,220,.022) 1px, transparent 1px);
            background-size: 72px 72px;
            mask-image: linear-gradient(to bottom, black, transparent 78%);
        }

        .block-container {
            max-width: 1160px;
            padding-top: 2rem;
            padding-bottom: 5rem;
        }

        header[data-testid="stHeader"] {
            background: transparent;
        }

        /* ---------- Streamlit controls ---------- */

        label[data-testid="stWidgetLabel"] p {
            color: #b8c9d6 !important;
            font-size: 12px !important;
            font-weight: 650 !important;
            letter-spacing: .1px;
        }

        div[data-testid="stTextInput"] input,
        div[data-testid="stTextArea"] textarea {
            background: rgba(9, 20, 34, .88) !important;
            border: 1px solid var(--border) !important;
            color: var(--text) !important;
            border-radius: 12px !important;
            box-shadow: inset 0 1px 0 rgba(255,255,255,.025) !important;
            transition: border-color .18s ease, box-shadow .18s ease, background .18s ease;
        }

        div[data-testid="stTextInput"] input {
            min-height: 48px;
        }

        div[data-testid="stTextArea"] textarea {
            min-height: 112px;
        }

        div[data-testid="stTextInput"] input:hover,
        div[data-testid="stTextArea"] textarea:hover {
            background: rgba(11, 25, 42, .96) !important;
            border-color: rgba(148,190,220,.22) !important;
        }

        div[data-testid="stTextInput"] input:focus,
        div[data-testid="stTextArea"] textarea:focus {
            border-color: rgba(98,223,202,.58) !important;
            box-shadow: 0 0 0 1px rgba(98,223,202,.14), 0 0 26px rgba(98,223,202,.07) !important;
        }

        div[data-testid="stTextInput"] input::placeholder,
        div[data-testid="stTextArea"] textarea::placeholder {
            color: #607688 !important;
        }

        /* Form container */
        div[data-testid="stForm"] {
            border: 0 !important;
            padding: 0 !important;
        }

        /* Primary action */
        div.stButton > button,
        button[kind="primary"] {
            min-height: 46px !important;
            border: 1px solid rgba(98,223,202,.20) !important;
            border-radius: 11px !important;
            background: linear-gradient(135deg, #45cbb7, #55bde8) !important;
            color: #06131a !important;
            font-weight: 800 !important;
            letter-spacing: -.05px !important;
            box-shadow: 0 12px 30px rgba(61,194,188,.16) !important;
            transition: transform .16s ease, box-shadow .16s ease, filter .16s ease !important;
        }

        div.stButton > button:hover,
        button[kind="primary"]:hover {
            filter: brightness(1.06) !important;
            transform: translateY(-1px);
            box-shadow: 0 16px 36px rgba(61,194,188,.23) !important;
        }

        div.stButton > button:active,
        button[kind="primary"]:active {
            transform: translateY(0);
        }

        /* Secondary buttons */
        button[kind="secondary"] {
            border: 1px solid var(--border) !important;
            border-radius: 10px !important;
            background: rgba(255,255,255,.035) !important;
            color: #b8cad7 !important;
            font-weight: 650 !important;
        }

        button[kind="secondary"]:hover {
            background: rgba(255,255,255,.06) !important;
            border-color: rgba(148,190,220,.24) !important;
            color: #edf6fb !important;
        }

        /* Containers / expanders */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background: linear-gradient(145deg, rgba(17,32,51,.88), rgba(10,22,37,.88)) !important;
            border: 1px solid var(--border) !important;
            border-radius: 16px !important;
            box-shadow: 0 18px 50px rgba(0,0,0,.14) !important;
        }

        details[data-testid="stExpander"] {
            background: rgba(10, 23, 38, .70) !important;
            border: 1px solid var(--border-soft) !important;
            border-radius: 13px !important;
        }

        details[data-testid="stExpander"] summary p {
            color: #cbd9e3 !important;
            font-weight: 650 !important;
        }

        details[data-testid="stExpander"] summary:hover {
            background: rgba(255,255,255,.025) !important;
        }

        div[data-testid="stAlert"] {
            border-radius: 11px !important;
            border: 1px solid var(--border) !important;
        }

        /* ---------- Brand ---------- */

        .brand-row {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .brand-mark {
            width: 40px;
            height: 40px;
            border-radius: 11px;
            display: grid;
            place-items: center;
            color: #06131a;
            font-size: 19px;
            font-weight: 900;
            background: linear-gradient(135deg, #62dfca, #71c7ff);
            box-shadow: 0 10px 28px rgba(73,205,194,.18);
        }

        .brand-name {
            font-size: 17px;
            line-height: 1;
            font-weight: 760;
            letter-spacing: -.35px;
            color: #eaf4f8;
        }

        .brand-mini {
            margin-top: 5px;
            color: #708799;
            font-size: 10px;
            letter-spacing: .65px;
            text-transform: uppercase;
        }

        /* ---------- Landing ---------- */

        .hero {
            text-align: center;
            padding: 4.7rem 0 2.15rem;
        }

        .eyebrow {
            display: inline-flex;
            align-items: center;
            gap: 7px;
            padding: 7px 11px;
            border-radius: 999px;
            background: rgba(98,223,202,.075);
            border: 1px solid rgba(98,223,202,.17);
            color: #83e8d7;
            font-size: 10px;
            font-weight: 800;
            letter-spacing: 1px;
            text-transform: uppercase;
        }

        .hero h1 {
            margin: 17px 0 12px;
            color: #f0f7fa;
            font-size: clamp(42px, 5.2vw, 68px);
            line-height: .99;
            letter-spacing: -3.2px;
            font-weight: 820;
        }

        .hero h1 span {
            background: linear-gradient(100deg, #f0f7fa 20%, #83dfd1 63%, #7ac8f4 100%);
            -webkit-background-clip: text;
            background-clip: text;
            color: transparent;
        }

        .hero-copy {
            max-width: 670px;
            margin: 0 auto;
            color: #8fa5b5;
            font-size: 15px;
            line-height: 1.7;
        }

        .analysis-card {
            max-width: 900px;
            margin: 1rem auto 0;
            padding: 26px;
            border-radius: 18px;
            background:
                radial-gradient(circle at 100% 0%, rgba(98,223,202,.055), transparent 28%),
                linear-gradient(145deg, rgba(18,34,54,.92), rgba(10,22,37,.92));
            border: 1px solid rgba(148,190,220,.14);
            box-shadow: 0 30px 90px rgba(0,0,0,.25), 0 0 60px rgba(68,177,192,.035);
            text-align: left;
        }

        .card-heading {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
            margin-bottom: 18px;
        }

        .card-heading-title {
            color: #e9f3f7;
            font-size: 14px;
            font-weight: 760;
        }

        .card-heading-meta {
            color: #657c8e;
            font-size: 10px;
        }

        .hint-row {
            display: flex;
            flex-wrap: wrap;
            gap: 7px;
            margin-top: 14px;
        }

        .hint {
            padding: 6px 9px;
            border: 1px solid rgba(148,190,220,.09);
            border-radius: 8px;
            background: rgba(255,255,255,.022);
            color: #718899;
            font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
            font-size: 9px;
        }

        .feature {
            height: 100%;
            padding: 17px 18px;
            border: 1px solid rgba(148,190,220,.085);
            border-radius: 14px;
            background: rgba(13,28,46,.56);
            transition: transform .16s ease, border-color .16s ease, background .16s ease;
        }

        .feature:hover {
            transform: translateY(-2px);
            border-color: rgba(98,223,202,.18);
            background: rgba(15,33,52,.76);
        }

        .feature-icon {
            color: var(--accent);
            font-size: 17px;
            margin-bottom: 9px;
        }

        .feature-title {
            color: #dcebf1;
            font-size: 13px;
            font-weight: 720;
            margin-bottom: 4px;
        }

        .feature-copy {
            color: #718899;
            font-size: 11px;
            line-height: 1.55;
        }

        .footer-note,
        .bottom-note {
            text-align: center;
            color: #526a7c;
            font-size: 10px;
            letter-spacing: .15px;
        }

        .footer-note { margin-top: 34px; }
        .bottom-note { margin-top: 38px; }

        /* ---------- Results ---------- */

        .results-top {
            padding: 2rem 0 1.25rem;
        }

        .target-kicker {
            color: #6e8799;
            font-size: 9px;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 1.25px;
            margin-bottom: 8px;
        }

        .target-name {
            color: #eef7fa;
            font-size: clamp(31px, 3.8vw, 47px);
            line-height: 1;
            font-weight: 820;
            letter-spacing: -2px;
            margin-bottom: 10px;
        }

        .target-path {
            display: inline-flex;
            align-items: center;
            padding: 7px 10px;
            border-radius: 8px;
            background: rgba(255,255,255,.03);
            border: 1px solid rgba(148,190,220,.09);
            color: #849bab;
            font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
            font-size: 11px;
        }

        .risk-pill {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 7px 10px;
            border-radius: 999px;
            font-size: 9px;
            font-weight: 850;
            letter-spacing: .7px;
            text-transform: uppercase;
        }

        .risk-pill.low {
            color: #74e5b1;
            background: rgba(103,226,170,.075);
            border: 1px solid rgba(103,226,170,.15);
        }

        .risk-pill.medium {
            color: #f0d477;
            background: rgba(242,207,114,.075);
            border: 1px solid rgba(242,207,114,.15);
        }

        .risk-pill.high {
            color: #ff8793;
            background: rgba(255,127,141,.075);
            border: 1px solid rgba(255,127,141,.15);
        }

        .metric {
            height: 100%;
            padding: 17px 18px;
            border-radius: 14px;
            background: linear-gradient(145deg, rgba(17,34,54,.82), rgba(10,23,38,.82));
            border: 1px solid rgba(148,190,220,.10);
            box-shadow: inset 0 1px 0 rgba(255,255,255,.018);
        }

        .metric-label {
            color: #708799;
            font-size: 9px;
            font-weight: 760;
            letter-spacing: .9px;
            text-transform: uppercase;
            margin-bottom: 10px;
        }

        .metric-value {
            color: #eaf4f8;
            font-size: 27px;
            line-height: 1;
            font-weight: 800;
            letter-spacing: -1px;
        }

        .metric-value.low { color: var(--green); }
        .metric-value.medium { color: var(--yellow); }
        .metric-value.high { color: var(--red); }

        .section-heading {
            display: flex;
            align-items: flex-start;
            gap: 10px;
            margin: 34px 0 13px;
        }

        .section-heading h2 {
            margin: 0;
            color: #e5f0f4;
            font-size: 17px;
            letter-spacing: -.35px;
        }

        .section-heading p {
            margin: 3px 0 0;
            color: #667d8f;
            font-size: 10px;
            line-height: 1.45;
        }

        .section-dot {
            width: 7px;
            height: 7px;
            margin-top: 7px;
            flex: 0 0 auto;
            border-radius: 50%;
            background: var(--accent);
            box-shadow: 0 0 13px rgba(98,223,202,.48);
        }

        /* AI container generated by Streamlit */
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.ai-label) {
            position: relative;
            overflow: hidden;
            background:
                radial-gradient(circle at 100% 0%, rgba(98,223,202,.07), transparent 28%),
                linear-gradient(145deg, rgba(18,37,57,.96), rgba(10,23,38,.96)) !important;
            border-color: rgba(98,223,202,.15) !important;
        }

        div[data-testid="stVerticalBlockBorderWrapper"]:has(.ai-label)::before {
            content: "";
            position: absolute;
            left: 0;
            top: 0;
            bottom: 0;
            width: 3px;
            background: linear-gradient(180deg, var(--accent), var(--accent-2));
        }

        .ai-label {
            color: #78dfcf;
            font-size: 9px;
            font-weight: 850;
            letter-spacing: 1px;
            text-transform: uppercase;
            margin-bottom: 12px;
        }

        .evidence-card {
            height: 100%;
            padding: 19px;
            border-radius: 15px;
            background: linear-gradient(145deg, rgba(15,31,50,.84), rgba(9,22,36,.84));
            border: 1px solid rgba(148,190,220,.095);
            box-shadow: inset 0 1px 0 rgba(255,255,255,.015);
        }

        .evidence-title {
            color: #dcebf1;
            font-size: 13px;
            font-weight: 750;
            margin-bottom: 4px;
        }

        .evidence-subtitle {
            color: #60788a;
            font-size: 9px;
            margin-bottom: 14px;
        }

        .entity {
            padding: 11px 0;
            border-bottom: 1px solid rgba(148,190,220,.065);
        }

        .entity:last-child { border-bottom: none; }

        .entity-name {
            color: #d8e7ed;
            font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
            font-size: 11px;
            font-weight: 650;
        }

        .entity-meta {
            margin-top: 4px;
            color: #607789;
            font-size: 9px;
            line-height: 1.45;
        }

        .empty-state {
            padding: 18px 0 6px;
            color: #5c7385;
            font-size: 10px;
        }

        .test-summary {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 6px;
            margin-bottom: 10px;
        }

        .test-stat {
            padding: 9px;
            border-radius: 9px;
            background: rgba(255,255,255,.023);
            border: 1px solid rgba(148,190,220,.065);
        }

        .test-stat-value {
            color: #e8f1f4;
            font-size: 16px;
            font-weight: 800;
        }

        .test-stat-label {
            color: #607789;
            font-size: 7px;
            text-transform: uppercase;
            letter-spacing: .65px;
            margin-top: 3px;
        }

        .test-pass { color: var(--green); }
        .test-fail { color: var(--red); }

        .gap-card,
        .clean-card {
            padding: 15px 17px;
            border-radius: 12px;
            font-size: 11px;
            line-height: 1.55;
        }

        .gap-card {
            background: rgba(242,207,114,.055);
            border: 1px solid rgba(242,207,114,.13);
            color: #d8c987;
        }

        .clean-card {
            background: rgba(103,226,170,.045);
            border: 1px solid rgba(103,226,170,.11);
            color: #91d8b7;
        }

        .timeline-item {
            position: relative;
            padding: 0 0 18px 19px;
            border-left: 1px solid rgba(148,190,220,.11);
        }

        .timeline-item:last-child { padding-bottom: 0; }

        .timeline-dot {
            position: absolute;
            left: -4px;
            top: 2px;
            width: 7px;
            height: 7px;
            border-radius: 50%;
            background: var(--accent-2);
            box-shadow: 0 0 0 4px rgba(113,199,255,.07);
        }

        .timeline-meta {
            color: #62798b;
            font-size: 9px;
            margin-bottom: 4px;
        }

        .timeline-message {
            color: #c6d6df;
            font-size: 11px;
        }

        .question-box {
            padding: 13px 15px;
            border-radius: 10px;
            background: rgba(255,255,255,.023);
            border: 1px solid rgba(148,190,220,.075);
            color: #a9bcc8;
            font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
            font-size: 10px;
            line-height: 1.55;
        }

        /* Markdown generated inside AI answer */
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.ai-label) p,
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.ai-label) li {
            color: #c9d8df;
            line-height: 1.65;
            font-size: 13px;
        }

        div[data-testid="stVerticalBlockBorderWrapper"]:has(.ai-label) strong {
            color: #eef7fa;
        }

        /* Avoid Streamlit's excessive empty spacing */
        div[data-testid="stVerticalBlock"] > div:has(> div.stMarkdown) {
            gap: .42rem;
        }

        @media (max-width: 760px) {
            .block-container { padding-top: 1.25rem; }
            .hero { padding-top: 3rem; }
            .hero h1 { letter-spacing: -2px; }
            .analysis-card { padding: 18px; }
            .card-heading { align-items: flex-start; flex-direction: column; }
            .test-summary { grid-template-columns: repeat(2, 1fr); }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
