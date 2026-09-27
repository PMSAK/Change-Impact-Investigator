import streamlit as st

def load_styles():
    st.markdown(
    """
    <style>
        :root {
            --bg: #07080c;
            --surface: rgba(17, 18, 25, 0.78);
            --surface-strong: #111219;
            --surface-soft: rgba(255,255,255,0.035);
            --border: rgba(255,255,255,0.085);
            --border-soft: rgba(255,255,255,0.055);
            --text: #f5f5f7;
            --muted: #8e92a3;
            --muted-2: #666b7c;
            --purple: #7c5cff;
            --purple-2: #9b7cff;
            --green: #5fdda0;
            --yellow: #f2ca62;
            --red: #ff727b;
        }

        .stApp {
            background:
                radial-gradient(circle at 78% -5%, rgba(124, 92, 255, 0.18), transparent 27%),
                radial-gradient(circle at 13% 0%, rgba(84, 102, 255, 0.08), transparent 24%),
                linear-gradient(180deg, #090a10 0%, #07080c 55%, #06070a 100%);
            color: var(--text);
        }

        .stApp::before {
            content: "";
            position: fixed;
            inset: 0;
            pointer-events: none;
            background-image: linear-gradient(rgba(255,255,255,.018) 1px, transparent 1px),
                              linear-gradient(90deg, rgba(255,255,255,.018) 1px, transparent 1px);
            background-size: 72px 72px;
            mask-image: linear-gradient(to bottom, rgba(0,0,0,.65), transparent 70%);
        }

        .block-container {
            max-width: 1220px;
            padding-top: 2.4rem;
            padding-bottom: 5rem;
        }

        header[data-testid="stHeader"] {
            background: transparent;
        }

        /* Streamlit labels */
        label[data-testid="stWidgetLabel"] p {
            color: #b8bbc7 !important;
            font-size: 13px !important;
            font-weight: 600 !important;
        }

        div[data-testid="stTextInput"] input,
        div[data-testid="stTextArea"] textarea {
            background: rgba(25, 26, 35, 0.92) !important;
            border: 1px solid var(--border) !important;
            color: #f1f1f5 !important;
            border-radius: 12px !important;
            box-shadow: inset 0 1px 0 rgba(255,255,255,.025) !important;
        }

        div[data-testid="stTextInput"] input {
            min-height: 48px;
        }

        div[data-testid="stTextArea"] textarea {
            min-height: 112px;
        }

        div[data-testid="stTextInput"] input:focus,
        div[data-testid="stTextArea"] textarea:focus {
            border-color: rgba(124, 92, 255, .75) !important;
            box-shadow: 0 0 0 1px rgba(124, 92, 255, .18), 0 0 28px rgba(124,92,255,.08) !important;
        }

        div[data-testid="stTextInput"] input::placeholder,
        div[data-testid="stTextArea"] textarea::placeholder {
            color: #5e6272 !important;
        }

        /* Buttons */
        div.stButton > button {
            border: 1px solid rgba(255,255,255,.08) !important;
            border-radius: 11px !important;
            min-height: 44px !important;
            background: linear-gradient(135deg, #7058f7, #8a4df5) !important;
            color: white !important;
            font-weight: 700 !important;
            box-shadow: 0 10px 28px rgba(105, 76, 235, .22) !important;
            transition: transform .15s ease, box-shadow .15s ease, filter .15s ease;
        }

        div.stButton > button:hover {
            filter: brightness(1.08);
            transform: translateY(-1px);
            box-shadow: 0 14px 34px rgba(105, 76, 235, .30) !important;
        }

        div.stButton > button:active {
            transform: translateY(0);
        }

        /* Bordered Streamlit containers */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background: rgba(14,15,21,.72) !important;
            border: 1px solid rgba(255,255,255,.065) !important;
            border-radius: 15px !important;
        }

        /* Expander */
        details[data-testid="stExpander"] {
            background: rgba(15,16,22,.72) !important;
            border: 1px solid var(--border-soft) !important;
            border-radius: 14px !important;
        }

        details[data-testid="stExpander"] summary p {
            color: #d9dbe3 !important;
            font-weight: 650 !important;
        }

        /* Alerts */
        div[data-testid="stAlert"] {
            border-radius: 12px !important;
        }

        /* Remove excessive Streamlit spacing */
        div[data-testid="stVerticalBlock"] > div:has(> div.stMarkdown) {
            gap: .45rem;
        }

        /* ------------------------------------------------------------ */
        /* Brand */
        /* ------------------------------------------------------------ */

        .brand-row {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .brand-mark {
            width: 40px;
            height: 40px;
            border-radius: 12px;
            display: grid;
            place-items: center;
            color: white;
            font-size: 20px;
            font-weight: 800;
            background: linear-gradient(135deg, #6f5af8, #914ef4);
            box-shadow: 0 10px 32px rgba(113, 83, 244, .28);
        }

        .brand-name {
            font-size: 18px;
            line-height: 1;
            font-weight: 750;
            letter-spacing: -.35px;
            color: #f4f4f7;
        }

        .brand-mini {
            margin-top: 5px;
            color: #777b8b;
            font-size: 11px;
            letter-spacing: .35px;
            text-transform: uppercase;
        }

        /* ------------------------------------------------------------ */
        /* Landing */
        /* ------------------------------------------------------------ */

        .hero {
            text-align: center;
            padding: 5.1rem 0 2.5rem;
        }

        .eyebrow {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 7px 11px;
            border-radius: 999px;
            background: rgba(124,92,255,.09);
            border: 1px solid rgba(124,92,255,.18);
            color: #aa9aff;
            font-size: 11px;
            font-weight: 750;
            letter-spacing: .9px;
            text-transform: uppercase;
        }

        .hero h1 {
            margin: 18px 0 10px;
            color: #f7f7fa;
            font-size: clamp(42px, 5.3vw, 70px);
            line-height: .98;
            letter-spacing: -3.4px;
            font-weight: 820;
        }

        .hero h1 span {
            background: linear-gradient(100deg, #f7f7fa 20%, #a892ff 78%, #8d72ff 100%);
            -webkit-background-clip: text;
            background-clip: text;
            color: transparent;
        }

        .hero-copy {
            max-width: 690px;
            margin: 0 auto;
            color: #9296a7;
            font-size: 16px;
            line-height: 1.65;
        }

        .analysis-card {
            max-width: 900px;
            margin: 1.2rem auto 0;
            padding: 26px;
            border-radius: 18px;
            background: linear-gradient(180deg, rgba(21,22,31,.90), rgba(13,14,20,.88));
            border: 1px solid rgba(255,255,255,.095);
            box-shadow: 0 30px 90px rgba(0,0,0,.30), 0 0 60px rgba(110,82,240,.06);
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
            color: #f0f0f4;
            font-size: 14px;
            font-weight: 750;
        }

        .card-heading-meta {
            color: #666b7b;
            font-size: 11px;
        }

        .hint-row {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: 16px;
        }

        .hint {
            padding: 7px 10px;
            border: 1px solid rgba(255,255,255,.06);
            border-radius: 8px;
            background: rgba(255,255,255,.025);
            color: #777c8d;
            font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
            font-size: 10px;
        }

        .feature-grid {
            max-width: 900px;
            margin: 28px auto 0;
        }

        .feature {
            height: 100%;
            padding: 17px 18px;
            border: 1px solid rgba(255,255,255,.055);
            border-radius: 14px;
            background: rgba(255,255,255,.018);
        }

        .feature-icon {
            color: #a08eff;
            font-size: 17px;
            margin-bottom: 9px;
        }

        .feature-title {
            color: #e5e5ea;
            font-size: 13px;
            font-weight: 700;
            margin-bottom: 4px;
        }

        .feature-copy {
            color: #737788;
            font-size: 11px;
            line-height: 1.5;
        }

        .footer-note {
            text-align: center;
            margin-top: 38px;
            color: #4e5261;
            font-size: 11px;
            letter-spacing: .2px;
        }

        /* ------------------------------------------------------------ */
        /* Results */
        /* ------------------------------------------------------------ */

        .results-top {
            padding: 2rem 0 1.35rem;
        }

        .back-label {
            color: #777b8c;
            font-size: 12px;
            margin-bottom: 20px;
        }

        .target-kicker {
            color: #777b8c;
            font-size: 10px;
            font-weight: 750;
            text-transform: uppercase;
            letter-spacing: 1.15px;
            margin-bottom: 8px;
        }

        .target-name {
            color: #f6f6f9;
            font-size: clamp(32px, 4vw, 48px);
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
            background: rgba(255,255,255,.035);
            border: 1px solid rgba(255,255,255,.055);
            color: #8d91a2;
            font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
            font-size: 12px;
        }

        .risk-pill {
            display: inline-flex;
            align-items: center;
            gap: 7px;
            padding: 7px 10px;
            border-radius: 999px;
            font-size: 10px;
            font-weight: 800;
            letter-spacing: .7px;
            text-transform: uppercase;
        }

        .risk-pill.low {
            color: #6ee2a8;
            background: rgba(95,221,160,.09);
            border: 1px solid rgba(95,221,160,.16);
        }

        .risk-pill.medium {
            color: #f4d06a;
            background: rgba(242,202,98,.09);
            border: 1px solid rgba(242,202,98,.16);
        }

        .risk-pill.high {
            color: #ff7f87;
            background: rgba(255,114,123,.09);
            border: 1px solid rgba(255,114,123,.16);
        }

        .metric {
            height: 100%;
            padding: 18px 19px;
            border-radius: 14px;
            background: rgba(16,17,24,.78);
            border: 1px solid rgba(255,255,255,.07);
            box-shadow: inset 0 1px 0 rgba(255,255,255,.018);
        }

        .metric-label {
            color: #777b8c;
            font-size: 10px;
            font-weight: 750;
            letter-spacing: .9px;
            text-transform: uppercase;
            margin-bottom: 11px;
        }

        .metric-value {
            color: #f4f4f7;
            font-size: 28px;
            line-height: 1;
            font-weight: 800;
            letter-spacing: -1px;
        }

        .metric-value.low { color: var(--green); }
        .metric-value.medium { color: var(--yellow); }
        .metric-value.high { color: var(--red); }

        .section-heading {
            display: flex;
            align-items: center;
            gap: 9px;
            margin: 34px 0 13px;
        }

        .section-heading h2 {
            margin: 0;
            color: #eeeeF2;
            font-size: 18px;
            letter-spacing: -.4px;
        }

        .section-heading p {
            margin: 2px 0 0;
            color: #666b7a;
            font-size: 11px;
        }

        .section-dot {
            width: 7px;
            height: 7px;
            border-radius: 50%;
            background: #866cfb;
            box-shadow: 0 0 14px rgba(134,108,251,.55);
        }

        .ai-card {
            position: relative;
            overflow: hidden;
            padding: 26px 28px;
            border-radius: 17px;
            background:
                radial-gradient(circle at 100% 0%, rgba(124,92,255,.10), transparent 30%),
                linear-gradient(145deg, rgba(23,22,34,.96), rgba(13,14,20,.96));
            border: 1px solid rgba(124,92,255,.18);
            box-shadow: 0 20px 60px rgba(0,0,0,.20);
        }

        .ai-card::before {
            content: "";
            position: absolute;
            top: 0;
            left: 0;
            width: 3px;
            height: 100%;
            background: linear-gradient(180deg, #8a70ff, #5e45d9);
        }

        .ai-label {
            color: #a28eff;
            font-size: 10px;
            font-weight: 800;
            letter-spacing: 1px;
            text-transform: uppercase;
            margin-bottom: 16px;
        }

        .evidence-card {
            height: 100%;
            padding: 20px;
            border-radius: 15px;
            background: rgba(14,15,21,.78);
            border: 1px solid rgba(255,255,255,.065);
        }

        .evidence-title {
            color: #e8e8ed;
            font-size: 14px;
            font-weight: 750;
            margin-bottom: 4px;
        }

        .evidence-subtitle {
            color: #626777;
            font-size: 10px;
            margin-bottom: 15px;
        }

        .entity {
            padding: 12px 0;
            border-bottom: 1px solid rgba(255,255,255,.055);
        }

        .entity:last-child { border-bottom: none; }

        .entity-name {
            color: #e4e4ea;
            font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
            font-size: 12px;
            font-weight: 650;
        }

        .entity-meta {
            margin-top: 4px;
            color: #676c7c;
            font-size: 10px;
            line-height: 1.45;
        }

        .empty-state {
            padding: 18px 0 6px;
            color: #5f6474;
            font-size: 11px;
        }

        .test-summary {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 7px;
            margin-bottom: 10px;
        }

        .test-stat {
            padding: 10px;
            border-radius: 9px;
            background: rgba(255,255,255,.025);
            border: 1px solid rgba(255,255,255,.045);
        }

        .test-stat-value {
            color: #ececf1;
            font-size: 17px;
            font-weight: 800;
        }

        .test-stat-label {
            color: #626777;
            font-size: 8px;
            text-transform: uppercase;
            letter-spacing: .65px;
            margin-top: 3px;
        }

        .test-pass { color: var(--green); }
        .test-fail { color: var(--red); }

        .gap-card {
            padding: 16px 18px;
            border-radius: 13px;
            background: rgba(242,202,98,.055);
            border: 1px solid rgba(242,202,98,.13);
            color: #d6c98e;
            font-size: 12px;
            line-height: 1.55;
        }

        .clean-card {
            padding: 16px 18px;
            border-radius: 13px;
            background: rgba(95,221,160,.045);
            border: 1px solid rgba(95,221,160,.11);
            color: #91d5b3;
            font-size: 12px;
        }

        .timeline-item {
            position: relative;
            padding: 0 0 18px 19px;
            border-left: 1px solid rgba(255,255,255,.09);
        }

        .timeline-item:last-child {
            padding-bottom: 0;
        }

        .timeline-dot {
            position: absolute;
            left: -4px;
            top: 2px;
            width: 7px;
            height: 7px;
            border-radius: 50%;
            background: #866cfb;
            box-shadow: 0 0 0 4px rgba(134,108,251,.08);
        }

        .timeline-meta {
            color: #696e7e;
            font-size: 10px;
            margin-bottom: 4px;
        }

        .timeline-message {
            color: #cfd1d9;
            font-size: 12px;
        }

        .question-box {
            padding: 14px 16px;
            border-radius: 11px;
            background: rgba(255,255,255,.025);
            border: 1px solid rgba(255,255,255,.055);
            color: #aeb2bf;
            font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
            font-size: 11px;
            line-height: 1.55;
        }

        .bottom-note {
            text-align: center;
            color: #4f5362;
            font-size: 10px;
            margin-top: 38px;
        }

        @media (max-width: 760px) {
            .block-container { padding-top: 1.3rem; }
            .hero { padding-top: 3rem; }
            .hero h1 { letter-spacing: -2px; }
            .analysis-card { padding: 18px; }
            .test-summary { grid-template-columns: repeat(2, 1fr); }
        }
    </style>
    """,
    unsafe_allow_html=True,
)