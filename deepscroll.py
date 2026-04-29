import streamlit as st
import streamlit.components.v1 as components
import requests
import json
import re
import hashlib
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
        "reading": "📚 Reading...",
        "building": "🧠 Building idea chain...",
        "next_ch": "Next Chapter →",
        "done": "🎉 Done!",
        "done_sub": "Drop another book.",
        "reset": "🔄 New Book",
        "land_t": "Drop a book. Start scrolling.",
        "land_s": "Any PDF becomes a visual journey.",
        "music": "🎵 Music",
        "music_on": "🔊 Music ON",
        "music_off": "🔇 Music OFF",
        "tap": "tap",
        "what_means": "What it means",
        "example_label": "Example",
        "takeaway_label": "Takeaway",
        "ai": "Write hook in MAX 12 words in English. Write meaning, example, takeaway in English.",
    },
    "DE": {
        "sub": "Scrolle Wissen. Kein Lärm.",
        "upload": "📁 PDF laden",
        "classics": "📚 Klassiker",
        "load": "📖 Laden",
        "reading": "📚 Liest...",
        "building": "🧠 Baut Ideenkette...",
        "next_ch": "Weiter →",
        "done": "🎉 Fertig!",
        "done_sub": "Lade ein neues Buch.",
        "reset": "🔄 Neues Buch",
        "land_t": "Buch hochladen. Loscrollen.",
        "land_s": "Jedes PDF wird zur Reise.",
        "music": "🎵 Musik",
        "music_on": "🔊 Musik AN",
        "music_off": "🔇 Musik AUS",
        "tap": "tippen",
        "what_means": "Was es bedeutet",
        "example_label": "Beispiel",
        "takeaway_label": "Fazit",
        "ai": "Write hook in MAX 12 words in German. Write meaning, example, takeaway in German.",
    },
    "UA": {
        "sub": "Скроль мудрість. Без шуму.",
        "upload": "📁 PDF",
        "classics": "📚 Класика",
        "load": "📖 Читати",
        "reading": "📚 Читаю...",
        "building": "🧠 Будую ланцюг ідей...",
        "next_ch": "Далі →",
        "done": "🎉 Готово!",
        "done_sub": "Кинь нову книгу.",
        "reset": "🔄 Нова книга",
        "land_t": "Кинь книгу. Скроль.",
        "land_s": "Будь-який PDF стане подорожжю.",
        "music": "🎵 Музика",
        "music_on": "🔊 Музика ВКЛ",
        "music_off": "🔇 Музика ВИКЛ",
        "tap": "тап",
        "what_means": "Що це значить",
        "example_label": "Приклад",
        "takeaway_label": "Висновок",
        "ai": "Write hook in MAX 12 words in Ukrainian. Write meaning, example, takeaway in Ukrainian.",
    },
    "FR": {
        "sub": "Scrollez le savoir. Zéro bruit.",
        "upload": "📁 PDF",
        "classics": "📚 Classiques",
        "load": "📖 Charger",
        "reading": "📚 Lecture...",
        "building": "🧠 Construction...",
        "next_ch": "Suivant →",
        "done": "🎉 Terminé !",
        "done_sub": "Chargez un autre livre.",
        "reset": "🔄 Nouveau",
        "land_t": "Déposez un livre. Scrollez.",
        "land_s": "Chaque PDF devient un voyage.",
        "music": "🎵 Musique",
        "music_on": "🔊 Musique ON",
        "music_off": "🔇 Musique OFF",
        "tap": "appuyez",
        "what_means": "Ce que ça veut dire",
        "example_label": "Exemple",
        "takeaway_label": "À retenir",
        "ai": "Write hook in MAX 12 words in French. Write meaning, example, takeaway in French.",
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
    #MainMenu, header, footer, .stDeployButton { display: none !important; }
    .block-container { padding-top: 1rem !important; max-width: 480px !important; }

    .conn {
        text-align: center;
        color: #e94560;
        font-size: 22px;
        margin: 6px 0;
        opacity: 0.4;
    }
    .ch-t {
        color: #e94560;
        font-size: 1.6em;
        font-weight: 700;
        text-align: center;
        margin: 12px 0 3px;
    }
    .ch-s {
        color: #444;
        text-align: center;
        font-size: 0.8em;
        margin-bottom: 18px;
    }
    .land {
        text-align: center;
        padding: 70px 20px;
    }
    .land h2 { color: #ccc; font-weight: 700; }
    .land p { color: #555; }

    .stButton > button[kind="primary"] {
        background: #e94560 !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        margin-top: 10px !important;
        padding: 14px !important;
        font-size: 1em !important;
        font-family: 'Space Grotesk', sans-serif !important;
        font-weight: 600 !important;
    }
    .stButton > button[kind="primary"]:hover {
        background: #d63851 !important;
    }
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
#  MUSIC
# ═══════════════════════════════════════════════════════

MUSIC = {
    "dark": [
        "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-8.mp3",
        "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-11.mp3",
        "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-14.mp3",
    ],
    "epic": [
        "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-3.mp3",
        "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-6.mp3",
        "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-9.mp3",
    ],
    "calm": [
        "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-3.mp3",
        "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-6.mp3",
        "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-12.mp3",
    ],
    "mysterious": [
        "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-10.mp3",
        "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-14.mp3",
        "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-8.mp3",
    ],
    "hopeful": [
        "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-6.mp3",
        "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-3.mp3",
        "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-9.mp3",
    ],
    "intense": [
        "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3",
        "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-2.mp3",
        "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-5.mp3",
    ],
    "melancholic": [
        "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-12.mp3",
        "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-3.mp3",
        "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-6.mp3",
    ],
}


# ═══════════════════════════════════════════════════════
#  IMAGES — stable seed that never changes
# ═══════════════════════════════════════════════════════

def get_image_url(prompt, idx=0):
    """Generate a stable image URL that won't change between reruns."""
    stable_string = f"{prompt}_{idx}"
    seed = int(hashlib.md5(stable_string.encode()).hexdigest()[:8], 16) % 100000
    return f"https://picsum.photos/seed/{seed}/800/600"


# ═══════════════════════════════════════════════════════
#  PDF
# ═══════════════════════════════════════════════════════

def extract_pdf(pdf_bytes):
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        text = ""
        for page_num in range(len(doc)):
            page = doc[page_num]
            page_text = page.get_text("text")
            if not page_text or len(page_text.strip()) < 10:
                blocks = page.get_text("blocks")
                if isinstance(blocks, list):
                    page_text = "\n".join(
                        b[4] for b in blocks
                        if isinstance(b, tuple) and len(b) > 4
                        and isinstance(b[4], str)
                    )
            if isinstance(page_text, str) and page_text.strip():
                text += page_text + "\n\n"
        doc.close()
        text = re.sub(r'\n{3,}', '\n\n', text).strip()
        return text if len(text) > 50 else ""
    except Exception as e:
        st.error(f"❌ Could not read PDF: {e}")
        return ""


def split_chapters(text):
    if not text or len(text) < 100:
        return ["Text too short."]

    for pattern in [
        r'(?=\n\s*(?:CHAPTER|Chapter)\s+[\dIVXLCDM]+)',
        r'(?=\n\s*(?:PART|Part)\s+[\dIVXLCDM]+)',
    ]:
        parts = re.split(pattern, text)
        parts = [p.strip() for p in parts if p.strip() and len(p.strip()) > 200]
        if len(parts) >= 2:
            return parts[:50]

    paras = re.split(r'\n\s*\n', text)
    if len(paras) >= 4:
        chunks, current = [], ""
        for p in paras:
            p = p.strip()
            if not p:
                continue
            if len(current) + len(p) > 2500 and len(current) > 500:
                chunks.append(current.strip())
                current = p
            else:
                current += "\n\n" + p
        if current.strip():
            chunks.append(current.strip())
        if len(chunks) >= 2:
            return chunks[:50]

    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks, current = [], ""
    for s in sentences:
        if len(current) + len(s) > 2500 and len(current) > 500:
            chunks.append(current.strip())
            current = s
        else:
            current += " " + s
    if current.strip():
        chunks.append(current.strip())

    return chunks[:50] if chunks else [text[:3000]]


# ═══════════════════════════════════════════════════════
#  AI
# ═══════════════════════════════════════════════════════

def make_chain(chapter_text):
    if not client:
        return [{"hook": "No AI.", "meaning": "", "example": "", "takeaway": "", "visual": "abstract", "mood": "calm"}]

    ai_lang = t("ai")

    try:
        r = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": f"""You summarize book chapters into scrollable cards that TEACH the reader.

Each card has 4 parts:
1. hook: Short punchy sentence (MAX 12 words). Makes reader curious.
2. meaning: What the author ACTUALLY means. 1-2 simple sentences. Faithful to the chapter.
3. example: One CONCRETE example from the book, history, or real life. 1 sentence.
4. takeaway: One short conclusion or lesson. 1 sentence.

CRITICAL RULES:
- Do NOT write vague motivational quotes
- Do NOT write generic philosophy
- EXPLAIN the actual ideas from THIS specific chapter
- Generate exactly 5 cards
- visual: 2-3 English words for a landscape/nature photo
- mood: one of: dark, epic, calm, mysterious, hopeful, intense, melancholic
- {ai_lang}

Return ONLY a JSON array:
[{{"hook":"short headline","meaning":"clear explanation","example":"specific example","takeaway":"lesson learned","visual":"photo keywords","mood":"calm"}}]"""
                },
                {
                    "role": "user",
                    "content": f"Summarize this chapter into idea cards:\n\n{chapter_text[:3000]}"
                }
            ],
            model=AI_MODEL,
            temperature=0.7,
            max_tokens=2000,
        )
        return parse_json(r.choices[0].message.content.strip())
    except Exception as e:
        st.warning(f"⚠️ AI error: {e}")
        return [{"hook": "Error. Refresh.", "meaning": "", "example": "", "takeaway": "", "visual": "abstract", "mood": "calm"}]


def make_title(chapter_text):
    if not client:
        return "..."
    ai_lang = t("ai")
    try:
        r = client.chat.completions.create(
            messages=[{
                "role": "user",
                "content": f"Poetic title, 2-4 words. {ai_lang} Return ONLY the title:\n\n{chapter_text[:1500]}"
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

    try:
        result = json.loads(cleaned)
        if isinstance(result, list):
            return validate(result)
    except json.JSONDecodeError:
        pass

    match = re.search(r'\[.*\]', cleaned, re.DOTALL)
    if match:
        try:
            result = json.loads(match.group())
            if isinstance(result, list):
                return validate(result)
        except json.JSONDecodeError:
            pass

    objs = []
    for o in re.findall(r'\{[^{}]+\}', cleaned):
        try:
            objs.append(json.loads(o))
        except json.JSONDecodeError:
            pass
    if objs:
        return validate(objs)

    return [{"hook": raw[:200], "meaning": "", "example": "", "takeaway": "", "visual": "abstract", "mood": "calm"}]


def validate(chain):
    moods = {"dark", "epic", "calm", "mysterious", "hopeful", "intense", "melancholic"}
    out = []
    for item in chain:
        if not isinstance(item, dict):
            continue
        v = {
            "hook": str(item.get("hook", item.get("idea", "..."))),
            "meaning": str(item.get("meaning", "")),
            "example": str(item.get("example", "")),
            "takeaway": str(item.get("takeaway", "")),
            "visual": str(item.get("visual", item.get("visual_prompt", "abstract"))),
            "mood": str(item.get("mood", "calm")).lower().strip(),
        }
        if v["mood"] not in moods:
            v["mood"] = "calm"
        out.append(v)
    return out or [{"hook": "...", "meaning": "", "example": "", "takeaway": "", "visual": "abstract", "mood": "calm"}]


# ═══════════════════════════════════════════════════════
#  FREE BOOKS
# ═══════════════════════════════════════════════════════

BOOKS = {
    "📜 Art of War — Sun Tzu": "https://www.gutenberg.org/cache/epub/132/pg132.txt",
    "🏛️ Meditations — Marcus Aurelius": "https://www.gutenberg.org/cache/epub/2680/pg2680.txt",
    "🧠 Beyond Good & Evil — Nietzsche": "https://www.gutenberg.org/cache/epub/4363/pg4363.txt",
    "👑 The Prince — Machiavelli": "https://www.gutenberg.org/cache/epub/1232/pg1232.txt",
    "📖 Frankenstein — Shelley": "https://www.gutenberg.org/cache/epub/84/pg84.txt",
    "🕳️ The Republic — Plato": "https://www.gutenberg.org/cache/epub/1497/pg1497.txt",
}


def download_book(url):
    try:
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        text = r.text
        for m in ["*** START OF THE PROJECT", "*** START OF THIS", "***START OF"]:
            idx = text.find(m)
            if idx != -1:
                nl = text.find('\n', idx)
                if nl != -1:
                    text = text[nl + 1:]
                break
        for m in ["*** END OF THE PROJECT", "*** END OF THIS", "***END OF",
                  "End of the Project Gutenberg", "End of Project Gutenberg"]:
            idx = text.find(m)
            if idx != -1:
                text = text[:idx]
                break
        text = text.strip()
        return text if len(text) > 100 else ""
    except Exception as e:
        st.error(f"❌ Download failed: {e}")
        return ""


# ═══════════════════════════════════════════════════════
#  CARD COMPONENT — self-contained HTML with animation
# ═══════════════════════════════════════════════════════

def render_card(hook, meaning, example, takeaway, mood, img_url,
                index, total, tap_text, lbl_meaning, lbl_example, lbl_takeaway):

    def esc(s):
        return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;").replace("'", "&#39;").replace("\n", " ")

    hook_safe = esc(hook)
    meaning_safe = esc(meaning)
    example_safe = esc(example)
    takeaway_safe = esc(takeaway)

    has_content = bool(meaning or example or takeaway)

    explain_sections = ""
    if meaning:
        explain_sections += f'<div class="ex-sec"><div class="ex-lbl">📖 {lbl_meaning}</div><div class="ex-txt">{meaning_safe}</div></div>'
    if example:
        explain_sections += f'<div class="ex-sec"><div class="ex-lbl">💡 {lbl_example}</div><div class="ex-txt">{example_safe}</div></div>'
    if takeaway:
        explain_sections += f'<div class="ex-sec"><div class="ex-lbl">🔑 {lbl_takeaway}</div><div class="ex-txt">{takeaway_safe}</div></div>'

    tap_section = ""
    if has_content:
        tap_section = f"""
            <div class="tap-bar" id="tapBar" onclick="toggle()">
                <span id="tapLabel">{tap_text} ▾</span>
            </div>
            <div class="explain" id="exBox">
                {explain_sections}
            </div>
        """

    # Calculate heights
    closed_height = 370
    open_height = 700

    html = f"""
    <html>
    <head>
    <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
        *{{margin:0;padding:0;box-sizing:border-box;}}
        body{{background:transparent;font-family:'Space Grotesk',sans-serif;}}

        .wrap{{width:100%;}}

        .hero{{
            position:relative;
            border-radius:22px 22px 4px 4px;
            overflow:hidden;
            height:320px;
            display:flex;
            align-items:flex-end;
            cursor:{('pointer' if has_content else 'default')};
        }}
        .hero-bg{{
            position:absolute;top:0;left:0;
            width:100%;height:100%;
            object-fit:cover;z-index:1;background:#111;
        }}
        .hero-grd{{
            position:absolute;top:0;left:0;
            width:100%;height:100%;
            background:linear-gradient(to bottom,
                rgba(0,0,0,0.05) 0%,
                rgba(0,0,0,0.4) 50%,
                rgba(0,0,0,0.92) 100%);
            z-index:2;
        }}
        .hero-body{{
            position:relative;z-index:3;
            padding:25px;width:100%;
        }}
        .hero-txt{{
            color:#fff;font-size:1.45em;font-weight:700;
            line-height:1.4;
            text-shadow:0 2px 12px rgba(0,0,0,0.8);
        }}
        .hero-ft{{
            color:rgba(255,255,255,0.4);font-size:0.75em;
            margin-top:10px;display:flex;
            justify-content:space-between;align-items:center;
        }}
        .mood{{
            background:rgba(233,69,96,0.25);color:#e94560;
            padding:2px 10px;border-radius:20px;font-weight:600;
        }}

        .tap-bar{{
            background:#0d1117;border:1px solid #1a2332;
            border-top:none;padding:10px;text-align:center;
            cursor:pointer;transition:all 0.3s;
        }}
        .tap-bar:hover{{background:#161b22;border-color:#e94560;}}
        .tap-bar span{{
            color:#e94560;font-size:0.85em;font-weight:600;
            letter-spacing:0.5px;
        }}

        .explain{{
            max-height:0;overflow:hidden;
            transition:max-height 0.5s ease,padding 0.5s ease,opacity 0.4s ease;
            opacity:0;
            background:linear-gradient(145deg,#0d1117,#161b22);
            border:1px solid #1a2332;border-top:none;
            border-radius:0 0 22px 22px;
            padding:0 25px;
        }}
        .explain.open{{
            max-height:350px;opacity:1;padding:22px 25px;
            overflow-y:auto;
        }}

        .ex-sec{{margin-bottom:14px;}}
        .ex-sec:last-child{{margin-bottom:0;}}
        .ex-lbl{{
            color:#e94560;font-size:0.7em;font-weight:700;
            text-transform:uppercase;letter-spacing:1.5px;
            margin-bottom:4px;
        }}
        .ex-txt{{color:#c8c8c8;font-size:0.93em;line-height:1.6;}}

        .explain::-webkit-scrollbar{{width:4px;}}
        .explain::-webkit-scrollbar-track{{background:#0d1117;}}
        .explain::-webkit-scrollbar-thumb{{background:#e94560;border-radius:4px;}}
    </style>
    </head>
    <body>
        <div class="wrap">
            <div class="hero" onclick="toggle()">
                <img class="hero-bg" src="{img_url}" loading="lazy"
                     onerror="this.src='https://picsum.photos/seed/fb{index}/800/600'">
                <div class="hero-grd"></div>
                <div class="hero-body">
                    <div class="hero-txt">{hook_safe}</div>
                    <div class="hero-ft">
                        <span class="mood">{mood}</span>
                        <span>{index + 1}/{total}</span>
                    </div>
                </div>
            </div>
            {tap_section}
        </div>
        <script>
            var open=false;
            function toggle(){{
                var box=document.getElementById('exBox');
                var lbl=document.getElementById('tapLabel');
                if(!box||!lbl)return;
                open=!open;
                if(open){{
                    box.classList.add('open');
                    lbl.innerHTML='▴ close';
                }}else{{
                    box.classList.remove('open');
                    lbl.innerHTML='{tap_text} ▾';
                }}
            }}
        </script>
    </body>
    </html>
    """

    components.html(html, height=open_height, scrolling=False)


# ═══════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════

def main():
    defaults = {
        "lang": "EN",
        "chains": {},
        "current_chapter": 0,
        "music_enabled": True,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

    # ── HEADER ──
    st.markdown(
        "<h1 style='text-align:center;color:#e94560;font-size:2.3em;"
        "margin:8px 0 0;'>🧠 DeepScroll</h1>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<p style='text-align:center;color:#444;font-size:0.85em;"
        f"margin:4px 0 12px;'>{t('sub')}</p>",
        unsafe_allow_html=True,
    )

    # ── LANGUAGE + MUSIC TOGGLE ──
    top_cols = st.columns([1, 1, 1, 1, 1.5])

    for i, (code, flag) in enumerate([("EN", "🇬🇧"), ("DE", "🇩🇪"), ("UA", "🇺🇦"), ("FR", "🇫🇷")]):
        with top_cols[i]:
            label = f"✓ {flag}" if code == st.session_state["lang"] else flag
            if st.button(label, key=f"lang_{code}", use_container_width=True):
                if code != st.session_state["lang"]:
                    st.session_state["lang"] = code
                    st.session_state["chains"] = {}
                    st.rerun()

    with top_cols[4]:
        music_on = st.session_state["music_enabled"]
        music_label = t("music_on") if music_on else t("music_off")
        if st.button(music_label, key="music_toggle", use_container_width=True):
            st.session_state["music_enabled"] = not music_on
            st.rerun()

    st.markdown("---")

    # ── SOURCE ──
    tab1, tab2 = st.tabs([t("upload"), t("classics")])
    book_ready = False

    with tab1:
        uploaded = st.file_uploader("Upload", type=["pdf"], label_visibility="collapsed")
        if uploaded:
            file_id = f"{uploaded.name}_{uploaded.size}"
            if st.session_state.get("file_id") != file_id:
                st.session_state["pdf_bytes"] = uploaded.read()
                st.session_state["file_id"] = file_id
                for k in ["chapters", "chains", "current_chapter", "raw_text"]:
                    st.session_state.pop(k, None)
                st.session_state["chains"] = {}
                st.session_state["current_chapter"] = 0
            book_ready = True

    with tab2:
        sel = st.selectbox("Pick", list(BOOKS.keys()), label_visibility="collapsed")
        if st.button(t("load"), use_container_width=True):
            with st.spinner(t("reading")):
                txt = download_book(BOOKS[sel])
                if txt:
                    st.session_state["raw_text"] = txt
                    for k in ["chapters", "chains", "current_chapter", "pdf_bytes", "file_id"]:
                        st.session_state.pop(k, None)
                    st.session_state["chains"] = {}
                    st.session_state["current_chapter"] = 0
                    st.rerun()
        if "raw_text" in st.session_state:
            book_ready = True

    # ── PROCESS ──
    if book_ready and "chapters" not in st.session_state:
        with st.spinner(t("reading")):
            if "pdf_bytes" in st.session_state:
                raw = extract_pdf(st.session_state["pdf_bytes"])
            elif "raw_text" in st.session_state:
                raw = st.session_state["raw_text"]
            else:
                raw = ""
            if raw and len(raw) > 50:
                st.session_state["chapters"] = split_chapters(raw)
                st.session_state["current_chapter"] = 0
                st.session_state["chains"] = {}
                st.rerun()
            else:
                st.error("❌ Could not extract text.")
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
    if cur >= total:
        cur = total - 1
        st.session_state["current_chapter"] = cur

    # Navigation
    c1, c2, c3 = st.columns([1, 2, 1])
    with c1:
        if cur > 0 and st.button("⬅️", key="prev", use_container_width=True):
            st.session_state["current_chapter"] = cur - 1
            st.rerun()
    with c2:
        st.markdown(
            f"<p style='text-align:center;color:#555;margin-top:8px;'>"
            f"{cur + 1} / {total}</p>",
            unsafe_allow_html=True,
        )
    with c3:
        if cur < total - 1 and st.button("➡️", key="nxt", use_container_width=True):
            st.session_state["current_chapter"] = cur + 1
            st.rerun()

    # Generate chain
    chains = st.session_state["chains"]
    if cur not in chains:
        with st.spinner(t("building")):
            ch_text = chapters[cur]
            title = make_title(ch_text)
            chain = make_chain(ch_text)
            chains[cur] = {"title": title, "chain": chain}
            st.session_state["chains"] = chains

    data = chains[cur]

    # Title
    st.markdown(f'<div class="ch-t">{data["title"]}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="ch-s">{cur + 1} / {total}</div>', unsafe_allow_html=True)

    # ── MUSIC (only if enabled) ──
    if st.session_state["music_enabled"] and data["chain"]:
        mood = data["chain"][0].get("mood", "calm")
        tracks = MUSIC.get(mood, MUSIC["calm"])
        tracks_json = json.dumps(tracks)

        with st.expander(f"🎵 {t('music')} — {mood.upper()}", expanded=False):
            components.html(f"""
                <div style="
                    font-family:'Segoe UI',sans-serif;
                    background:#111;border-radius:12px;
                    padding:15px;color:#ccc;">
                    <div style="display:flex;align-items:center;gap:12px;margin-bottom:12px;">
                        <button id="tBtn" onclick="tog()" style="
                            background:#e94560;border:none;color:white;
                            width:40px;height:40px;border-radius:50%;
                            font-size:18px;cursor:pointer;">▶</button>
                        <button onclick="nxt()" style="
                            background:#222;border:1px solid #333;color:#ccc;
                            padding:8px 16px;border-radius:20px;
                            cursor:pointer;font-size:14px;">⏭ Next</button>
                        <div style="flex:1;display:flex;align-items:center;gap:8px;">
                            <span style="font-size:12px;">🔈</span>
                            <input type="range" min="0" max="100" value="25"
                                style="flex:1;accent-color:#e94560;height:4px;"
                                oninput="sv(this.value)">
                            <span style="font-size:12px;">🔊</span>
                        </div>
                    </div>
                    <div id="tI" style="font-size:11px;color:#555;text-align:center;">
                        Track 1 / {len(tracks)}</div>
                </div>
                <script>
                    var t={tracks_json},c=0,tv=0.25,ip=false;
                    var a=new Audio(t[0]);a.volume=0;
                    a.addEventListener('ended',function(){{nxt();}});
                    function fi(){{var v=0;var i=setInterval(function(){{
                        v+=0.005;if(v>=tv){{v=tv;clearInterval(i);}}a.volume=v;}},100);}}
                    function tog(){{var b=document.getElementById('tBtn');
                        if(ip){{a.pause();b.innerHTML='▶';ip=false;}}
                        else{{a.play();fi();b.innerHTML='⏸';ip=true;}}}}
                    function nxt(){{c=(c+1)%t.length;var w=ip;
                        a.src=t[c];document.getElementById('tI').innerHTML=
                        'Track '+(c+1)+' / '+t.length;
                        if(w){{a.volume=0;a.play();fi();}}}}
                    function sv(v){{tv=v/100;if(ip){{a.volume=tv;}}}}
                    setTimeout(function(){{a.play().then(function(){{
                        ip=true;document.getElementById('tBtn').innerHTML='⏸';
                        fi();}}).catch(function(){{}});}},2000);
                </script>
            """, height=100)

    # ── CARDS ──
    chain = data["chain"]
    for i, node in enumerate(chain):
        hook = node.get("hook", node.get("idea", "..."))
        meaning = node.get("meaning", "")
        example = node.get("example", "")
        takeaway = node.get("takeaway", "")
        visual = node.get("visual", "abstract")
        mood = node.get("mood", "calm")
        img = get_image_url(visual, idx=cur * 100 + i)

        render_card(
            hook=hook,
            meaning=meaning,
            example=example,
            takeaway=takeaway,
            mood=mood,
            img_url=img,
            index=i,
            total=len(chain),
            tap_text=t("tap"),
            lbl_meaning=t("what_means"),
            lbl_example=t("example_label"),
            lbl_takeaway=t("takeaway_label"),
        )

        if i < len(chain) - 1:
            st.markdown('<div class="conn">⟱</div>', unsafe_allow_html=True)

    # ── END ──
    st.markdown("---")
    if cur < total - 1:
        if st.button(t("next_ch"), use_container_width=True, type="primary", key="next_ch"):
            st.session_state["current_chapter"] = cur + 1
            st.rerun()
    else:
        st.markdown(f"""
            <div style="text-align:center;padding:30px;">
                <h2 style="color:#e94560;">{t('done')}</h2>
                <p style="color:#555;">{t('done_sub')}</p>
            </div>
        """, unsafe_allow_html=True)
        if st.button(t("reset"), use_container_width=True, key="reset_btn"):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()


if __name__ == "__main__":
    main()
