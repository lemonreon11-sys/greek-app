import io
import random
import sys
import streamlit as st
from gtts import gTTS

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

# 安全なCSSによる自動翻訳防止 ＆ 単語ポップアップデザイン
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
# 2. 旅行フレーズデータベース（全9ジャンル）
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

    # === カフェ ===
    {
        "greek": "Ένα νερό, παρακαλώ.",
        "reading": "エナ ネロ, パラカロ",
        "meaning": "お水を1つお願いします",
        "category": "カフェ",
        "level": "初級",
        "speaker": "自分",
        "breakdown": [
            {"word": "Ένα", "meaning": "1つの"},
            {"word": "νερό,", "meaning": "水"},
            {"word": "παρακαλώ.", "meaning": "お願いします"}
        ]
    },
    {
        "greek": "Έναν καφέ, παρακαλώ.",
        "reading": "エナン カフェ, パラカロ",
        "meaning": "温かいコーヒーを1つお願いします",
        "category": "カフェ",
        "level": "初級",
        "speaker": "自分",
        "breakdown": [
            {"word": "Έναν", "meaning": "1つの"},
            {"word": "καφέ,", "meaning": "コーヒー"},
            {"word": "παρακαλώ.", "meaning": "お願いします"}
        ]
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
    {
        "greek": "Κάτι άλλο για εσάς;",
        "reading": "カティ アロ ヤ エサス？",
        "meaning": "他にご注文はよろしいですか？",
        "category": "カフェ",
        "level": "上級",
        "speaker": "スタッフ",
        "breakdown": [
            {"word": "Κάτι", "meaning": "何か"},
            {"word": "άλλο", "meaning": "他に"},
            {"word": "για", "meaning": "〜のために"},
            {"word": "εσάς;", "meaning": "あなたに"}
        ]
    },

    # === タクシー・交通 ===
    {
        "greek": "Ταξί!",
        "reading": "タクシ！",
        "meaning": "タクシー！",
        "category": "タクシー・交通",
        "level": "初級",
        "speaker": "自分",
        "breakdown": [
            {"word": "Ταξί!", "meaning": "タクシー！"}
        ]
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
        "greek": "Στο ξενοδοχείο, παρακαλώ.",
        "reading": "スト クセノドヒオ, パラカロ",
        "meaning": "ホテルまでお願いします",
        "category": "タクシー・交通",
        "level": "中級",
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
        "level": "中級",
        "speaker": "自分",
        "breakdown": [
            {"word": "Σταματήστε", "meaning": "止めてください"},
            {"word": "εδώ,", "meaning": "ここで"},
            {"word": "παρακαλώ.", "meaning": "お願いします"}
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
        "greek": "Έχετε βαλίτσες για το πορτμπαγκάζ;",
        "reading": "エヘテ ヴァリツェス ヤ ト ポルトバンガズ？",
        "meaning": "トランクに入れるお荷物はありますか？",
        "category": "タクシー・交通",
        "level": "上級",
        "speaker": "スタッフ",
        "breakdown": [
            {"word": "Έχετε", "meaning": "ありますか"},
            {"word": "βαλίτσες", "meaning": "スーツケース/荷物"},
            {"word": "για το", "meaning": "〜用の"},
            {"word": "πορτμπαγκάζ;", "meaning": "トランク"}
        ]
    },
    {
        "greek": "Μόνο μετρητά, παρακαλώ.",
        "reading": "モノ メトリタ, パラカロ",
        "meaning": "現金のみのお支払いになります",
        "category": "タクシー・交通",
        "level": "上級",
        "speaker": "スタッフ",
        "breakdown": [
            {"word": "Μόνο", "meaning": "〜だけ（のみ）"},
            {"word": "μετρητά,", "meaning": "現金"},
            {"word": "παρακαλώ.", "meaning": "お願いします"}
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

    # === 空港・飛行機 ===
    {
        "greek": "Διαβατήριο",
        "reading": "ディヴァティリオ",
        "meaning": "パスポート",
        "category": "空港・飛行機",
        "level": "初級",
        "speaker": "自分",
        "breakdown": [
            {"word": "Διαβατήριο", "meaning": "パスポート"}
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
        "greek": "Έχετε υγρά στη χειραποσκευή σας;",
        "reading": "エヘテ イグラ スティ ヒラポスケヴィ サス？",
        "meaning": "手荷物に液体物は入っていますか？",
        "category": "空港・飛行機",
        "level": "上級",
        "speaker": "スタッフ",
        "breakdown": [
            {"word": "Έχετε", "meaning": "ありますか"},
            {"word": "υγρά", "meaning": "液体物"},
            {"word": "στη χειραποσκευή", "meaning": "手荷物に"},
            {"word": "σας;", "meaning": "あなたの"}
        ]
    },

    # === レストラン・食事 ===
    {
        "greek": "Τον κατάλογο, παρακαλώ.",
        "reading": "トン カタロゴ, パラカロ",
        "meaning": "メニューを見せてください",
        "category": "レストラン",
        "level": "初級",
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
        "category": "レストラン",
        "level": "初級",
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
        "category": "レストラン",
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
        "greek": "Όλα ήταν καλά;",
        "reading": "オラ イタン カラ？",
        "meaning": "お料理（お味）はいかがでしたか？",
        "category": "レストラン",
        "level": "上級",
        "speaker": "スタッフ",
        "breakdown": [
            {"word": "Όλα", "meaning": "すべて"},
            {"word": "ήταν", "meaning": "〜でしたか"},
            {"word": "καλά;", "meaning": "良かった / 美味しかった"}
        ]
    },
    {
        "greek": "Πληρώνετε μαζί ή χωριστά;",
        "reading": "プリロネテ マズィ イ ホリスタ？",
        "meaning": "お会計はご一緒ですか、別々ですか？",
        "category": "レストラン",
        "level": "上級",
        "speaker": "スタッフ",
        "breakdown": [
            {"word": "Πληρώνετε", "meaning": "支払いますか"},
            {"word": "μαζί", "meaning": "一緒に"},
            {"word": "ή", "meaning": "それとも"},
            {"word": "χωριστά;", "meaning": "別々に（割り勘）"}
        ]
    },
    {
        "greek": "Είναι πολύ νόστιμο!",
        "reading": "イネ ポリ ノスティモ！",
        "meaning": "とても美味しいです！",
        "category": "レストラン",
        "level": "中級",
        "speaker": "自分",
        "breakdown": [
            {"word": "Είναι", "meaning": "〜です"},
            {"word": "πολύ", "meaning": "とても"},
            {"word": "νόστιμο!", "meaning": "美味しい"}
        ]
    },

    # === ホテル・宿泊 ===
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
        "level": "中級",
        "speaker": "自分",
        "breakdown": [
            {"word": "Έχω κάνει", "meaning": "しました"},
            {"word": "κράτηση.", "meaning": "予約を"}
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

    # === 売店・スーパー・買い物 ===
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
        "greek": "Έχετε ψιλά;",
        "reading": "エヘテ プシラ？",
        "meaning": "細かい小銭はお持ちですか？",
        "category": "売店・買い物",
        "level": "上級",
        "speaker": "スタッフ",
        "breakdown": [
            {"word": "Έχετε", "meaning": "お持ちですか"},
            {"word": "ψιλά;", "meaning": "細かい小銭"}
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
        "greek": "Πού είναι το ΑΤΜ;",
        "reading": "プ イネ ト アテエミ？",
        "meaning": "ATMはどこにありますか？",
        "category": "施設・道案内",
        "level": "初級",
        "speaker": "自分",
        "breakdown": [
            {"word": "Πού", "meaning": "どこ"},
            {"word": "είναι", "meaning": "ありますか"},
            {"word": "το ΑΤΜ;", "meaning": "ATM"}
        ]
    },
    {
        "greek": "Πού είναι το φαρμακείο;",
        "reading": "プ イネ ト ファルマキオ？",
        "meaning": "薬局はどこですか？",
        "category": "施設・道案内",
        "level": "中級",
        "speaker": "自分",
        "breakdown": [
            {"word": "Πού", "meaning": "どこ"},
            {"word": "είναι", "meaning": "ありますか"},
            {"word": "το φαρμακείο;", "meaning": "薬局"}
        ]
    },
    {
        "greek": "Είναι κοντά ή μακριά;",
        "reading": "イネ コンタ イ マクリア？",
        "meaning": "近いですか、それとも遠いですか？",
        "category": "施設・道案内",
        "level": "中級",
        "speaker": "自分",
        "breakdown": [
            {"word": "Είναι", "meaning": "〜ですか"},
            {"word": "κοντά", "meaning": "近い"},
            {"word": "ή", "meaning": "それとも"},
            {"word": "μακριά;", "meaning": "遠い"}
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
    {
        "greek": "Είναι κλειστό σήμερα.",
        "reading": "イネ クリスト シメラ",
        "meaning": "今日は閉まっています（休業日・案内）",
        "category": "施設・道案内",
        "level": "上級",
        "speaker": "スタッフ",
        "breakdown": [
            {"word": "Είναι", "meaning": "〜です"},
            {"word": "κλειστό", "meaning": "閉まっている"},
            {"word": "σήμερα.", "meaning": "今日は"}
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
        "breakdown": [
            {"word": "Βοήθεια!", "meaning": "助けて！"}
        ]
    },
    {
        "greek": "Σταματήστε!",
        "reading": "スタマティステ！",
        "meaning": "やめて！ / 止まって！",
        "category": "緊急・トラブル",
        "level": "初級",
        "speaker": "自分",
        "breakdown": [
            {"word": "Σταματήστε!", "meaning": "やめて！ / 止まって！"}
        ]
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
# 3. 音声生成関数
# -------------------------------------------------------------
@st.cache_data
def get_greek_audio(text):
    tts = gTTS(text=text, lang="el")
    fp = io.BytesIO()
    tts.write_to_fp(fp)
    fp.seek(0)
    return fp.read()

# -------------------------------------------------------------
# 4. 単語タップ可能なHTML文章生成関数（毎問確実に更新）
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

# -------------------------------------------------------------
# 6. サイドバー設定
# -------------------------------------------------------------
st.sidebar.header("🎯 学習モード設定")

categories = [
    "全場面（ランダム特訓）",
    "基本挨拶",
    "カフェ",
    "タクシー・交通",
    "空港・飛行機",
    "レストラン",
    "ホテル",
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
    filter_changed = True

st.sidebar.markdown("---")
if st.sidebar.button("🔄 ゲームをリセット", use_container_width=True, key="reset_btn"):
    st.session_state.hearts = 5
    st.session_state.xp = 0
    st.session_state.streak = 0
    filter_changed = True

if st.sidebar.button("🔒 ログアウト", use_container_width=True, key="logout_btn"):
    st.session_state.authenticated = False
    st.rerun()

# -------------------------------------------------------------
# 7. 問題抽出 ＆ 紛らわしい選択肢の生成ロジック
# -------------------------------------------------------------
def get_filtered_pool():
    pool = DATASET
    if selected_cat != "全場面（ランダム特訓）":
        pool = [q for q in pool if q["category"] == selected_cat]
    if selected_lvl != "すべての難易度":
        pool = [q for q in pool if q["level"] == selected_lvl]
    return pool

def next_question():
    pool = get_filtered_pool()
    if not pool:
        st.session_state.current_q = None
        return

    candidates = [q for q in pool if q != st.session_state.current_q]
    if not candidates:
        candidates = pool
    target = random.choice(candidates)
    st.session_state.current_q = target

    st.session_state.is_listening_mode = random.random() < 0.30

    same_cat_wrong = [q["meaning"] for q in DATASET if q["category"] == target["category"] and q["meaning"] != target["meaning"]]

    if len(same_cat_wrong) >= 3:
        wrong_choices = random.sample(same_cat_wrong, 3)
    else:
        other_wrong = [q["meaning"] for q in DATASET if q["category"] != target["category"] and q["meaning"] != target["meaning"]]
        needed = 3 - len(same_cat_wrong)
        wrong_choices = same_cat_wrong + random.sample(other_wrong, min(needed, len(other_wrong)))

    choices = wrong_choices + [target["meaning"]]
    random.shuffle(choices)
    st.session_state.choices = choices
    st.session_state.answered = False
    st.session_state.q_count += 1

if filter_changed or st.session_state.current_q is None:
    next_question()

# -------------------------------------------------------------
# 8. メイン学習画面
# -------------------------------------------------------------
st.title("🇬🇷 ギリシャ語特訓アプリ")

st.info(f"📍 **設定中のモード:** 【{selected_cat}】 ｜ 難易度: **{selected_lvl}**")

if st.session_state.hearts <= 0:
    st.error("💔 ハートがゼロになりました！")
    st.subheader(f"獲得スコア: {st.session_state.xp} XP")
    if st.button("🔄 ハートを満タンにして再挑戦", use_container_width=True, key="revive_btn"):
        st.session_state.hearts = 5
        st.session_state.streak = 0
        next_question()
        st.rerun()
    st.stop()

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

speaker_badge = "🛎️ **店員・係員が話しかけています（聞き取り特訓）**" if q.get("speaker") == "スタッフ" else "🗣️ **あなたが話すフレーズ**"
st.caption(f"{speaker_badge} ｜ ジャンル: 【{q['category']}】 / 難易度: {q['level']}")

# 音声再生（st.empty()で描画することで、キャッシュを残さず毎問確実に更新）
audio_bytes = get_greek_audio(q["greek"])
audio_box = st.empty()
audio_box.audio(audio_bytes, format="audio/mp3")

# ギリシャ語文字の表示エリア
sentence_container = st.empty()
with sentence_container.container():
    if st.session_state.is_listening_mode:
        st.info("🎧 **リスニング特訓：** 音声を聞いて、相手が何と言っているか選んでください！")
        st.subheader("「 ❓ ❓ ❓ 」")
    else:
        st.caption("💡 **ギリシャ語の単語をタップ（またはマウスホバー）すると意味がわかります**")
        render_duo_sentence(q, st.session_state.q_count)

st.write("")

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
                st.session_state.hearts -= 1
                st.session_state.streak = 0
            st.rerun()
else:
    if st.session_state.is_correct:
        st.success("🎉 正解！ +10 XP")
    else:
        st.error(f"💔 不正解... 正解は: **{q['meaning']}**")

    speaker_title = "店員・相手の発言" if q.get("speaker") == "スタッフ" else "フレーズ"
    st.markdown(f"""
    > **🇬🇷 ギリシャ文字:** {q['greek']}  
    > **🗣️ カタカナ発音:** **{q['reading']}**  
    > **🇯🇵 日本語の意味:** **{q['meaning']}**（{speaker_title}）
    """)

    breakdown_list = q.get("breakdown", [])
    if breakdown_list:
        with st.expander("🔍 単語・パーツごとの詳しい解説を見る"):
            for item in breakdown_list:
                st.write(f"- **{item['word']}** : {item['meaning']}")

    if st.button("次の問題へ進む ➔", use_container_width=True, key=f"next_btn_{st.session_state.q_count}"):
        next_question()
        st.rerun()
