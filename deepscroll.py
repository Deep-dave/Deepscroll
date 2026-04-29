import streamlit as st
import requests
import json
import re
import fitz
from groq import Groq

# ═══════════════════════════════════════════════════════
#  CONFIG
# ═══════════════════════════════════════════════════════

GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
AI_MODEL = "llama-3.3-70b-versatile"

# ═══════════════════════════════════════════════════════
#  TRANSLATIONS
# ═══════════════════════════════════════════════════════

TR = {
    "EN": {
        "sub": "Scroll wisdom. Skip the noise.",
        "upload": "📁 Upload PDF",
        "classics": "📚 Classics",
        "load": "📖 Load",
        "reading": "Reading...",
        "building": "🧠 Building...",
        "next_ch": "Next →",
        "done": "🎉 Done!",
        "done_sub": "Drop another book.",
        "reset": "🔄 New Book",
        "land_t": "Drop a book. Start scrolling.",
        "land_s": "Any PDF becomes a visual journey.",
        "ai": "Write each idea in MAX 12 words in English. Be punchy like a headline.",
    },
    "DE": {
        "sub": "Scrolle Wissen. Überspringe den Lärm.",
        "upload": "📁 PDF laden",
        "classics": "📚 Klassiker",
        "load": "📖 Laden",
        "reading": "Liest...",
        "building": "🧠 Baut...",
        "next_ch": "Weiter →",
        "done": "🎉 Fertig!",
        "done_sub": "Lade ein neues Buch.",
        "reset": "🔄 Neues Buch",
        "land_t": "Buch hochladen. Loscrollen.",
        "land_s": "Jedes PDF wird zur visuellen Reise.",
        "ai": "Write each idea in MAX 12 words in German. Be punchy like a headline.",
    },
    "UA": {
        "sub": "Скроль мудрість. Пропускай шум.",
        "upload": "📁 PDF",
        "classics": "📚 Класика",
        "load": "📖 Читати",
        "reading": "Читаю...",
        "building": "🧠 Будую...",
        "next_ch": "Далі →",
        "done": "🎉 Готово!",
        "done_sub": "Кинь нову книгу.",
        "reset": "🔄 Нова книга",
        "land_t": "Кинь книгу. Скроль.",
        "land_s": "Будь-який PDF стане подорожжю.",
        "ai": "Write each idea in MAX 12 words in Ukrainian. Be punchy like a headline.",
    },
    "FR": {
        "sub": "Scrollez le savoir. Ignorez le bruit.",
        "upload": "📁 PDF",
        "classics": "📚 Classiques",
        "load": "📖 Charger",
        "reading": "Lecture...",
        "building": "🧠 Construction...",
        "next_ch": "Suivant →",
        "done": "🎉 Terminé !",
        "done_sub": "Chargez un autre livre.",
        "reset": "🔄 Nouveau livre",
        "land_t": "Déposez un livre. Scrollez.",
        "land_s": "Chaque PDF devient un voyage visuel.",
        "ai": "Write each idea in MAX 12 words in French. Be punchy like a headline.",
    },
}


def t(key):
    lang = st.session_state.get("lang", "EN")
    return TR.get(lang, TR["EN"]).get(key, key)


# ═══════════════════════════════════════════════════════
#  PAGE CONFIG
# ═══════════════════════════════════════════════════════

st.set_page_config(page_title="DeepScroll", page_icon="🧠", layout="centered")

# ═══════════════════════════════════════════════════════
#  STYLES
# ═══════════════════════════════════════════════════════

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&display=swap');

    .stApp {
        background-color: #050505;
        font-family: 'Space Grotesk', sans-serif;
    }
    #MainMenu, header, footer, .stDeployButton { visibility: hidden; display: none; }
    .block-container { padding-top: 1rem !important; max-width: 480px !important; }

    /* ── HERO CARD ── */
    .hero {
        position: relative;
        border-radius: 22px;
        overflow: hidden;
        margin-bottom: 10px;
        height: 340px;
        display: flex;
        align-items: flex-end;
        box-shadow: 0 10px 40px rgba(0,0,0,0.5);
        animation: pop 0.4s ease-out;
    }
    .hero-bg {
        position: absolute;
        top: 0; left: 0;
        width: 100%; height: 100%;
        object-fit: cover;
        z-index: 1;
        background: #111;
    }
    .hero-grad {
        position: absolute;
        top: 0; left: 0;
        width: 100%; height: 100%;
        background: linear-gradient(
            to bottom,
            rgba(0,0,0,0.05) 0%,
            rgba(0,0,0,0.4) 50%,
            rgba(0,0,0,0.92) 100%
        );
        z-index: 2;
    }
    .hero-body {
        position: relative;
        z-index: 3;
        padding: 25px;
        width: 100%;
    }
    .hero-txt {
        color: #fff;
        font-size: 1.5em;
        font-weight: 700;
        line-height: 1.4;
        text-shadow: 0 2px 12px rgba(0,0,0,0.8);
    }
    .hero-foot {
        color: rgba(255,255,255,0.4);
        font-size: 0.75em;
        margin-top: 10px;
        display: flex;
        justify-content: space-between;
    }
    .mood-tag {
        background: rgba(233,69,96,0.25);
        color: #e94560;
        padding: 2px 10px;
        border-radius: 20px;
        font-weight: 600;
    }
    @keyframes pop {
        from { opacity: 0; transform: translateY(25px) scale(0.97); }
        to   { opacity: 1; transform: translateY(0) scale(1); }
    }

    /* ── CONNECTOR ── */
    .conn { text-align: center; color: #e94560; font-size: 22px; margin: 3px 0; opacity: 0.4; }

    /* ── CHAPTER ── */
    .ch-t { color: #e94560; font-size: 1.6em; font-weight: 700; text-align: center; margin: 12px 0 3px; }
    .ch-s { color: #444; text-align: center; font-size: 0.8em; margin-bottom: 18px; }

    /* ── LANDING ── */
    .land { text-align: center; padding: 70px 20px; }
    .land h2 { color: #ccc; font-weight: 700; }
    .land p { color: #555; }

    /* ── MUSIC BUTTON (floating circle) ── */
    .music-toggle {
        position: fixed;
        bottom: 25px;
        right: 25px;
        width: 50px;
        height: 50px;
        border-radius: 50%;
        background: #e94560;
        border: none;
        color: white;
        font-size: 22px;
        cursor: pointer;
        z-index: 9999;
        box-shadow: 0 4px 20px rgba(233,69,96,0.5);
        transition: transform 0.2s, box-shadow 0.2s;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .music-toggle:hover {
        transform: scale(1.1);
        box-shadow: 0 6px 30px rgba(233,69,96,0.7);
    }

    /* ── MUSIC PANEL (popup) ── */
    .music-panel {
        position: fixed;
        bottom: 85px;
        right: 25px;
        background: #111;
        border: 1px solid #333;
        border-radius: 16px;
        padding: 18px;
        z-index: 9999;
        width: 220px;
        box-shadow: 0 8px 30px rgba(0,0,0,0.6);
        display: none;
        animation: fadeUp 0.3s ease-out;
    }
    .music-panel.open { display: block; }

    .music-panel-title {
        color: #e94560;
        font-size: 0.85em;
        font-weight: 700;
        margin-bottom: 12px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .music-panel-close {
        background: none;
        border: none;
        color: #666;
        font-size: 18px;
        cursor: pointer;
    }
    .music-panel-close:hover { color: #e94560; }

    .music-btn {
        background: #1a1a1a;
        border: 1px solid #333;
        color: #ccc;
        width: 100%;
        padding: 8px;
        border-radius: 10px;
        font-size: 16px;
        cursor: pointer;
        margin-bottom: 8px;
        font-family: 'Space Grotesk', sans-serif;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
    }
    .music-btn:hover { border-color: #e94560; color: #e94560; }

    .vol-row {
        display: flex;
        align-items: center;
        gap: 8px;
        color: #666;
        font-size: 14px;
        margin-top: 4px;
    }
    .vol-row input[type="range"] {
        flex: 1;
        accent-color: #e94560;
        height: 4px;
    }

    @keyframes fadeUp {
        from { opacity: 0; transform: translateY(10px); }
        to   { opacity: 1; transform: translateY(0); }
    }

    /* ── SPACER ── */
    .spacer { height: 100px; }
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════
#  GROQ
# ═══════════════════════════════════════════════════════

@st.cache_resource
def get_groq():
    try:
        return Groq(api_key=GROQ_API_KEY)
    except Exception as e:
        st.error(f"❌ {e}")
        return None


client = get_groq()

# ═══════════════════════════════════════════════════════
#  MUSIC TRACKS (tested & working)
# ═══════════════════════════════════════════════════════

TRACKS = {
    "dark": [
        "https://files.freemusicarchive.org/storage-freemusicarchive-org/music/no_curator/Kevin_MacLeod/Oddities/Kevin_MacLeod_-_Cryptic_Sorrow.mp3",
        "https://files.freemusicarchive.org/storage-freemusicarchive-org/music/ccCommunity/Chad_Crouch/Arps/Chad_Crouch_-_Dusk.mp3",
    ],
    "epic": [
        "https://files.freemusicarchive.org/storage-freemusicarchive-org/music/no_curator/Kevin_MacLeod/Themes/Kevin_MacLeod_-_Impact_Prelude.mp3",
        "https://files.freemusicarchive.org/storage-freemusicarchive-org/music/ccCommunity/Chad_Crouch/Arps/Chad_Crouch_-_Algorithms.mp3",
    ],
    "calm": [
        "https://files.freemusicarchive.org/storage-freemusicarchive-org/music/ccCommunity/Chad_Crouch/Arps/Chad_Crouch_-_Shipping_Lanes.mp3",
        "https://files.freemusicarchive.org/storage-freemusicarchive-org/music/no_curator/Lobo_Loco/Stimmungen/Lobo_Loco_-_05_-_Ambient_North.mp3",
    ],
    "mysterious": [
        "https://files.freemusicarchive.org/storage-freemusicarchive-org/music/no_curator/Kevin_MacLeod/Oddities/Kevin_MacLeod_-_Cryptic_Sorrow.mp3",
        "https://files.freemusicarchive.org/storage-freemusicarchive-org/music/ccCommunity/Chad_Crouch/Arps/Chad_Crouch_-_Dusk.mp3",
    ],
    "hopeful": [
        "https://files.freemusicarchive.org/storage-freemusicarchive-org/music/ccCommunity/Chad_Crouch/Arps/Chad_Crouch_-_Shipping_Lanes.mp3",
        "https://files.freemusicarchive.org/storage-freemusicarchive-org/music/ccCommunity/Chad_Crouch/Arps/Chad_Crouch_-_Algorithms.mp3",
    ],
    "intense": [
        "https://files.freemusicarchive.org/storage-freemusicarchive-org/music/no_curator/Kevin_MacLeod/Themes/Kevin_MacLeod_-_Impact_Prelude.mp3",
        "https://files.freemusicarchive.org/storage-freemusicarchive-org/music/ccCommunity/Chad_Crouch/Arps/Chad_Crouch_-_Algorithms.mp3",
    ],
    "melancholic": [
        "https://files.freemusicarchive.org/storage-freemusicarchive-org/music/ccCommunity/Chad_Crouch/Arps/Chad_Crouch_-_Dusk.mp3",
        "https://files.freemusicarchive.org/storage-freemusicarchive-org/music/ccCommunity/Chad_Crouch/Arps/Chad_Crouch_-_Shipping_Lanes.mp3",
    ],
}


def get_tracks(mood):
    return TRACKS.get(mood.lower().strip(), TRACKS["calm"])


# ═══════════════════════════════════════════════════════
#  IMAGES — picsum.photos (instant, always works)
# ═══════════════════════════════════════════════════════

def get_image_url(prompt, idx=0):
    """
    picsum.photos gives random beautiful photos instantly.
    We use the seed parameter to get consistent but different images.
    """
    seed = hash(prompt + str(idx)) % 100000
    return f"https://picsum.photos/seed/{seed}/800/600"


# ═══════════════════════════════════════════════════════
#  PDF
# ═══════════════════════════════════════════════════════

def extract_pdf(pdf_bytes):
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        txt = ""
        for p in doc:
            t = p.get_text()
            if t:
                txt += t + "\n"
        doc.close()
        return txt.strip()
    except Exception as e:
        st.error(f"❌ {e}")
        return ""


def split_chapters(text):
    if not text or len(text) < 100:
        return ["Too short."]

    pat = r'(?=(?:^|\n)\s*(?:CHAPTER|Chapter|chapter)\s+[\dIVXLCDM]+)'
    parts = [p.strip() for p in re.split(pat, text) if p.strip() and len(p.strip()) > 100]
    if len(parts) >= 2:
        return parts

    paras = re.split(r'\n\s*\n\s*\n', text)
    if len(paras) >= 3:
        chunks, cur = [], ""
        for p in paras:
            if len(cur) + len(p) > 3000 and cur:
                chunks.append(cur.strip())
                cur = p
            else:
                cur += "\n\n" + p
        if cur.strip():
            chunks.append(cur.strip())
        if len(chunks) >= 2:
            return chunks

    return [
        text[i:i + 2500].strip()
        for i in range(0, len(text), 2500)
        if len(text[i:i + 2500].strip()) > 50
    ] or [text[:3000]]


# ═══════════════════════════════════════════════════════
#  AI
# ═══════════════════════════════════════════════════════

def make_chain(chapter_text):
    if not client:
        return [{"idea": "No AI.", "visual": "abstract", "mood": "calm"}]

    ai_lang = t("ai")

    try:
        r = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": f"""You create IDEA CHAINS for people with ADHD.

CRITICAL RULES:
- Each idea is MAX 10-15 WORDS. Like a billboard. Like a meme caption.
- NO long sentences. NO filler words.
- Ideas connect logically: cause→effect, question→answer
- Generate 4-6 ideas
- visual: 2-3 English words describing a photo scene
- mood: one of: dark, epic, calm, mysterious, hopeful, intense, melancholic
- {ai_lang}

Return ONLY JSON array:
[{{"idea":"short punchy text","visual":"keywords","mood":"calm"}}]

EXAMPLES of good ideas (notice how short):
- "We fear what we don't understand."
- "Power corrupts. Absolute power? Even faster."
- "The cave was comfortable. Truth wasn't."
"""
                },
                {"role": "user", "content": f"Create idea chain:\n\n{chapter_text[:3000]}"}
            ],
            model=AI_MODEL,
            temperature=0.7,
            max_tokens=1500,
        )
        return parse_json(r.choices[0].message.content.strip())
    except Exception as e:
        st.warning(f"⚠️ {e}")
        return [{"idea": "Error.", "visual": "abstract", "mood": "calm"}]


def make_title(chapter_text):
    if not client:
        return "..."
    ai_lang = t("ai")
    try:
        r = client.chat.completions.create(
            messages=[{
                "role": "user",
                "content": f"Give this a poetic title (2-4 words). {ai_lang} Return ONLY the title:\n\n{chapter_text[:1500]}"
            }],
            model=AI_MODEL,
            temperature=0.9,
            max_tokens=20,
        )
        return r.choices[0].message.content.strip().strip('"\'')[:50]
    except Exception:
        return "..."


def parse_json(raw):
    cleaned = re.sub(r'```json\s*', '', raw)
    cleaned = re.sub(r'```\s*', '', cleaned).strip()

    for fn in [
        lambda: json.loads(cleaned),
        lambda: json.loads(re.search(r'\[.*\]', cleaned, re.DOTALL).group()),
    ]:
        try:
            r = fn()
            if isinstance(r, list):
                return validate(r)
        except (json.JSONDecodeError, AttributeError):
            pass

    objs = []
    for o in re.findall(r'\{[^{}]+\}', cleaned):
        try:
            objs.append(json.loads(o))
        except json.JSONDecodeError:
            pass
    if objs:
        return validate(objs)

    return [{"idea": raw[:200], "visual": "abstract", "mood": "calm"}]


def validate(chain):
    moods = {"dark", "epic", "calm", "mysterious", "hopeful", "intense", "melancholic"}
    out = []
    for item in chain:
        if not isinstance(item, dict):
            continue
        v = {
            "idea": str(item.get("idea", "...")),
            "visual": str(item.get("visual", item.get("visual_prompt", "abstract"))),
            "mood": str(item.get("mood", "calm")).lower().strip(),
        }
        if v["mood"] not in moods:
            v["mood"] = "calm"
        out.append(v)
    return out or [{"idea": "...", "visual": "abstract", "mood": "calm"}]


# ═══════════════════════════════════════════════════════
#  FREE BOOKS
# ═══════════════════════════════════════════════════════

BOOKS = {
    "📜 Art of War": "https://www.gutenberg.org/cache/epub/132/pg132.txt",
    "🏛️ Meditations": "https://www.gutenberg.org/cache/epub/2680/pg2680.txt",
    "🧠 Beyond Good & Evil": "https://www.gutenberg.org/cache/epub/4363/pg4363.txt",
    "👑 The Prince": "https://www.gutenberg.org/cache/epub/1232/pg1232.txt",
    "📖 Frankenstein": "https://www.gutenberg.org/cache/epub/84/pg84.txt",
    "🕳️ The Republic": "https://www.gutenberg.org/cache/epub/1497/pg1497.txt",
}


def download_book(url):
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        text = r.text
        for m in ["*** START OF", "***START OF"]:
            i = text.find(m)
            if i != -1:
                nl = text.find('\n', i)
                if nl != -1:
                    text = text[nl + 1:]
                break
        for m in ["*** END OF", "***END OF", "End of the Project Gutenberg"]:
            i = text.find(m)
            if i != -1:
                text = text[:i]
                break
        return text.strip()
    except Exception as e:
        st.error(f"❌ {e}")
        return ""


# ═══════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════

def main():
    # Init
    if "lang" not in st.session_state:
        st.session_state["lang"] = "EN"
    if "chains" not in st.session_state:
        st.session_state["chains"] = {}
    if "current_chapter" not in st.session_state:
        st.session_state["current_chapter"] = 0

    # ── HEADER ──
    st.markdown(
        "<h1 style='text-align:center;color:#e94560;font-size:2.3em;"
        "margin:8px 0 0;'>🧠 DeepScroll</h1>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<p style='text-align:center;color:#444;font-size:0.85em;"
        f"margin:4px 0 15px;'>{t('sub')}</p>",
        unsafe_allow_html=True,
    )

    # ── LANGUAGE SELECTOR ──
    lang_cols = st.columns(4)
    for i, (code, flag) in enumerate([("EN", "🇬🇧"), ("DE", "🇩🇪"), ("UA", "🇺🇦"), ("FR", "🇫🇷")]):
        with lang_cols[i]:
            current = st.session_state["lang"]
            label = f"✓ {flag}" if code == current else flag
            if st.button(label, key=f"l_{code}", use_container_width=True):
                if code != current:
                    st.session_state["lang"] = code
                    st.session_state["chains"] = {}
                    st.rerun()

    # ── SOURCE ──
    tab1, tab2 = st.tabs([t("upload"), t("classics")])
    book_text = None

    with tab1:
        up = st.file_uploader("pdf", type=["pdf"], label_visibility="collapsed")
        if up:
            if "pdf_bytes" not in st.session_state:
                st.session_state["pdf_bytes"] = up.read()
            book_text = "__PDF__"

    with tab2:
        sel = st.selectbox("b", list(BOOKS.keys()), label_visibility="collapsed")
        if st.button(t("load"), use_container_width=True):
            with st.spinner(t("reading")):
                txt = download_book(BOOKS[sel])
                if txt:
                    st.session_state["raw_text"] = txt
                    for k in ["chapters", "chains", "current_chapter", "pdf_bytes"]:
                        if k in st.session_state:
                            del st.session_state[k]
                    st.session_state["chains"] = {}
                    st.session_state["current_chapter"] = 0

        if "raw_text" in st.session_state:
            book_text = "__GUT__"

    # ── PROCESS ──
    if book_text and "chapters" not in st.session_state:
        with st.spinner(t("reading")):
            raw = (
                extract_pdf(st.session_state["pdf_bytes"])
                if book_text == "__PDF__"
                else st.session_state["raw_text"]
            )
            if raw:
                st.session_state["chapters"] = split_chapters(raw)
                st.session_state["current_chapter"] = 0
                st.session_state["chains"] = {}
                st.rerun()
            else:
                st.error("Empty.")
                return

    # ── LANDING ──
    if "chapters" not in st.session_state:
        st.markdown(f"""
            <div class="land">
                <p style="font-size:3.5em;">📖</p>
                <h2>{t('land_t')}</h2>
                <p>{t('land_s')}</p>
            </div>
        """, unsafe_allow_html=True)
        return

    # ── DISPLAY ──
    chapters = st.session_state["chapters"]
    total = len(chapters)
    cur = st.session_state["current_chapter"]

    # Nav
    c1, c2, c3 = st.columns([1, 2, 1])
    with c1:
        if cur > 0 and st.button("⬅️", use_container_width=True, key="prev"):
            st.session_state["current_chapter"] -= 1
            st.rerun()
    with c2:
        st.markdown(
            f"<p style='text-align:center;color:#555;margin-top:8px;'>"
            f"{cur + 1} / {total}</p>",
            unsafe_allow_html=True,
        )
    with c3:
        if cur < total - 1 and st.button("➡️", use_container_width=True, key="nxt"):
            st.session_state["current_chapter"] += 1
            st.rerun()

    # Generate
    chains = st.session_state["chains"]
    if cur not in chains:
        with st.spinner(t("building")):
            ch = chapters[cur]
            title = make_title(ch)
            chain = make_chain(ch)
            chains[cur] = {"title": title, "chain": chain}
            st.session_state["chains"] = chains

    data = chains[cur]
    st.markdown(f'<div class="ch-t">{data["title"]}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="ch-s">{cur + 1} / {total}</div>', unsafe_allow_html=True)

    # ── CARDS ──
    chain = data["chain"]
    for i, node in enumerate(chain):
        idea = node["idea"]
        visual = node["visual"]
        mood = node["mood"]
        img = get_image_url(visual, idx=cur * 100 + i)

        st.markdown(f"""
            <div class="hero">
                <img class="hero-bg" src="{img}" loading="lazy"
                     onerror="this.src='https://picsum.photos/seed/fallback{i}/800/600'">
                <div class="hero-grad"></div>
                <div class="hero-body">
                    <div class="hero-txt">{idea}</div>
                    <div class="hero-foot">
                        <span class="mood-tag">{mood}</span>
                        <span>{i + 1}/{len(chain)}</span>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        if i < len(chain) - 1:
            st.markdown('<div class="conn">⟱</div>', unsafe_allow_html=True)

    # ── END ──
    st.markdown("---")
    if cur < total - 1:
        if st.button(t("next_ch"), use_container_width=True, type="primary"):
            st.session_state["current_chapter"] += 1
            st.rerun()
    else:
        st.markdown(f"""
            <div style="text-align:center;padding:40px;">
                <h2 style="color:#e94560;">{t('done')}</h2>
                <p style="color:#555;">{t('done_sub')}</p>
            </div>
        """, unsafe_allow_html=True)
        if st.button(t("reset"), use_container_width=True):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()

    # ── MUSIC (floating circle + popup panel) ──
    if chain:
        mood = chain[0].get("mood", "calm")
        trks = get_tracks(mood)

        st.markdown(f"""
            <audio id="bgm" loop preload="auto" volume="0.4">
                <source src="{trks[0]}" type="audio/mpeg">
            </audio>

            <div class="music-panel" id="mPanel">
                <div class="music-panel-title">
                    🎵 Music
                    <button class="music-panel-close" onclick="
                        document.getElementById('mPanel').classList.remove('open');
                    ">✕</button>
                </div>
                <button class="music-btn" onclick="
                    var a=document.getElementById('bgm');
                    if(a.paused){{a.play();this.innerHTML='⏸ Pause';}}
                    else{{a.pause();this.innerHTML='▶ Play';}}
                ">▶ Play</button>
                <button class="music-btn" onclick="
                    var a=document.getElementById('bgm');
                    var srcs={json.dumps(trks)};
                    var ci=srcs.indexOf(a.querySelector('source').src);
                    var ni=(ci+1)%srcs.length;
                    a.querySelector('source').src=srcs[ni];
                    a.load(); a.play();
                ">⏭ Next Track</button>
                <div class="vol-row">
                    <span>🔈</span>
                    <input type="range" min="0" max="100" value="40"
                        oninput="document.getElementById('bgm').volume=this.value/100">
                    <span>🔊</span>
                </div>
            </div>

            <button class="music-toggle" onclick="
                var p=document.getElementById('mPanel');
                p.classList.toggle('open');
            ">🎵</button>
        """, unsafe_allow_html=True)

    st.markdown('<div class="spacer"></div>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()
