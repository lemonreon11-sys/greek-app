import io
import random
import re
import sys
import unicodedata
from difflib import SequenceMatcher
import streamlit as st
from gtts import gTTS

# 音声認識ライブラリの安全インポート
try:
    import speech_recognition as sr
    SPEECH_REC_AVAILABLE = True
except ImportError:
    SPEECH_REC_AVAILABLE = False

# -------------------------------------------------------------
# 0. F5キー直接実行時の自動ブラウザ切り替え処理
# -------------------------------------------------------------
from streamlit.web import cli as stcli

if not st.runtime.exists():
    sys.argv = ["streamlit", "run", __file__]
    sys.exit(stcli.main())

# -------------------------------------------------------------
# 1. セキュリティ設定（合言葉・パスワード）
# -------------------------------------------------------------
SECRET_PASSWORD = "0731"

st.set_page_config(page_title="ギリシャ語Duo道場", page_icon="🇬🇷", layout="centered")

# 安全なCSSによる自動翻訳防止 ＆ 単語ポップアップ ＆ 録音UI特大正円デザイン
st.markdown(
    """
    <style>
    html, body, div, span, p, h1, h2, h3 {
        translate: no !important;
        -webkit-translate: no !important;
    }
    .duo-sentence-box {
        text-align: center;
        font-size: 1.55rem;
        font-weight: bold;
        line-height: 2.6rem;
        margin: 15px 0 20px 0;
        user-select: none;
        -webkit-tap-highlight-color: transparent;
    }
    .duo-quote {
        color: #94a3b8;
        font-size: 1.6rem;
    }
    .duo-word {
        position: relative;
        display: inline-block;
        cursor: pointer;
        border-bottom: 2.5px dotted #0284c7;
        color: #0369a1;
        padding: 0 4px;
        margin: 0 2px;
        border-radius: 4px;
        transition: all 0.15s ease;
    }
    .duo-word:hover, .duo-word:focus, .duo-word:active {
        background-color: #e0f2fe;
        outline: none;
    }
    .duo-word:hover .duo-tooltip,
    .duo-word:focus .duo-tooltip,
    .duo-word:active .duo-tooltip {
        visibility: visible;
        opacity: 1;
        transform: translateX(-50%) translateY(0);
    }
    .duo-tooltip {
        visibility: hidden;
        opacity: 0;
        width: max-content;
        max-width: 220px;
        background-color: #1e293b;
        color: #ffffff;
        text-align: center;
        border-radius: 8px;
        padding: 6px 12px;
        position: absolute;
        z-index: 999;
        bottom: 125%;
        left: 50%;
        transform: translateX(-50%) translateY(6px);
        transition: opacity 0.2s ease, transform 0.2s ease;
        font-size: 0.95rem;
        font-weight: normal;
        box-shadow: 0 6px 16px rgba(0,0,0,0.25);
        pointer-events: none;
        white-space: nowrap;
    }
    .duo-tooltip::after {
        content: "";
        position: absolute;
        top: 100%;
        left: 50%;
        margin-left: -6px;
        border-width: 6px;
        border-style: solid;
        border-color: #1e293b transparent transparent transparent;
    }
    .dish-card {
        background-color: #f0fdf4;
        border: 1.5px solid #86efac;
        border-radius: 10px;
        padding: 12px 16px;
        margin-top: 12px;
        color: #166534;
        font-size: 0.95rem;
        line-height: 1.5rem;
    }

    /* 🎤 録音エリア（st.audio_input）の正円・特大デザイン */
    [data-testid="stAudioInput"] {
        background-color: #f0f9ff !important;
        border: 2px dashed #0284c7 !important;
        border-radius: 20px !important;
        padding: 16px !important;
        margin: 12px 0 !important;
        box-sizing: border-box !important;
    }

    /* グレーのバー自体を高くして、正円が収まるスペースを確保 */
    [data-testid="stAudioInput"] > div {
        min-height: 76px !important;
        height: auto !important;
        display: flex !important;
        align-items: center !important;
        border-radius: 38px !important;
        padding: 6px 14px !important;
    }

    /* 録音ボタンを潰れない「綺麗な特大の正円（まる）」に固定 */
    [data-testid="stAudioInput"] button {
        width: 60px !important;
        height: 60px !important;
        min-width: 60px !important;
        min-height: 60px !important;
        max-width: 60px !important;
        max-height: 60px !important;
        aspect-ratio: 1 / 1 !important;
        border-radius: 50% !important;
        flex-shrink: 0 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        box-shadow: 0 4px 12px rgba(2, 132, 199, 0.3) !important;
        cursor: pointer !important;
        transition: transform 0.12s ease !important;
        margin: 0 10px 0 0 !important;
    }
    [data-testid="stAudioInput"] button:active {
        transform: scale(0.92) !important;
    }
    [data-testid="stAudioInput"] button svg {
        width: 30px !important;
        height: 30px !important;
    }

    /* 録音完了後のオーディオプレーヤー内部ボタンは正円指定を安全解除 */
    [data-testid="stAudioInput"] [data-testid="stAudio"] {
        width: 100% !important;
        margin-top: 8px !important;
    }
    [data-testid="stAudioInput"] [data-testid="stAudio"] button {
        width: auto !important;
        height: auto !important;
        min-width: auto !important;
        min-height: auto !important;
        max-width: none !important;
        max-height: none !important;
        aspect-ratio: auto !important;
        border-radius: 6px !important;
        box-shadow: none !important;
        margin: 0 4px !important;
        transform: none !important;
    }
    [data-testid="stAudioInput"] [data-testid="stAudio"] button svg {
        width: 18px !important;
        height: 18px !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔒 ギリシャ語アプリ（保護中）")
    st.write("このアプリはパスワードで保護されています。合言葉を入力してください。")

    pwd_input = st.text_input("パスワード", type="password", key="login_pwd")

    if st.button("ログインして始める", use_container_width=True, key="login_btn"):
        if pwd_input == SECRET_PASSWORD:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("パスワードが正しくありません。")
    st.stop()

# -------------------------------------------------------------
# 2. 旅行フレーズ・グルメ・看板データベース
# -------------------------------------------------------------
DATASET = [
    # === 基本挨拶・日常会話 ===
    {
        "greek": "Γεια σας",
        "reading": "ヤ サス",
        "meaning": "こんにちは / さようなら（丁寧）",
        "category": "基本挨拶",
        "level": "初級",
        "speaker": "自分",
        "breakdown": [
            {"word": "Γεια", "meaning": "健康 / やあ"},
            {"word": "σας", "meaning": "あなたに（丁寧・複数）"}
        ]
    },
    {
        "greek": "Ευχαριστώ",
        "reading": "エフハリスト",
        "meaning": "ありがとう",
        "category": "基本挨拶",
        "level": "初級",
        "speaker": "自分",
        "breakdown": [
            {"word": "Ευχαριστώ", "meaning": "ありがとう / 感謝します"}
        ]
    },
    {
        "greek": "Παρακαλώ",
        "reading": "パラカロ",
        "meaning": "お願いします / どういたしまして",
        "category": "基本挨拶",
        "level": "初級",
        "speaker": "自分",
        "breakdown": [
            {"word": "Παρακαλώ", "meaning": "お願いします / どういたしまして"}
        ]
    },
    {
        "greek": "Ναι / Όχι",
        "reading": "ネ / オヒ",
        "meaning": "はい / いいえ（※ネが肯定）",
        "category": "基本挨拶",
        "level": "初級",
        "speaker": "自分",
        "breakdown": [
            {"word": "Ναι", "meaning": "はい（肯定）"},
            {"word": "/", "meaning": "/"},
            {"word": "Όχι", "meaning": "いいえ（否定）"}
        ]
    },
    {
        "greek": "Καλημέρα",
        "reading": "カリメラ",
        "meaning": "おはようございます（午前中の挨拶）",
        "category": "基本挨拶",
        "level": "初級",
        "speaker": "自分",
        "breakdown": [{"word": "Καλημέρα", "meaning": "良い朝（おはよう）"}]
    },
    {
        "greek": "Καλησπέρα",
        "reading": "カリスペラ",
        "meaning": "こんばんは（午後・夕方以降の挨拶）",
        "category": "基本挨拶",
        "level": "初級",
        "speaker": "自分",
        "breakdown": [{"word": "Καλησπέρα", "meaning": "良い夕暮れ（こんばんは）"}]
    },
    {
        "greek": "Συγγνώμη",
        "reading": "シグノミ",
        "meaning": "すみません / 失礼します",
        "category": "基本挨拶",
        "level": "中級",
        "speaker": "自分",
        "breakdown": [
            {"word": "Συγγνώμη", "meaning": "すみません / ごめんなさい"}
        ]
    },
    {
        "greek": "Τι κάνετε;",
        "reading": "ティ カネテ？",
        "meaning": "お元気ですか？ / 調子はどう？",
        "category": "基本挨拶",
        "level": "中級",
        "speaker": "自分",
        "breakdown": [
            {"word": "Τι", "meaning": "何"},
            {"word": "κάνετε;", "meaning": "していますか（調子はどう？）"}
        ]
    },
    {
        "greek": "Μιλάτε αγγλικά;",
        "reading": "ミラテ アングリカ？",
        "meaning": "英語は話せますか？",
        "category": "基本挨拶",
        "level": "中級",
        "speaker": "自分",
        "breakdown": [
            {"word": "Μιλάτε", "meaning": "話せますか（丁寧）"},
            {"word": "αγγλικά;", "meaning": "英語を"}
        ]
    },
    {
        "greek": "Δεν καταλαβαίνω.",
        "reading": "デン カタラヴェノ",
        "meaning": "わかりません / 理解できません",
        "category": "基本挨拶",
        "level": "上級",
        "speaker": "自分",
        "breakdown": [
            {"word": "Δεν", "meaning": "〜ない（否定）"},
            {"word": "καταλαβαίνω.", "meaning": "理解する / わかる"}
        ]
    },
    {
        "greek": "Ορίστε!",
        "reading": "オリステ！",
        "meaning": "どうぞ！（品物を渡すとき、注文を聞くとき）",
        "category": "基本挨拶",
        "level": "上級",
        "speaker": "スタッフ",
        "breakdown": [
            {"word": "Ορίστε!", "meaning": "どうぞ！ / はい、何でしょうか"}
        ]
    },
    {
        "greek": "Πώς μπορώ να σας βοηθήσω;",
        "reading": "ポス ボロ ナ サス ヴォイシソ？",
        "meaning": "どのようなご用件でしょうか？ / 何かお探しですか？",
        "category": "基本挨拶",
        "level": "上級",
        "speaker": "スタッフ",
        "breakdown": [
            {"word": "Πώς", "meaning": "どのように"},
            {"word": "μπορώ", "meaning": "〜できる"},
            {"word": "να", "meaning": "〜すること"},
            {"word": "σας", "meaning": "あなたを"},
            {"word": "βοηθήσω;", "meaning": "手伝う / 助ける"}
        ]
    },

    # === カフェ（飲み物単語・注文） ===
    {
        "greek": "Νερό",
        "reading": "ネロ",
        "meaning": "お水（単語）",
        "category": "カフェ",
        "level": "初級",
        "speaker": "料理",
        "breakdown": [{"word": "Νερό", "meaning": "お水"}],
        "dish_info": "ギリシャのカフェでは、何を頼んでもまず冷えたボトルの水（またはグラスの水）が無料で運ばれてくる文化があります。"
    },
    {
        "greek": "Καφές",
        "reading": "カフェス",
        "meaning": "コーヒー（単語）",
        "category": "カフェ",
        "level": "初級",
        "speaker": "料理",
        "breakdown": [{"word": "Καφές", "meaning": "コーヒー"}]
    },
    {
        "greek": "Φραπέ",
        "reading": "フラペ",
        "meaning": "フラッペ（ギリシャ発祥の泡立つ名物アイスコーヒー）",
        "category": "カフェ",
        "level": "初級",
        "speaker": "料理",
        "breakdown": [{"word": "Φραπέ", "meaning": "フラッペ"}],
        "dish_info": "インスタントコーヒーを水と氷でシェイクしてきめ細かい泡を立てた、ギリシャの夏の風物詩ドリンクです。"
    },
    {
        "greek": "Ελληνικός καφές",
        "reading": "エリニコス カフェス",
        "meaning": "ギリシャコーヒー（小鍋で粉ごと煮出す濃厚な伝統コーヒー）",
        "category": "カフェ",
        "level": "初級",
        "speaker": "料理",
        "breakdown": [
            {"word": "Ελληνικός", "meaning": "ギリシャの"},
            {"word": "καφές", "meaning": "コーヒー"}
        ],
        "dish_info": "小鍋（ブリキ）で粉と一緒に煮出す伝統コーヒー。粉が底に沈むのを待って上澄みを飲みます。底の泥状の粉は残すのがマナー。"
    },
    {
        "greek": "Έναν φρέντο εσπρέσο, παρακαλώ.",
        "reading": "エナン フレット エスプレッソ, パラカロ",
        "meaning": "アイスエスプレッソを1杯ください",
        "category": "カフェ",
        "level": "中級",
        "speaker": "自分",
        "breakdown": [
            {"word": "Έναν", "meaning": "1つの"},
            {"word": "φρέντο", "meaning": "冷たい（アイス）"},
            {"word": "εσπρέσο,", "meaning": "エスプレッソ"},
            {"word": "παρακαλώ.", "meaning": "お願いします"}
        ]
    },
    {
        "greek": "Έναν φρέντο καπουτσίνο, παρακαλώ.",
        "reading": "エナン フレット カプチーノ, パラカロ",
        "meaning": "アイスカプチーノを1杯ください",
        "category": "カフェ",
        "level": "中級",
        "speaker": "自分",
        "breakdown": [
            {"word": "Έναν", "meaning": "1つの"},
            {"word": "φρέντο", "meaning": "冷たい（アイス）"},
            {"word": "καπουτσίνο,", "meaning": "カプチーノ"},
            {"word": "παρακαλώ.", "meaning": "お願いします"}
        ]
    },
    {
        "greek": "Για έξω, παρακαλώ.",
        "reading": "ヤ エクソ, パラカロ",
        "meaning": "テイクアウト（持ち帰り）でお願いします",
        "category": "カフェ",
        "level": "中級",
        "speaker": "自分",
        "breakdown": [
            {"word": "Για", "meaning": "〜向けに"},
            {"word": "έξω,", "meaning": "外（テイクアウト）"},
            {"word": "παρακαλώ.", "meaning": "お願いします"}
        ]
    },
    {
        "greek": "Για εδώ ή για έξω;",
        "reading": "ヤ エド イ ヤ エクソ？",
        "meaning": "店内でお召し上がりですか、お持ち帰りですか？",
        "category": "カフェ",
        "level": "上級",
        "speaker": "スタッフ",
        "breakdown": [
            {"word": "Για εδώ", "meaning": "店内で"},
            {"word": "ή", "meaning": "それとも"},
            {"word": "για έξω;", "meaning": "お持ち帰りで"}
        ]
    },
    {
        "greek": "Πόση ζάχαρη θέλετε;",
        "reading": "ポスィ ザハリ セレテ？",
        "meaning": "お砂糖の量はどうなさいますか？",
        "category": "カフェ",
        "level": "上級",
        "speaker": "スタッフ",
        "breakdown": [
            {"word": "Πόση", "meaning": "どれくらいの"},
            {"word": "ζάχαρη", "meaning": "砂糖"},
            {"word": "θέλετε;", "meaning": "欲しいですか"}
        ]
    },

    # === レストラン・名物料理 ===
    {
        "greek": "Μουσακάς",
        "reading": "ムサカス",
        "meaning": "ムサカ（ナス・ポテト・ひき肉の重ね焼き）",
        "category": "レストラン・名物料理",
        "level": "初級",
        "speaker": "料理",
        "breakdown": [{"word": "Μουσακάς", "meaning": "ムサカ（ギリシャ代表料理）"}],
        "dish_info": "【ギリシャの国民食】素揚げしたナスとジャガイモ、スパイスを効かせたひき肉を層にし、濃厚なベシャメルソースを乗せてオーブンで焼き上げた伝統料理です。"
    },
    {
        "greek": "Σουβλάκι",
        "reading": "スヴラキ",
        "meaning": "スヴラキ（豚・鶏などの串焼き肉）",
        "category": "レストラン・名物料理",
        "level": "初級",
        "speaker": "料理",
        "breakdown": [{"word": "Σουβλάκι", "meaning": "スヴラキ（串焼き肉）"}],
        "dish_info": "【定番肉料理】オリーブオイル、レモン、オレガノでマリネした豚肉や鶏肉を串に刺して炭火で香ばしく焼いた料理。レモンをたっぷり絞って食べます。"
    },
    {
        "greek": "Γύρος",
        "reading": "ギロス",
        "meaning": "ギロス（回転炙り焼き肉のピタサンド）",
        "category": "レストラン・名物料理",
        "level": "初級",
        "speaker": "料理",
        "breakdown": [{"word": "Γύρος", "meaning": "ギロス（定番ストリートフード）"}],
        "dish_info": "【必食の庶民派グルメ】大きな回転串で炙り焼きにした肉を薄く削ぎ落とし、トマト、玉ねぎ、ポテト、ザジキと一緒にピタパンでくるんだ手軽で絶品のサンドです。"
    },
    {
        "greek": "Χωριάτικη",
        "reading": "ホリアティキ",
        "meaning": "グリークサラダ（フェタチーズ丸ごと乗せ田舎風サラダ）",
        "category": "レストラン・名物料理",
        "level": "初級",
        "speaker": "料理",
        "breakdown": [{"word": "Χωριάτικη", "meaning": "田舎風サラダ（グリークサラダ）"}],
        "dish_info": "【タヴェルナの必需品】完熟トマト、きゅうり、赤玉ねぎ、オリーブの上に分厚いフェタチーズが丸ごと乗り、オリーブオイルとオレガノがたっぷりかかっています。"
    },
    {
        "greek": "Τζατζίκι",
        "reading": "ザジキ",
        "meaning": "ザジキ（ヨーグルトときゅうりとにんにくの万能ディップ）",
        "category": "レストラン・名物料理",
        "level": "初級",
        "speaker": "料理",
        "breakdown": [{"word": "Τζατζίκι", "meaning": "ザジキ（ヨーグルトディップ）"}]
    },
    {
        "greek": "Τον κατάλογο, παρακαλώ.",
        "reading": "トン カタロゴ, パラカロ",
        "meaning": "メニューを見せてください",
        "category": "レストラン・名物料理",
        "level": "中級",
        "speaker": "自分",
        "breakdown": [
            {"word": "Τον κατάλογο,", "meaning": "メニューを"},
            {"word": "παρακαλώ.", "meaning": "お願いします"}
        ]
    },
    {
        "greek": "Τον λογαριασμό, παρακαλώ.",
        "reading": "トン ロガリアズモ, パラカロ",
        "meaning": "お会計をお願いします",
        "category": "レストラン・名物料理",
        "level": "中級",
        "speaker": "自分",
        "breakdown": [
            {"word": "Τον λογαριασμό,", "meaning": "お会計を"},
            {"word": "παρακαλώ.", "meaning": "お願いします"}
        ]
    },
    {
        "greek": "Είστε έτοιμοι να παραγγείλετε;",
        "reading": "イステ エティミ ナ パランギレテ？",
        "meaning": "ご注文はお決まりですか？",
        "category": "レストラン・名物料理",
        "level": "上級",
        "speaker": "スタッフ",
        "breakdown": [
            {"word": "Είστε", "meaning": "〜ですか"},
            {"word": "έτοιμοι", "meaning": "準備ができた"},
            {"word": "να", "meaning": "〜すること"},
            {"word": "παραγγείλετε;", "meaning": "注文する"}
        ]
    },
    {
        "greek": "Πληρώνετε μαζί ή χωριστά;",
        "reading": "プリロネテ マズィ イ ホリスタ？",
        "meaning": "お会計はご一緒ですか、別々ですか？",
        "category": "レストラン・名物料理",
        "level": "上級",
        "speaker": "スタッフ",
        "breakdown": [
            {"word": "Πληρώνετε", "meaning": "支払いますか"},
            {"word": "μαζί", "meaning": "一緒に"},
            {"word": "ή", "meaning": "それとも"},
            {"word": "χωριστά;", "meaning": "別々に（割り勘）"}
        ]
    },

    # === 空港・飛行機（超強化） ===
    {
        "greek": "Διαβατήριο",
        "reading": "ディヴァティリオ",
        "meaning": "パスポート（単語）",
        "category": "空港・飛行機",
        "level": "初級",
        "speaker": "自分",
        "breakdown": [{"word": "Διαβατήριο", "meaning": "パスポート"}]
    },
    {
        "greek": "Για τουρισμό.",
        "reading": "ヤ トゥリズモ",
        "meaning": "観光です（入国審査での目的質問への返答）",
        "category": "空港・飛行機",
        "level": "初級",
        "speaker": "自分",
        "breakdown": [
            {"word": "Για", "meaning": "〜のために"},
            {"word": "τουρισμό.", "meaning": "観光"}
        ]
    },
    {
        "greek": "Μια θέση στο παράθυρο, παρακαλώ.",
        "reading": "ミア セスィ スト パラシロ, パラカロ",
        "meaning": "窓側の席をお願いします（チェックイン時）",
        "category": "空港・飛行機",
        "level": "初級",
        "speaker": "自分",
        "breakdown": [
            {"word": "Μια θέση", "meaning": "席を1つ"},
            {"word": "στο παράθυρο,", "meaning": "窓側の"},
            {"word": "παρακαλώ.", "meaning": "お願いします"}
        ]
    },
    {
        "greek": "Μια θέση στο διάδρομο, παρακαλώ.",
        "reading": "ミア セスィ スト ディアドロモ, パラカロ",
        "meaning": "通路側の席をお願いします（チェックイン時）",
        "category": "空港・飛行機",
        "level": "初級",
        "speaker": "自分",
        "breakdown": [
            {"word": "Μια θέση", "meaning": "席を1つ"},
            {"word": "στο διάδρομο,", "meaning": "通路側の"},
            {"word": "παρακαλώ.", "meaning": "お願いします"}
        ]
    },
    {
        "greek": "Πού είναι η πύλη επιβίβασης;",
        "reading": "プ イネ イ ピリ エピヴィヴァシス？",
        "meaning": "搭乗ゲートはどこですか？",
        "category": "空港・飛行機",
        "level": "中級",
        "speaker": "自分",
        "breakdown": [
            {"word": "Πού", "meaning": "どこ"},
            {"word": "είναι", "meaning": "ありますか"},
            {"word": "η πύλη", "meaning": "搭乗口 / ゲート"},
            {"word": "επιβίβασης;", "meaning": "搭乗の"}
        ]
    },
    {
        "greek": "Η βαλίτσα μου δεν ήρθε.",
        "reading": "イ ヴァリツァ ム デン イールセ",
        "meaning": "私のスーツケースが出てきません（ロストバゲージ窓口）",
        "category": "空港・飛行機",
        "level": "中級",
        "speaker": "自分",
        "breakdown": [
            {"word": "Η βαλίτσα", "meaning": "スーツケースが"},
            {"word": "μου", "meaning": "私の"},
            {"word": "δεν ήρθε.", "meaning": "届きませんでした/来ませんでした"}
        ]
    },
    {
        "greek": "Η βαλίτσα μου έχει σπάσει.",
        "reading": "イ ヴァリツァ ム エヒ スパシ",
        "meaning": "スーツケースが破損しています（破損申告窓口）",
        "category": "空港・飛行機",
        "level": "中級",
        "speaker": "自分",
        "breakdown": [
            {"word": "Η βαλίτσα μου", "meaning": "私のスーツケースが"},
            {"word": "έχει σπάσει.", "meaning": "壊れています/割れています"}
        ]
    },
    {
        "greek": "Χάνω την πτήση μετεπιβίβασης!",
        "reading": "ハノ ティン プティスィ メテピヴィヴァスィス！",
        "meaning": "乗り継ぎ便に乗り遅れそうです！",
        "category": "空港・飛行機",
        "level": "上級",
        "speaker": "自分",
        "breakdown": [
            {"word": "Χάνω", "meaning": "逃す/遅れる"},
            {"word": "την πτήση", "meaning": "便を"},
            {"word": "μετεπιβίβασης!", "meaning": "乗り継ぎの"}
        ]
    },
    {
        "greek": "Το διαβατήριο και την κάρτα επιβίβασης, παρακαλώ.",
        "reading": "ト ディヴァティリオ ケ ティン カルタ エピヴィヴァシス, パラカロ",
        "meaning": "パスポートと搭乗券を見せてください",
        "category": "空港・飛行機",
        "level": "上級",
        "speaker": "スタッフ",
        "breakdown": [
            {"word": "Το διαβατήριο", "meaning": "パスポート"},
            {"word": "και", "meaning": "と"},
            {"word": "την κάρτα", "meaning": "カード / 券"},
            {"word": "επιβίβασης,", "meaning": "搭乗の"},
            {"word": "παρακαλώ.", "meaning": "お願いします"}
        ]
    },
    {
        "greek": "Βάλτε τη βαλίτσα στη ζυγαριά, παρακαλώ.",
        "reading": "ヴァルテ ティ ヴァリツァ スティ スィガリア, パラカロ",
        "meaning": "スーツケースを秤の上に乗せてください",
        "category": "空港・飛行機",
        "level": "上級",
        "speaker": "スタッフ",
        "breakdown": [
            {"word": "Βάλτε", "meaning": "乗せてください"},
            {"word": "τη βαλίτσα", "meaning": "荷物を"},
            {"word": "στη ζυγαριά,", "meaning": "秤の上に"},
            {"word": "παρακαλώ.", "meaning": "お願いします"}
        ]
    },
    {
        "greek": "Η βαλίτσα σας είναι υπέρβαρη.",
        "reading": "イ ヴァリツァ サス イネ イペルヴァリ",
        "meaning": "お荷物が重量オーバー（超過）です（追加料金が必要）",
        "category": "空港・飛行機",
        "level": "上級",
        "speaker": "スタッフ",
        "breakdown": [
            {"word": "Η βαλίτσα σας", "meaning": "あなたのお荷物は"},
            {"word": "είναι", "meaning": "〜です"},
            {"word": "υπέρβαρη.", "meaning": "重量オーバーの"}
        ]
    },
    {
        "greek": "Η πύλη επιβίβασης άλλαξε.",
        "reading": "イ ピリ エピヴィヴァスィス アラクセ",
        "meaning": "搭乗ゲートが変更になりました（空港アナウンス・係員）",
        "category": "空港・飛行機",
        "level": "上級",
        "speaker": "スタッフ",
        "breakdown": [
            {"word": "Η πύλη επιβίβασης", "meaning": "搭乗ゲートが"},
            {"word": "άλλαξε.", "meaning": "変わりました/変更されました"}
        ]
    },
    {
        "greek": "ΕΛΕΓΧΟΣ ΔΙΑΒΑΤΗΡΙΩΝ",
        "reading": "エレンホス ディヴァティリオン",
        "meaning": "パスポートコントロール / 入国審査（看板）",
        "category": "空港・飛行機",
        "level": "初級",
        "speaker": "看板",
        "breakdown": [
            {"word": "ΕΛΕΓΧΟΣ", "meaning": "審査/検査"},
            {"word": "ΔΙΑΒΑΤΗΡΙΩΝ", "meaning": "パスポートの"}
        ]
    },
    {
        "greek": "ΤΕΛΩΝΕΙΟ",
        "reading": "テロニオ",
        "meaning": "税関（CUSTOMS・看板）",
        "category": "空港・飛行機",
        "level": "初級",
        "speaker": "看板",
        "breakdown": [{"word": "ΤΕΛΩΝΕΙΟ", "meaning": "税関"}]
    },
    {
        "greek": "ΑΚΥΡΩΘΗΚΕ",
        "reading": "アキロシケ",
        "meaning": "欠航 / キャンセル（フライト電光掲示板の赤文字）",
        "category": "空港・飛行機",
        "level": "中級",
        "speaker": "看板",
        "breakdown": [{"word": "ΑΚΥΡΩΘΗΚΕ", "meaning": "キャンセルされました/欠航"}]
    },
    {
        "greek": "ΚΑΘΥΣΤΕΡΗΣΗ",
        "reading": "カシスィテリスィ",
        "meaning": "遅延 / DELAY（フライト電光掲示板の表示）",
        "category": "空港・飛行機",
        "level": "中級",
        "speaker": "看板",
        "breakdown": [{"word": "ΚΑΘΥΣΤΕΡΗΣΗ", "meaning": "遅延/遅れ"}]
    },

    # === タクシー・交通（超強化） ===
    {
        "greek": "Ταξί",
        "reading": "タクシ",
        "meaning": "タクシー（単語）",
        "category": "タクシー・交通",
        "level": "初級",
        "speaker": "自分",
        "breakdown": [{"word": "Ταξί", "meaning": "タクシー"}]
    },
    {
        "greek": "Στο αεροδρόμιο, παρακαλώ.",
        "reading": "スト アエロドロミオ, パラカロ",
        "meaning": "空港までお願いします",
        "category": "タクシー・交通",
        "level": "初級",
        "speaker": "自分",
        "breakdown": [
            {"word": "Στο", "meaning": "〜まで / 〜へ"},
            {"word": "αεροδρόμιο,", "meaning": "空港"},
            {"word": "παρακαλώ.", "meaning": "お願いします"}
        ]
    },
    {
        "greek": "Στο ξεノδοχείο, παρακαλώ.",
        "greek": "Στο ξενοδοχείο, παρακαλώ.",
        "reading": "スト クセノドヒオ, パラカロ",
        "meaning": "ホテルまでお願いします",
        "category": "タクシー・交通",
        "level": "初級",
        "speaker": "自分",
        "breakdown": [
            {"word": "Στο", "meaning": "〜まで / 〜へ"},
            {"word": "ξενοδοχείο,", "meaning": "ホテル"},
            {"word": "παρακαλώ.", "meaning": "お願いします"}
        ]
    },
    {
        "greek": "Σταマτήστε εδώ, παρακαλώ.",
        "greek": "Σταματήστε εδώ, παρακαλώ.",
        "reading": "スタマティステ エド, パラカロ",
        "meaning": "ここで止めてください",
        "category": "タクシー・交通",
        "level": "初級",
        "speaker": "自分",
        "breakdown": [
            {"word": "Σταματήστε", "meaning": "止めてください"},
            {"word": "εδώ,", "meaning": "ここで"},
            {"word": "παρακαλώ.", "meaning": "お願いします"}
        ]
    },
    {
        "greek": "Περίπου πόσο θα κοστίσει;",
        "reading": "ペリプ ポソ サ コスティーシ？",
        "meaning": "そこまで大体いくらかかりますか？（ぼったくり防止）",
        "category": "タクシー・交通",
        "level": "中級",
        "speaker": "自分",
        "breakdown": [
            {"word": "Περίπου", "meaning": "大体/およそ"},
            {"word": "πόσο", "meaning": "いくら"},
            {"word": "θα κοστίσει;", "meaning": "費用がかかりますか"}
        ]
    },
    {
        "greek": "Είναι πολύ ακριβό!",
        "reading": "イネ ポリ アクリヴォ！",
        "meaning": "高すぎます！（不当な請求への抗議）",
        "category": "タクシー・交通",
        "level": "中級",
        "speaker": "自分",
        "breakdown": [
            {"word": "Είναι", "meaning": "〜です"},
            {"word": "πολύ", "meaning": "とても"},
            {"word": "ακριβό!", "meaning": "高額な/高い"}
        ]
    },
    {
        "greek": "Βιάζομαι, έχω πτήση!",
        "reading": "ヴィアゾメ, エホ プティスィ！",
        "meaning": "急いでいます、飛行機に間に合わなくなります！",
        "category": "タクシー・交通",
        "level": "中級",
        "speaker": "自分",
        "breakdown": [
            {"word": "Βιάζομαι,", "meaning": "急いでいます"},
            {"word": "έχω", "meaning": "持っています"},
            {"word": "πτήση!", "meaning": "フライトを"}
        ]
    },
    {
        "greek": "Ανοίξτε το κλιματιστικό, παρακαλώ.",
        "reading": "アニクステ ト クリマティスティコ, パラカロ",
        "meaning": "エアコンをつけてもらえますか？",
        "category": "タクシー・交通",
        "level": "中級",
        "speaker": "自分",
        "breakdown": [
            {"word": "Ανοίξτε", "meaning": "つけてください/開けて"},
            {"word": "το κλιματιστικό,", "meaning": "エアコンを"},
            {"word": "παρακαλώ.", "meaning": "お願いします"}
        ]
    },
    {
        "greek": "Κλείστε το κλιματιστικό, παρακαλώ.",
        "reading": "クリステ ト クリマティスティコ, パラカロ",
        "meaning": "エアコンを消してください（寒すぎる時）",
        "category": "タクシー・交通",
        "level": "中級",
        "speaker": "自分",
        "breakdown": [
            {"word": "Κλείστε", "meaning": "消してください/閉めて"},
            {"word": "το κλιματιστικό,", "meaning": "エアコンを"},
            {"word": "παρακαλώ.", "meaning": "お願いします"}
        ]
    },
    {
        "greek": "Στη γωνία, παρακαλώ.",
        "reading": "スティ ゴニア, パラカロ",
        "meaning": "あの角のところで降ろしてください",
        "category": "タクシー・交通",
        "level": "中級",
        "speaker": "自分",
        "breakdown": [
            {"word": "Στη γωνία,", "meaning": "角のところで"},
            {"word": "παρακαλώ.", "meaning": "お願いします"}
        ]
    },
    {
        "greek": "Τα ρέスタ δεν είναι σωστά.",
        "greek": "Τα ρέστα δεν είναι σωστά.",
        "reading": "タ レスタ デン イネ ソスタ",
        "meaning": "おつりが合っていません / 足りません",
        "category": "タクシー・交通",
        "level": "上級",
        "speaker": "自分",
        "breakdown": [
            {"word": "Τα ρέστα", "meaning": "おつりが"},
            {"word": "δεν είναι", "meaning": "〜ではない"},
            {"word": "σωστά.", "meaning": "正しい"}
        ]
    },
    {
        "greek": "Ξέχασα κάτι στο ταξί!",
        "reading": "クセハサ カティ スト タクシ！",
        "meaning": "タクシーの中に忘れ物をしてしまいました！",
        "category": "タクシー・交通",
        "level": "上級",
        "speaker": "自分",
        "breakdown": [
            {"word": "Ξέχασα", "meaning": "忘れました"},
            {"word": "κάτι", "meaning": "何かを"},
            {"word": "στο ταξί!", "meaning": "タクシーの中に"}
        ]
    },
    {
        "greek": "Βάλτε το ταξίμετρο, παρακαλώ.",
        "reading": "ヴァルテ ト タクシメトロ, パラカロ",
        "meaning": "メーターを回してください",
        "category": "タクシー・交通",
        "level": "上級",
        "speaker": "自分",
        "breakdown": [
            {"word": "Βάλτε", "meaning": "回してください / 入れて"},
            {"word": "το", "meaning": "その"},
            {"word": "ταξίμετρο,", "meaning": "メーター"},
            {"word": "παρακαλώ.", "meaning": "お願いします"}
        ]
    },
    {
        "greek": "Μπορώ να πληρώσω με κάρτα;",
        "reading": "ボロ ナ プリロソ メ カルタ？",
        "meaning": "クレジットカードで支払えますか？",
        "category": "タクシー・交通",
        "level": "上級",
        "speaker": "自分",
        "breakdown": [
            {"word": "Μπορώ", "meaning": "〜できますか"},
            {"word": "να", "meaning": "〜すること"},
            {"word": "πληρώσω", "meaning": "支払う"},
            {"word": "με", "meaning": "〜で"},
            {"word": "κάρτα;", "meaning": "カード"}
        ]
    },
    {
        "greek": "Πού θέλετε να πάτε;",
        "reading": "プ セレテ ナ パテ？",
        "meaning": "どちらまで行かれますか？（運転手の声かけ）",
        "category": "タクシー・交通",
        "level": "上級",
        "speaker": "スタッフ",
        "breakdown": [
            {"word": "Πού", "meaning": "どこへ"},
            {"word": "θέλετε", "meaning": "行きたいですか"},
            {"word": "να", "meaning": "〜すること"},
            {"word": "πάτε;", "meaning": "行く"}
        ]
    },
    {
        "greek": "Έχει πολλή κίνηση.",
        "reading": "エヒ ポリ キニスィ",
        "meaning": "道路がひどく渋滞しています（運転手のセリフ）",
        "category": "タクシー・交通",
        "level": "上級",
        "speaker": "スタッフ",
        "breakdown": [
            {"word": "Έχει", "meaning": "あります"},
            {"word": "πολλή", "meaning": "たくさんの"},
            {"word": "κίνηση.", "meaning": "交通（渋滞）"}
        ]
    },
    {
        "greek": "Υπάρχουν διόδια.",
        "reading": "イパルフン ディオディア",
        "meaning": "有料道路（高速料金）が加算されます",
        "category": "タクシー・交通",
        "level": "上級",
        "speaker": "スタッフ",
        "breakdown": [
            {"word": "Υπάρχουν", "meaning": "あります"},
            {"word": "διόδια.", "meaning": "通行料金/有料道路代"}
        ]
    },

    # === ホテル・宿泊（超強化） ===
    {
        "greek": "ΥΠΟΔΟΧΗ",
        "reading": "イポドヒ",
        "meaning": "フロント / レセプション（ホテルの案内看板）",
        "category": "ホテル",
        "level": "初級",
        "speaker": "看板",
        "breakdown": [{"word": "ΥΠΟΔΟΧΗ", "meaning": "レセプション / フロント"}]
    },
    {
        "greek": "Το κλειδί",
        "reading": "ト クリディ",
        "meaning": "部屋の鍵（単語）",
        "category": "ホテル",
        "level": "初級",
        "speaker": "自分",
        "breakdown": [{"word": "Το κλειδί", "meaning": "鍵"}]
    },
    {
        "greek": "Το κλειδί, παρακαλώ.",
        "reading": "ト クリディ, パラカロ",
        "meaning": "部屋の鍵をください",
        "category": "ホテル",
        "level": "初級",
        "speaker": "自分",
        "breakdown": [
            {"word": "Το κλειδί,", "meaning": "鍵を"},
            {"word": "παρακαλώ.", "meaning": "お願いします"}
        ]
    },
    {
        "greek": "Έχω κάνει κράτηση.",
        "reading": "エホ カニ クラティスィ",
        "meaning": "予約をしています（チェックイン時）",
        "category": "ホテル",
        "level": "初級",
        "speaker": "自分",
        "breakdown": [
            {"word": "Έχω κάνει", "meaning": "しました"},
            {"word": "κράτηση.", "meaning": "予約を"}
        ]
    },
    {
        "greek": "Ποιος είναι ο κωδικός του Wi-Fi;",
        "reading": "ピオス イネ オ コディコス トゥ ワイファイ？",
        "meaning": "Wi-Fiのパスワードは何ですか？",
        "category": "ホテル",
        "level": "初級",
        "speaker": "自分",
        "breakdown": [
            {"word": "Ποιος είναι", "meaning": "何ですか"},
            {"word": "ο κωδικός", "meaning": "暗証番号/パスワード"},
            {"word": "του Wi-Fi;", "meaning": "Wi-Fiの"}
        ]
    },
    {
        "greek": "Μπορείτε να κρατήσετε τις βαλίτσες μου;",
        "reading": "ボリテ ナ クラティセテ ティス ヴァリツェス ム？",
        "meaning": "荷物を預かってもらえますか？（チェックイン前・後）",
        "category": "ホテル",
        "level": "中級",
        "speaker": "自分",
        "breakdown": [
            {"word": "Μπορείτε", "meaning": "〜できますか"},
            {"word": "να κρατήσετε", "meaning": "預かる/保管する"},
            {"word": "τις βαλίτσες μου;", "meaning": "私のスーツケースを"}
        ]
    },
    {
        "greek": "Δεν έχει ζεστό νερό.",
        "reading": "デン エヒ ゼスト ネロ",
        "meaning": "お湯が出ません（シャワートラブル）",
        "category": "ホテル",
        "level": "中級",
        "speaker": "自分",
        "breakdown": [
            {"word": "Δεν έχει", "meaning": "ありません/出ません"},
            {"word": "ζεστό", "meaning": "温かい"},
            {"word": "νερό.", "meaning": "水（お湯）"}
        ]
    },
    {
        "greek": "Το κλιματιστικό δεν δουλεύει.",
        "reading": "ト クリマティスティコ デン ドゥレヴィ",
        "meaning": "エアコンが故障していて動きません",
        "category": "ホテル",
        "level": "中級",
        "speaker": "自分",
        "breakdown": [
            {"word": "Το κλιματιστικό", "meaning": "エアコンが"},
            {"word": "δεν δουλεύει.", "meaning": "動かない/機能しない"}
        ]
    },
    {
        "greek": "Η τουαλέτα έχει βουλώσει.",
        "reading": "イ トゥアレタ エヒ ヴロシ",
        "meaning": "トイレが詰まって流れません",
        "category": "ホテル",
        "level": "中級",
        "speaker": "自分",
        "breakdown": [
            {"word": "Η τουαλέτα", "meaning": "トイレが"},
            {"word": "έχει βουλώσει.", "meaning": "詰まっています"}
        ]
    },
    {
        "greek": "Μια πετσέτα ακόμα, παρακαλώ.",
        "reading": "ミア ペチェタ アコマ, パラカロ",
        "meaning": "タオルをもう1枚いただけますか？",
        "category": "ホテル",
        "level": "中級",
        "speaker": "自分",
        "breakdown": [
            {"word": "Μια πετσέτα", "meaning": "タオルを1枚"},
            {"word": "ακόμα,", "meaning": "もう/さらに"},
            {"word": "παρακαλώ.", "meaning": "お願いします"}
        ]
    },
    {
        "greek": "Το διπλανό δωμάτιο έχει πολύ θόρυβο.",
        "reading": "ト ディプラノ ドマティオ エヒ ポリ ソリヴォ",
        "meaning": "隣の部屋がとても騒がしい（うるさい）です",
        "category": "ホテル",
        "level": "上級",
        "speaker": "自分",
        "breakdown": [
            {"word": "Το διπλανό δωμάτιο", "meaning": "隣の部屋が"},
            {"word": "έχει", "meaning": "あります"},
            {"word": "πολύ θόρυβο.", "meaning": "とても大きな騒音が"}
        ]
    },
    {
        "greek": "Μπορώ να κάνω αργότερα check-out;",
        "reading": "ボロ ナ カノ アルゴテラ チェックアウト？",
        "meaning": "レイトチェックアウト（遅めの出発）は可能ですか？",
        "category": "ホテル",
        "level": "上級",
        "speaker": "自分",
        "breakdown": [
            {"word": "Μπορώ", "meaning": "〜できますか"},
            {"word": "να κάνω", "meaning": "する"},
            {"word": "αργότερα", "meaning": "より遅くに"},
            {"word": "check-out;", "meaning": "チェックアウト"}
        ]
    },
    {
        "greek": "Σε ποιο όνομα είναι η κράτηση;",
        "reading": "セ ピオ オノマ イネ イ クラティスィ？",
        "meaning": "ご予約のお名前は何様でしょうか？",
        "category": "ホテル",
        "level": "上級",
        "speaker": "スタッフ",
        "breakdown": [
            {"word": "Σε ποιο", "meaning": "どの / 何の"},
            {"word": "όνομα", "meaning": "名前"},
            {"word": "είναι", "meaning": "〜ですか"},
            {"word": "η κράτηση;", "meaning": "ご予約"}
        ]
    },
    {
        "greek": "Το πρωινό είναι από τις εφτά μέχρι τις δέκα.",
        "reading": "ト プロイノ イネ アポ ティス エフタ メフリ ティス デカ",
        "meaning": "ご朝食は7時から10時までです",
        "category": "ホテル",
        "level": "上級",
        "speaker": "スタッフ",
        "breakdown": [
            {"word": "Το πρωινό", "meaning": "朝食は"},
            {"word": "είναι", "meaning": "〜です"},
            {"word": "από τις εφτά", "meaning": "7時から"},
            {"word": "μέχρι τις δέκα.", "meaning": "10時まで"}
        ]
    },
    {
        "greek": "Το δωμάτιό σας είναι στον τρίτο όροφο.",
        "reading": "ト ドマティオ サス イネ ストン トリート オロフォ",
        "meaning": "お部屋は3階でございます",
        "category": "ホテル",
        "level": "上級",
        "speaker": "スタッフ",
        "breakdown": [
            {"word": "Το δωμάτιό σας", "meaning": "あなたのお部屋は"},
            {"word": "είναι", "meaning": "あります"},
            {"word": "στον τρίτο", "meaning": "3階の"},
            {"word": "όροφο.", "meaning": "フロアに"}
        ]
    },
    {
        "greek": "Πρέπει να πληρώσετε το φόρο διαμονής.",
        "reading": "プレピ ナ プリロセテ ト フォロ ディアモニス",
        "meaning": "宿泊税（観光税）のお支払いが必要です（チェックイン時）",
        "category": "ホテル",
        "level": "上級",
        "speaker": "スタッフ",
        "breakdown": [
            {"word": "Πρέπει να", "meaning": "〜しなければならない"},
            {"word": "πληρώσετε", "meaning": "支払う"},
            {"word": "το φόρο", "meaning": "税金を"},
            {"word": "διαμονής.", "meaning": "宿泊の"}
        ]
    },
    {
        "greek": "Το check-out είναι στις έντεκα το πρωί.",
        "reading": "ト チェックアウト イネ スティス エンテカ ト プロイ",
        "meaning": "チェックアウトは午前11時となっております",
        "category": "ホテル",
        "level": "上級",
        "speaker": "スタッフ",
        "breakdown": [
            {"word": "Το check-out", "meaning": "チェックアウトは"},
            {"word": "είναι", "meaning": "〜です"},
            {"word": "στις έντεκα", "meaning": "11時に"},
            {"word": "το πρωί.", "meaning": "午前（朝）の"}
        ]
    },
    {
        "greek": "Χρειαζόμαστε μια πιστωτική κάρτα για εγγύηση.",
        "reading": "フリアゾマステ ミア ピストティキ カルタ ヤ エンギイスィ",
        "meaning": "保証（デポジット）用のクレジットカードをお預かりします",
        "category": "ホテル",
        "level": "上級",
        "speaker": "スタッフ",
        "breakdown": [
            {"word": "Χρειαζόμαστε", "meaning": "必要です"},
            {"word": "μια πιστωτική κάρτα", "meaning": "クレジットカードが"},
            {"word": "για εγγύηση.", "meaning": "保証（デポジット）のために"}
        ]
    },

    # === 街の看板・標識 ===
    {
        "greek": "ΕΞΟΔΟΣ",
        "reading": "エグソドス",
        "meaning": "出口（街中・空港・駅の最重要看板）",
        "category": "街の看板・標識",
        "level": "初級",
        "speaker": "看板",
        "breakdown": [{"word": "ΕΞΟΔΟΣ", "meaning": "出口（EXIT）"}]
    },
    {
        "greek": "ΕΙΣΟΔΟΣ",
        "reading": "イソドス",
        "meaning": "入口（ドア・建物の案内看板）",
        "category": "街の看板・標識",
        "level": "初級",
        "speaker": "看板",
        "breakdown": [{"word": "ΕΙΣΟΔΟΣ", "meaning": "入口（ENTRANCE）"}]
    },
    {
        "greek": "ΑΝΟΙΚΤΟ",
        "reading": "アニックト",
        "meaning": "営業中 / OPEN（店の扉の札）",
        "category": "街の看板・標識",
        "level": "初級",
        "speaker": "看板",
        "breakdown": [{"word": "ΑΝΟΙΚΤΟ", "meaning": "営業中（開いています）"}]
    },
    {
        "greek": "ΚΛΕΙΣΤΟ",
        "reading": "クリスト",
        "meaning": "準備中 / 閉店 / CLOSED（店の扉の札）",
        "category": "街の看板・標識",
        "level": "初級",
        "speaker": "看板",
        "breakdown": [{"word": "ΚΛΕΙΣΤΟ", "meaning": "閉店 / 休業中"}]
    },
    {
        "greek": "ΤΑΜΕΙΟ",
        "reading": "タミオ",
        "meaning": "お会計 / レジ（店舗・スーパーの頭上看板）",
        "category": "街の看板・標識",
        "level": "初級",
        "speaker": "看板",
        "breakdown": [{"word": "ΤΑΜΕΙΟ", "meaning": "レジ / キャッシャー"}]
    },

    # === 売店・スーパー・買い物 ===
    {
        "greek": "Ευρώ",
        "reading": "エヴロ",
        "meaning": "ユーロ（通貨・単語）",
        "category": "売店・買い物",
        "level": "初級",
        "speaker": "自分",
        "breakdown": [{"word": "Ευρώ", "meaning": "ユーロ（€）"}]
    },
    {
        "greek": "Πόσο κάνει;",
        "reading": "ポソ カニ？",
        "meaning": "これいくらですか？",
        "category": "売店・買い物",
        "level": "初級",
        "speaker": "自分",
        "breakdown": [
            {"word": "Πόσο", "meaning": "いくら"},
            {"word": "κάνει;", "meaning": "しますか"}
        ]
    },
    {
        "greek": "Μια σακούλα, παρακαλώ.",
        "reading": "ミア サクラ, パラカロ",
        "meaning": "レジ袋を1枚ください",
        "category": "売店・買い物",
        "level": "初級",
        "speaker": "自分",
        "breakdown": [
            {"word": "Μια σακούλα,", "meaning": "レジ袋を1枚"},
            {"word": "παρακαλώ.", "meaning": "お願いします"}
        ]
    },
    {
        "greek": "Μπορώ να πληρώσω με μετρητά;",
        "reading": "ボロ ナ プリロソ メ メトリタ？",
        "meaning": "現金で支払えますか？",
        "category": "売店・買い物",
        "level": "中級",
        "speaker": "自分",
        "breakdown": [
            {"word": "Μπορώ", "meaning": "〜できますか"},
            {"word": "να πληρώσω", "meaning": "支払う"},
            {"word": "με μετρητά;", "meaning": "現金で"}
        ]
    },
    {
        "greek": "Χρειάζεστε απόδειξη;",
        "reading": "フリアゼステ アポディクスィ？",
        "meaning": "レシート（領収書）はご利用ですか？",
        "category": "売店・買い物",
        "level": "上級",
        "speaker": "スタッフ",
        "breakdown": [
            {"word": "Χρειάζεστε", "meaning": "必要ですか"},
            {"word": "απόδειξη;", "meaning": "レシート / 領収書"}
        ]
    },
    {
        "greek": "Μπορείτε να κάνετε καλύτερη τιμή;",
        "reading": "ボリテ ナ カネテ カリテリ ティミ？",
        "meaning": "少しおまけ（値引き）してもらえませんか？",
        "category": "売店・買い物",
        "level": "上級",
        "speaker": "自分",
        "breakdown": [
            {"word": "Μπορείτε", "meaning": "〜できますか"},
            {"word": "να κάνετε", "meaning": "する / まける"},
            {"word": "καλύτερη", "meaning": "より良い（安く）"},
            {"word": "τιμή;", "meaning": "値段 / 価格"}
        ]
    },

    # === 施設・道案内 ===
    {
        "greek": "Πού είναι η τουαλέτα;",
        "reading": "プ イネ イ トゥアレタ？",
        "meaning": "トイレはどこにありますか？",
        "category": "施設・道案内",
        "level": "初級",
        "speaker": "自分",
        "breakdown": [
            {"word": "Πού", "meaning": "どこ"},
            {"word": "είναι", "meaning": "ありますか"},
            {"word": "η τουαλέτα;", "meaning": "トイレ"}
        ]
    },
    {
        "greek": "Πού είναι ο σταθμός του μετρό;",
        "reading": "プ イネ オ スタスモス トゥ メトロ？",
        "meaning": "地下鉄の駅はどこですか？",
        "category": "施設・道案内",
        "level": "初級",
        "speaker": "自分",
        "breakdown": [
            {"word": "Πού", "meaning": "どこ"},
            {"word": "είναι", "meaning": "ありますか"},
            {"word": "ο σταθμός", "meaning": "駅"},
            {"word": "του μετρό;", "meaning": "地下鉄の"}
        ]
    },
    {
        "greek": "Πηγαίνετε ευθεία και στρίψτε δεξιά.",
        "reading": "ピゲネテ エフスィア ケ ストリプステ デクスィア",
        "meaning": "まっすぐ行って右に曲がってください（道案内）",
        "category": "施設・道案内",
        "level": "上級",
        "speaker": "スタッフ",
        "breakdown": [
            {"word": "Πηγαίνετε", "meaning": "行ってください"},
            {"word": "ευθεία", "meaning": "まっすぐに"},
            {"word": "και", "meaning": "そして"},
            {"word": "στρίψτε", "meaning": "曲がってください"},
            {"word": "δεξιά.", "meaning": "右へ"}
        ]
    },

    # === 緊急・トラブル ===
    {
        "greek": "Βοήθεια!",
        "reading": "ヴォイシィア！",
        "meaning": "助けて！",
        "category": "緊急・トラブル",
        "level": "初級",
        "speaker": "自分",
        "breakdown": [{"word": "Βοήθεια!", "meaning": "助けて！"}]
    },
    {
        "greek": "Σταματήστε!",
        "reading": "スタマティステ！",
        "meaning": "やめて！ / 止まって！",
        "category": "緊急・トラブル",
        "level": "初級",
        "speaker": "自分",
        "breakdown": [{"word": "Σταματήστε!", "meaning": "やめて！ / 止まって！"}]
    },
    {
        "greek": "Δεν νιώθω καλά.",
        "reading": "デン ニオソ カラ",
        "meaning": "気分が悪いです / 体調がすぐれません",
        "category": "緊急・トラブル",
        "level": "中級",
        "speaker": "自分",
        "breakdown": [
            {"word": "Δεν", "meaning": "〜ない"},
            {"word": "νιώθω", "meaning": "感じる"},
            {"word": "καλά.", "meaning": "良く / 元気に"}
        ]
    },
    {
        "greek": "Έχασα το πορτοφόλι μου.",
        "reading": "エハサ ト ポルトフォリ ム",
        "meaning": "財布を落として（盗まれて）しまいました",
        "category": "緊急・トラブル",
        "level": "中級",
        "speaker": "自分",
        "breakdown": [
            {"word": "Έχασα", "meaning": "失くしました"},
            {"word": "το πορτοφόλι", "meaning": "財布を"},
            {"word": "μου.", "meaning": "私の"}
        ]
    },
    {
        "greek": "Χρειάζομαι γιατρό.",
        "reading": "フリアゾメ ヤトロ",
        "meaning": "医者が必要です / 呼んでください",
        "category": "緊急・トラブル",
        "level": "中級",
        "speaker": "自分",
        "breakdown": [
            {"word": "Χρειάζομαι", "meaning": "必要としています"},
            {"word": "γιατρό.", "meaning": "医者を"}
        ]
    },
    {
        "greek": "Καλέστε την αστυνομία!",
        "reading": "カレステ ティン アスティノミア！",
        "meaning": "警察を呼んでください！",
        "category": "緊急・トラブル",
        "level": "上級",
        "speaker": "自分",
        "breakdown": [
            {"word": "Καλέστε", "meaning": "呼んでください"},
            {"word": "την αστυνομία!", "meaning": "警察を"}
        ]
    },
    {
        "greek": "Πού ακριβώς πονάτε;",
        "reading": "プ アクリヴォス ポナテ？",
        "meaning": "具体的にどこが痛みますか？（医師・薬剤師）",
        "category": "緊急・トラブル",
        "level": "上級",
        "speaker": "スタッフ",
        "breakdown": [
            {"word": "Πού", "meaning": "どこが"},
            {"word": "ακριβώς", "meaning": "具体的に / 正確に"},
            {"word": "πονάτε;", "meaning": "痛みますか"}
        ]
    },
    {
        "greek": "Έχετε κάποια αλλεργία;",
        "reading": "エヘテ カピア アレルギア？",
        "meaning": "何かアレルギーはお持ちですか？",
        "category": "緊急・トラブル",
        "level": "上級",
        "speaker": "スタッフ",
        "breakdown": [
            {"word": "Έχετε", "meaning": "ありますか"},
            {"word": "κάποια", "meaning": "何か"},
            {"word": "αλλεργία;", "meaning": "アレルギー"}
        ]
    },
]

# -------------------------------------------------------------
# 3. 音声生成 ＆ カタカナ変換 ＆ 発音判定関数
# -------------------------------------------------------------
@st.cache_data
def get_greek_audio(text):
    tts = gTTS(text=text, lang="el")
    fp = io.BytesIO()
    tts.write_to_fp(fp)
    fp.seek(0)
    return fp.read()

def normalize_greek(text):
    nfd = unicodedata.normalize('NFD', text.lower())
    no_accents = ''.join(c for c in nfd if unicodedata.category(c) != 'Mn')
    no_accents = no_accents.replace('ς', 'σ')
    clean = re.sub(r'[^\w\s]', '', no_accents).strip()
    return ' '.join(clean.split())

def greek_to_katakana(text):
    """ギリシャ文字をネイティブ風のカタカナ読みに自動変換するエンジン"""
    if not text:
        return ""
    t = text.lower()

    subs = [
        ('γεια', 'ヤ'), ('γει', 'イェ'), ('για', 'ヤ'), ('γιο', 'ヨ'), ('γιου', 'ユ'),
        ('μπ', 'b'), ('ντ', 'd'), ('γκ', 'g'), ('γγ', 'ng'),
        ('ευ', 'ef'), ('αυ', 'af'), ('ου', 'u'),
        ('αι', 'e'), ('ει', 'i'), ('οι', 'i'), ('υι', 'i'),
        ('τσ', 'ts'), ('τζ', 'dz'),
        ('α', 'a'), ('β', 'v'), ('γ', 'g'), ('δ', 'dh'), ('ε', 'e'),
        ('ζ', 'z'), ('η', 'i'), ('θ', 'th'), ('ι', 'i'), ('κ', 'k'),
        ('λ', 'l'), ('μ', 'm'), ('ν', 'n'), ('ξ', 'x'), ('ο', 'o'),
        ('π', 'p'), ('ρ', 'r'), ('σ', 's'), ('ς', 's'), ('τ', 't'),
        ('υ', 'i'), ('φ', 'f'), ('χ', 'h'), ('ψ', 'ps'), ('ω', 'o'),
        ('ά', 'a'), ('έ', 'e'), ('ή', 'i'), ('ί', 'i'), ('ό', 'o'),
        ('ύ', 'i'), ('ώ', 'o'), ('ϊ', 'i'), ('ϋ', 'i')
    ]

    table = [
        ('tsu', 'ツ'), ('shi', 'シ'), ('chi', 'チ'), ('dzu', 'ヅ'),
        ('kya', 'キャ'), ('kyu', 'キュ'), ('kyo', 'キョ'),
        ('sha', 'シャ'), ('shu', 'シュ'), ('sho', 'ショ'),
        ('cha', 'チャ'), ('chu', 'チュ'), ('cho', 'チョ'),
        ('nya', 'ニャ'), ('nyu', 'ニュ'), ('nyo', 'ニョ'),
        ('hya', 'ヒャ'), ('hyu', 'ヒュ'), ('hyo', 'ヒョ'),
        ('mya', 'ミャ'), ('myu', 'ミュ'), ('myo', 'ミョ'),
        ('rya', 'リャ'), ('ryu', 'リュ'), ('ryo', 'リョ'),
        ('gya', 'ギャ'), ('gyu', 'ギュ'), ('gyo', 'ギョ'),
        ('bya', 'ビャ'), ('byu', 'ビュ'), ('byo', 'ビョ'),
        ('pya', 'ピャ'), ('pyu', 'ピュ'), ('pyo', 'ピョ'),
        ('fa', 'ファ'), ('fi', 'フィ'), ('fe', 'フェ'), ('fo', 'フォ'), ('fu', 'フ'),
        ('va', 'ヴァ'), ('vi', 'ヴィ'), ('vu', 'ヴ'), ('ve', 'ヴェ'), ('vo', 'ヴォ'), ('v', 'ヴ'),
        ('dha', 'ザ'), ('dhi', 'ズィ'), ('dhu', 'ズ'), ('dhe', 'ゼ'), ('dho', 'ゾ'), ('dh', 'ズ'),
        ('tha', 'サ'), ('thi', 'スィ'), ('thu', 'ス'), ('the', 'セ'), ('tho', 'ソ'), ('th', 'ス'),
        ('dza', 'ザ'), ('dzi', 'ズィ'), ('dzu', 'ズ'), ('dze', 'ゼ'), ('dzo', 'ゾ'), ('dz', 'ズ'),
        ('tsa', 'ツァ'), ('tsi', 'ツィ'), ('tse', 'ツェ'), ('tso', 'ツォ'), ('ts', 'ツ'),
        ('xa', 'クサ'), ('xi', 'クシ'), ('xu', 'クス'), ('xe', 'クセ'), ('xo', 'クソ'),
        ('psa', 'プサ'), ('psi', 'プシ'), ('psu', 'プス'), ('pse', 'プセ'), ('pso', 'プソ'),
        ('ka', 'カ'), ('ki', 'キ'), ('ku', 'ク'), ('ke', 'ケ'), ('ko', 'コ'),
        ('ga', 'ガ'), ('gi', 'ギ'), ('gu', 'グ'), ('ge', 'ゲ'), ('go', 'ゴ'),
        ('sa', 'サ'), ('si', 'シ'), ('su', 'ス'), ('se', 'セ'), ('so', 'ソ'),
        ('za', 'ザ'), ('zi', 'ジ'), ('zu', 'ズ'), ('ze', 'ゼ'), ('zo', 'ゾ'),
        ('ta', 'タ'), ('ti', 'ティ'), ('tu', 'トゥ'), ('te', 'テ'), ('to', 'ト'),
        ('da', 'ダ'), ('di', 'ディ'), ('du', 'ドゥ'), ('de', 'デ'), ('do', 'ド'),
        ('na', 'ナ'), ('ni', 'ニ'), ('nu', 'ヌ'), ('ne', 'ネ'), ('no', 'ノ'),
        ('ha', 'ハ'), ('hi', 'ヒ'), ('hu', 'フ'), ('he', 'ヘ'), ('ho', 'ホ'),
        ('ba', 'バ'), ('bi', 'ビ'), ('bu', 'ブ'), ('be', 'ベ'), ('bo', 'ボ'),
        ('pa', 'パ'), ('pi', 'ピ'), ('pu', 'プ'), ('pe', 'ペ'), ('po', 'ポ'),
        ('ma', 'マ'), ('mi', 'ミ'), ('mu', 'ム'), ('me', 'メ'), ('mo', 'モ'),
        ('ya', 'ヤ'), ('yu', 'ユ'), ('yo', 'ヨ'),
        ('ra', 'ラ'), ('ri', 'リ'), ('ru', 'ル'), ('re', 'レ'), ('ro', 'ロ'),
        ('la', 'ラ'), ('li', 'リ'), ('lu', 'ル'), ('le', 'レ'), ('lo', 'ロ'),
        ('wa', 'ワ'), ('wo', 'ヲ'),
        ('a', 'ア'), ('i', 'イ'), ('u', 'ウ'), ('e', 'エ'), ('o', 'オ'),
        ('k', 'ク'), ('g', 'グ'), ('s', 'ス'), ('z', 'ズ'), ('t', 'ト'),
        ('d', 'ド'), ('n', 'ン'), ('h', 'フ'), ('b', 'ブ'), ('p', 'プ'),
        ('m', 'ム'), ('r', 'ル'), ('l', 'ル'), ('x', 'クス'), ('f', 'フ'),
    ]

    for g, r in subs:
        t = t.replace(g, r)
    for r, k in table:
        t = t.replace(r, k)
    return t

def evaluate_pronunciation(audio_file, target_greek):
    if not SPEECH_REC_AVAILABLE:
        return None, "SPEECH_REC_NOT_INSTALLED"

    r = sr.Recognizer()
    try:
        with sr.AudioFile(audio_file) as source:
            audio_data = r.record(source)
        recognized = r.recognize_google(audio_data, language="el-GR")
        
        norm_target = normalize_greek(target_greek)
        norm_rec = normalize_greek(recognized)
        score = SequenceMatcher(None, norm_target, norm_rec).ratio()
        return recognized, round(score * 100)
    except sr.UnknownValueError:
        return None, "UNKNOWN_VALUE"
    except Exception as e:
        return None, str(e)

# -------------------------------------------------------------
# 4. 単語タップ可能なHTML文章生成関数
# -------------------------------------------------------------
def render_duo_sentence(q, q_num):
    breakdown = q.get("breakdown", [])
    if not breakdown:
        st.subheader(f"「 {q['greek']} 」")
        return

    chips = []
    for item in breakdown:
        word = item["word"]
        meaning = item["meaning"]
        chip = f'<span class="duo-word" tabindex="0">{word}<span class="duo-tooltip">{meaning}</span></span>'
        chips.append(chip)

    html = f'''
    <div id="duo-q-{q_num}" class="duo-sentence-box">
      <span class="duo-quote">「</span>{' '.join(chips)}<span class="duo-quote">」</span>
    </div>
    '''
    st.markdown(html, unsafe_allow_html=True)

# -------------------------------------------------------------
# 5. 学習ステータス管理
# -------------------------------------------------------------
if "hearts" not in st.session_state:
    st.session_state.hearts = 5
if "xp" not in st.session_state:
    st.session_state.xp = 0
if "streak" not in st.session_state:
    st.session_state.streak = 0
if "q_count" not in st.session_state:
    st.session_state.q_count = 0
if "current_q" not in st.session_state:
    st.session_state.current_q = None
if "choices" not in st.session_state:
    st.session_state.choices = []
if "is_listening_mode" not in st.session_state:
    st.session_state.is_listening_mode = False
if "answered" not in st.session_state:
    st.session_state.answered = False
if "is_correct" not in st.session_state:
    st.session_state.is_correct = False
if "last_filter_key" not in st.session_state:
    st.session_state.last_filter_key = ""

if "deck" not in st.session_state:
    st.session_state.deck = []
if "wrong_questions" not in st.session_state:
    st.session_state.wrong_questions = []
if "is_review_mode" not in st.session_state:
    st.session_state.is_review_mode = False
if "review_queue" not in st.session_state:
    st.session_state.review_queue = []

# -------------------------------------------------------------
# 6. サイドバー設定
# -------------------------------------------------------------
st.sidebar.header("🎯 学習モード設定")

categories = [
    "全場面（ランダム特訓）",
    "空港・飛行機",
    "タクシー・交通",
    "ホテル",
    "基本挨拶",
    "カフェ",
    "レストラン・名物料理",
    "街の看板・標識",
    "売店・買い物",
    "施設・道案内",
    "緊急・トラブル",
]
selected_cat = st.sidebar.selectbox("どの場面を勉強しますか？", categories, key="sb_cat")
levels = ["すべての難易度", "初級", "中級", "上級"]
selected_lvl = st.sidebar.selectbox("難易度（レベル）", levels, key="sb_lvl")

current_filter_key = f"{selected_cat}_{selected_lvl}"
filter_changed = False
if st.session_state.last_filter_key != current_filter_key:
    st.session_state.last_filter_key = current_filter_key
    st.session_state.deck = []
    filter_changed = True

st.sidebar.markdown("---")
if st.sidebar.button("🔄 ゲームをリセット", use_container_width=True, key="reset_btn"):
    st.session_state.hearts = 5
    st.session_state.xp = 0
    st.session_state.streak = 0
    st.session_state.deck = []
    st.session_state.wrong_questions = []
    st.session_state.is_review_mode = False
    st.session_state.review_queue = []
    filter_changed = True

if st.sidebar.button("🔒 ログアウト", use_container_width=True, key="logout_btn"):
    st.session_state.authenticated = False
    st.rerun()

# -------------------------------------------------------------
# 7. 山札方式 ＆ 親和性ブレンドによる高ランダム出題ロジック
# -------------------------------------------------------------
RELATED_CATEGORIES = {
    "空港・飛行機": ["空港・飛行機", "タクシー・交通", "施設・道案内", "街の看板・標識"],
    "タクシー・交通": ["タクシー・交通", "施設・道案内", "空港・飛行機", "ホテル"],
    "ホテル": ["ホテル", "基本挨拶", "売店・買い物", "タクシー・交通"],
    "カフェ": ["カフェ", "レストラン・名物料理", "売店・買い物"],
    "レストラン・名物料理": ["レストラン・名物料理", "カフェ", "売店・買い物"],
    "街の看板・標識": ["街の看板・標識", "施設・道案内", "空港・飛行機"],
    "施設・道案内": ["施設・道案内", "タクシー・交通", "街の看板・標識", "緊急・トラブル"],
    "基本挨拶": ["基本挨拶", "ホテル", "売店・買い物"],
    "売店・買い物": ["売店・買い物", "カフェ", "レストラン・名物料理", "基本挨拶"],
    "緊急・トラブル": ["緊急・トラブル", "施設・道案内", "タクシー・交通"],
}

def get_filtered_pool():
    pool = DATASET
    if selected_cat != "全場面（ランダム特訓）":
        pool = [q for q in pool if q["category"] == selected_cat]
    if selected_lvl != "すべての難易度":
        pool = [q for q in pool if q["level"] == selected_lvl]
    return pool

def next_question():
    if st.session_state.is_review_mode:
        if not st.session_state.review_queue:
            st.session_state.current_q = None
            return
        target = st.session_state.review_queue[0]
        st.session_state.current_q = target
    else:
        pool = get_filtered_pool()
        if not pool:
            st.session_state.current_q = None
            return

        if not st.session_state.deck:
            new_deck = list(pool)
            random.shuffle(new_deck)
            st.session_state.deck = new_deck

        target = st.session_state.deck.pop(0)
        st.session_state.current_q = target

    if target["category"] == "街の看板・標識":
        st.session_state.is_listening_mode = False
    else:
        st.session_state.is_listening_mode = random.random() < 0.30

    cat = target["category"]
    rel_cats = RELATED_CATEGORIES.get(cat, [cat])

    same_cat_wrong = [q["meaning"] for q in DATASET if q["category"] == cat and q["meaning"] != target["meaning"]]
    rel_cat_wrong = [q["meaning"] for q in DATASET if q["category"] in rel_cats and q["meaning"] != target["meaning"]]
    all_wrong = [q["meaning"] for q in DATASET if q["meaning"] != target["meaning"]]

    wrong_choices = []
    if same_cat_wrong:
        k_same = min(len(same_cat_wrong), random.choice([1, 2]))
        wrong_choices.extend(random.sample(same_cat_wrong, k_same))

    needed = 3 - len(wrong_choices)
    avail_rel = [m for m in rel_cat_wrong if m not in wrong_choices]
    if len(avail_rel) >= needed:
        wrong_choices.extend(random.sample(avail_rel, needed))
    else:
        wrong_choices.extend(avail_rel)
        needed2 = 3 - len(wrong_choices)
        avail_all = [m for m in all_wrong if m not in wrong_choices]
        wrong_choices.extend(random.sample(avail_all, min(needed2, len(avail_all))))

    choices = wrong_choices + [target["meaning"]]
    random.shuffle(choices)
    st.session_state.choices = choices
    st.session_state.answered = False
    st.session_state.q_count += 1

if filter_changed or (st.session_state.current_q is None and not st.session_state.is_review_mode):
    next_question()

# -------------------------------------------------------------
# 8. メイン学習画面
# -------------------------------------------------------------
st.title("🇬🇷 ギリシャ語特訓アプリ")

# =============================================================
# A. 復習特訓完了画面
# =============================================================
if st.session_state.is_review_mode and not st.session_state.review_queue:
    st.balloons()
    st.success("🎉 **お見事！ すべての間違いを完全に克服しました！**")
    st.markdown("""
    間違えた問題をすべて解き直し、完璧にマスターしました！  
    ライフが **❤️❤️❤️❤️❤️（5個満タン）** に全回復しました。
    """)
    st.markdown("---")
    st.subheader("さらに勉強をはじめますか？")
    if st.button("✨ はい、さらに勉強を始める（ライフ5個で再開）", use_container_width=True, key="continue_study_btn"):
        st.session_state.is_review_mode = False
        st.session_state.hearts = 5
        st.session_state.streak = 0
        st.session_state.wrong_questions = []
        st.session_state.deck = []
        st.session_state.answered = False
        next_question()
        st.rerun()
    st.stop()

# =============================================================
# B. ハートゼロ時のゲームオーバー ＆ 復習特訓への案内画面
# =============================================================
if not st.session_state.is_review_mode and st.session_state.hearts <= 0:
    st.error("💔 ハートがゼロになりました！")
    st.subheader(f"獲得スコア: {st.session_state.xp} XP")

    num_wrong = len(st.session_state.wrong_questions)
    if num_wrong > 0:
        st.warning(f"⚠️ 今回つまずいた問題が **{num_wrong} 問** あります。")
        st.write("そのまま再挑戦することはできません。間違えた問題をすべて解き直して克服するとハートが全回復します！")

        if st.button("🔥 間違えた問題の復習特訓を始める", use_container_width=True, key="start_review_btn"):
            st.session_state.is_review_mode = True
            st.session_state.review_queue = list(st.session_state.wrong_questions)
            random.shuffle(st.session_state.review_queue)
            next_question()
            st.rerun()
    else:
        if st.button("🔄 ハートを満タンにして再挑戦", use_container_width=True, key="safe_reset_btn"):
            st.session_state.hearts = 5
            st.session_state.streak = 0
            st.session_state.deck = []
            next_question()
            st.rerun()
    st.stop()

# =============================================================
# C. ステータスバー表示
# =============================================================
if st.session_state.is_review_mode:
    st.warning(f"🔄 **【弱点克服・復習特訓中】** 残り間違えた問題: **{len(st.session_state.review_queue)} 問**（正解するまで終わりません）")
else:
    st.info(f"📍 **設定中のモード:** 【{selected_cat}】 ｜ 難易度: **{selected_lvl}**")
    col1, col2 = st.columns(2)
    with col1:
        hearts_ui = "❤️ " * st.session_state.hearts + "🖤 " * (5 - st.session_state.hearts)
        st.write(f"**ライフ:** {hearts_ui}")
    with col2:
        st.write(f"**スコア:** ⚡ {st.session_state.xp} XP | 🔥 **連続:** {st.session_state.streak}問")

st.markdown("---")

q = st.session_state.current_q
if q is None:
    st.warning("⚠️ 選択した条件に一致する問題がありません。サイドバーの設定を変更してください。")
    st.stop()

speaker_val = q.get("speaker", "自分")
if speaker_val == "スタッフ":
    speaker_badge = "🛎️ **店員・係員が話しかけています（聞き取り特訓）**"
elif speaker_val == "看板":
    speaker_badge = "🪧 **看板・サイン表示（街中・空港の読解特訓）**"
elif speaker_val == "料理":
    speaker_badge = "🍽️ **ギリシャ名物料理・メニュー単語**"
else:
    speaker_badge = "🗣️ **旅行で使う会話フレーズ**"

st.caption(f"{speaker_badge} ｜ ジャンル: 【{q['category']}】 / 難易度: {q['level']}")

audio_bytes = get_greek_audio(q["greek"])
audio_box = st.empty()
audio_box.audio(audio_bytes, format="audio/mp3")

sentence_container = st.empty()
with sentence_container.container():
    if st.session_state.is_listening_mode:
        st.info("🎧 **リスニング特訓：** 音声を聞いて、相手が何と言っているか選んでください！")
        st.subheader("「 ❓ ❓ ❓ 」")
    else:
        st.caption("💡 **ギリシャ語の単語をタップ（またはマウスホバー）すると意味がわかります**")
        render_duo_sentence(q, st.session_state.q_count)

st.write("")

# =============================================================
# D. 解答選択肢ボタン
# =============================================================
if not st.session_state.answered:
    for i, choice in enumerate(st.session_state.choices):
        btn_key = f"choice_{st.session_state.q_count}_{i}"
        if st.button(choice, use_container_width=True, key=btn_key):
            st.session_state.answered = True
            if choice == q["meaning"]:
                st.session_state.is_correct = True
                st.session_state.xp += 10
                st.session_state.streak += 1
            else:
                st.session_state.is_correct = False
                st.session_state.streak = 0
                if not st.session_state.is_review_mode:
                    st.session_state.hearts -= 1
                    if not any(item["greek"] == q["greek"] for item in st.session_state.wrong_questions):
                        st.session_state.wrong_questions.append(q)
            st.rerun()
else:
    # =============================================================
    # E. 解答後の結果表示 ＆ 発音チェック
    # =============================================================
    if st.session_state.is_correct:
        if st.session_state.is_review_mode:
            st.success("🎉 正解！ この問題を克服しました！")
        else:
            st.success("🎉 正解！ +10 XP")
    else:
        if st.session_state.is_review_mode:
            st.error(f"💔 不正解... 正解は: **{q['meaning']}**（もう一度あとで出題されます）")
        else:
            st.error(f"💔 不正解... 正解は: **{q['meaning']}**")

    if speaker_val == "スタッフ":
        speaker_title = "店員・相手の発言"
    elif speaker_val == "看板":
        speaker_title = "看板・標識"
    elif speaker_val == "料理":
        speaker_title = "名物料理・単語"
    else:
        speaker_title = "フレーズ"

    st.markdown(f"""
    > **🇬🇷 ギリシャ文字:** {q['greek']}  
    > **🗣️ カタカナ発音:** **{q['reading']}**  
    > **🇯🇵 日本語の意味:** **{q['meaning']}**（{speaker_title}）
    """)

    dish_info = q.get("dish_info")
    if dish_info:
        st.markdown(f"""
        <div class="dish-card">
          💡 <strong>どんな料理・文化？（グルメ解説）:</strong><br>{dish_info}
        </div>
        """, unsafe_allow_html=True)

    # -------------------------------------------------------------
    # 🎤 発音チェック機能（特大正円ボタン）
    # -------------------------------------------------------------
    with st.expander("🎤 声に出して発音テストに挑戦！（通じる度判定）", expanded=False):
        if not SPEECH_REC_AVAILABLE:
            st.warning("⚠️ 発音チェック機能を使うには、PCのコマンドプロンプトで `pip install SpeechRecognition` を実行してください。")
        else:
            st.info(f"🗣️ **お手本発音:** **「 {q['reading']} 」**")
            st.caption("👇 **大きな丸いマイクを押して録音開始 ➔ 言い終わったらもう一度押して停止**")
            
            audio_recorded = st.audio_input("マイク録音", key=f"rec_{st.session_state.q_count}", label_visibility="collapsed")

            if audio_recorded is not None:
                with st.spinner("AIがギリシャ人の耳で聞き取り中..."):
                    recognized_text, result = evaluate_pronunciation(audio_recorded, q["greek"])

                if recognized_text:
                    heard_kana = greek_to_katakana(recognized_text)
                    
                    st.markdown("---")
                    st.write(f"👂 **AIが聞き取ったギリシャ語:** 「 **{recognized_text}** 」")
                    
                    st.markdown(
                        f"""
                        <div style="background-color: #f8fafc; border-left: 4px solid #0284c7; padding: 10px 14px; border-radius: 8px; margin: 12px 0;">
                            <div style="font-size: 0.95rem; color: #475569; font-weight: bold; margin-bottom: 4px;">🇬🇷 ギリシャの人にはこう聞こえています：</div>
                            <div style="font-size: 1.35rem; color: #0284c7; font-weight: bold;">👉 「 {heard_kana} 」</div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                    norm_rec = normalize_greek(recognized_text)
                    norm_target = normalize_greek(q["greek"])
                    accidental_match = None
                    if norm_rec != norm_target:
                        for item in DATASET:
                            if normalize_greek(item["greek"]) == norm_rec and item["meaning"] != q["meaning"]:
                                accidental_match = item
                                break

                    if accidental_match:
                        st.warning(f"⚠️ **注意:** 今の発音だと「**{accidental_match['meaning']}**」と勘違いされてしまう可能性があります！")

                    if result >= 80:
                        st.success(f"🌟 **判定: {result}%！ 完璧です！** 現地の人にもバッチリ正確に伝わっています！")
                    elif result >= 55:
                        st.info(f"👍 **判定: {result}%！ おおむね通じます！** 「{heard_kana}」と伝わりますが、もう少し「{q['reading']}」の強弱を意識すると満点です！")
                    else:
                        st.warning(f"💪 **判定: {result}%！ 惜しい！** 現地の人には「{heard_kana}」と聞こえているため、上の音声をもう一度聴いて再チャレンジしてみましょう！")

                elif result == "UNKNOWN_VALUE":
                    st.error("⚠️ 音声を聞き取れませんでした。マイクに少し近づいて、もう一度ゆっくり発音してください。")
                else:
                    st.error("⚠️ 音声認識でエラーが発生しました。通信環境を確認してください。")

    breakdown_list = q.get("breakdown", [])
    if breakdown_list:
        with st.expander("🔍 単語・パーツごとの詳しい解説を見る"):
            for item in breakdown_list:
                st.write(f"- **{item['word']}** : {item['meaning']}")

    next_btn_label = "次の復習問題へ進む ➔" if st.session_state.is_review_mode else "次の問題へ進む ➔"
    if st.button(next_btn_label, use_container_width=True, key=f"next_btn_{st.session_state.q_count}"):
        if st.session_state.is_review_mode:
            if st.session_state.is_correct:
                st.session_state.review_queue.pop(0)
            else:
                retry_item = st.session_state.review_queue.pop(0)
                st.session_state.review_queue.append(retry_item)

        next_question()
        st.rerun()
