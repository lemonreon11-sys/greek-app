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
# 2. 旅行フレーズ・グルメ・看板データベース（超充実版）
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
        "breakdown": [
            {"word": "Καλημέρα", "meaning": "良い朝（おはよう）"}
        ]
    },
    {
        "greek": "Καλησπέρα",
        "reading": "カリスペラ",
        "meaning": "こんばんは（午後・夕方以降の挨拶）",
        "category": "基本挨拶",
        "level": "初級",
        "speaker": "自分",
        "breakdown": [
            {"word": "Καλησπέρα", "meaning": "良い夕暮れ（こんばんは）"}
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
        "greek": "Τσάι",
        "reading": "チャイ",
        "meaning": "お茶 / ハーブティー（単語）",
        "category": "カフェ",
        "level": "初級",
        "speaker": "料理",
        "breakdown": [{"word": "Τσάι", "meaning": "お茶 / 紅茶"}],
        "dish_info": "ギリシャでは山の自生ハーブを使った「山のお茶（ツァイ・トゥ・ヴヌー）」が健康茶として大人気です。"
    },
    {
        "greek": "Χυμός πορτοκάλι",
        "reading": "ヒモス ポルトカリ",
        "meaning": "生搾りオレンジジュース（定番ドリンク）",
        "category": "カフェ",
        "level": "初級",
        "speaker": "料理",
        "breakdown": [
            {"word": "Χυμός", "meaning": "ジュース"},
            {"word": "πορτοκάλι", "meaning": "オレンジ"}
        ],
        "dish_info": "ギリシャはオレンジの産地のため、どのカフェでも注文が入ってから生搾りする濃厚で甘いオレンジジュースが格安で飲めます。"
    },
    {
        "greek": "Μπύρα",
        "reading": "ビラ",
        "meaning": "ビール（単語）",
        "category": "カフェ",
        "level": "初級",
        "speaker": "料理",
        "breakdown": [{"word": "Μπύρα", "meaning": "ビール"}],
        "dish_info": "ギリシャ定番ビールは「Mythos（ミソス）」や「Alfa（アルファ）」。すっきり軽い飲み口で地中海気候にぴったりです。"
    },
    {
        "greek": "Κρασί",
        "reading": "クラシ",
        "meaning": "ワイン（単語）",
        "category": "カフェ",
        "level": "初級",
        "speaker": "料理",
        "breakdown": [{"word": "Κρασί", "meaning": "ワイン"}]
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
        ],
        "dish_info": "エスプレッソを氷と一緒にミキサーで急冷したギリシャ若者の圧倒的1番人気ドリンクです。"
    },
    {
        "greek": "Έναν φρέντο καπουτσίノ, παρακαλώ.",
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
        ],
        "dish_info": "冷たいアイスエスプレッソの上に、冷たいクリーミーなミルクフォームをふんわり乗せた贅沢なアイスカプチーノです。"
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
        ],
        "dish_info": "ギリシャでは注文時に砂糖を伝えます（無糖＝スケト、微糖＝メトリオ、甘口＝グリコ）。"
    },

    # === レストラン・名物料理（メニュー読解・解説完備） ===
    {
        "greek": "Μουσακάς",
        "reading": "ムサカス",
        "meaning": "ムサカ（ナス・ポテト・ひき肉の重ね焼き）",
        "category": "レストラン・名物料理",
        "level": "初級",
        "speaker": "料理",
        "breakdown": [{"word": "Μουσακάς", "meaning": "ムサカ（ギリシャ代表料理）"}],
        "dish_info": "【ギリシャの国民食】素揚げしたナスとジャガイモ、シナモン等のスパイスを効かせた牛・羊のひき肉を層にし、濃厚なベシャメルソースを乗せてオーブンで焼き上げた伝統料理です。"
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
        "dish_info": "【必食の庶民派グルメ】大きな回転串で炙り焼きにした肉を薄く削ぎ落とし、トマト、玉ねぎ、フライドポテト、ザジキと一緒にピタパンでくるんだ手軽で絶品のサンドイッチです。"
    },
    {
        "greek": "Χωριάτικη",
        "reading": "ホリアティキ",
        "meaning": "グリークサラダ（フェタチーズ丸ごと乗せ田舎風サラダ）",
        "category": "レストラン・名物料理",
        "level": "初級",
        "speaker": "料理",
        "breakdown": [{"word": "Χωριάτικη", "meaning": "田舎風サラダ（グリークサラダ）"}],
        "dish_info": "【タヴェルナの必需品】完熟トマト、きゅうり、赤玉ねぎ、黒オリーブの上に、分厚いフェタチーズがドカンと1枚乗り、オリーブオイルとオレガノがたっぷりかかっています。"
    },
    {
        "greek": "Τζατζίκι",
        "reading": "ザジキ",
        "meaning": "ザジキ（ヨーグルトときゅうりとにんにくの万能ディップ）",
        "category": "レストラン・名物料理",
        "level": "初級",
        "speaker": "料理",
        "breakdown": [{"word": "Τζατζίκι", "meaning": "ザジキ（ヨーグルトディップ）"}],
        "dish_info": "【ギリシャ料理の相棒】濃厚なギリシャヨーグルトにすりおろしたキュウリ、にんにく、オリーブオイル、ディルを混ぜたさっぱりディップ。パンやお肉につけて食べます。"
    },
    {
        "greek": "Σαγανάκι",
        "reading": "サガナキ",
        "meaning": "サガナキ（表面をカリッと焼いたとろける熱々チーズ）",
        "category": "レストラン・名物料理",
        "level": "初級",
        "speaker": "料理",
        "breakdown": [{"word": "Σαγανάκι", "meaning": "サガナキ（焼きチーズ）"}],
        "dish_info": "【お酒のおつまみNo.1】羊や山羊のハードチーズに小麦粉をまぶし、小鍋（サガニ）で表面がきつね色になるまでカリッと焼き上げたもの。熱々にレモンを絞っていただきます。"
    },
    {
        "greek": "Παστίτσιο",
        "reading": "パスティツィオ",
        "meaning": "パスティツィオ（筒状パスタとミートソースのギリシャ風グラタン）",
        "category": "レストラン・名物料理",
        "level": "初級",
        "speaker": "料理",
        "breakdown": [{"word": "Παστίτσιο", "meaning": "パスティツィオ（パスタグラタン）"}],
        "dish_info": "【家庭料理の王様】太い穴あきパスタの上にスパイスが香るミートソース、一番上に分厚いベシャメルソースを重ねて焼き上げた、ギリシャ版ラザニアのような大満足メニューです。"
    },
    {
        "greek": "Ταραμοσαλάτα",
        "reading": "タラモサラタ",
        "meaning": "タラモサラタ（魚卵とオリーブオイルのなめらかペースト）",
        "category": "レストラン・名物料理",
        "level": "初級",
        "speaker": "料理",
        "breakdown": [{"word": "Ταραμοσαλάτα", "meaning": "タラモサラタ（魚卵ペースト）"}],
        "dish_info": "【日本のタラモサラダの元祖】ボラの卵などの塩漬け魚卵を、水で戻したパン（またはジャガイモ）、レモン汁、オリーブオイルと練り上げた、パンが進むクリーミーな前菜です。"
    },
    {
        "greek": "Ντολμαδάκια",
        "reading": "ドルマダキア",
        "meaning": "ドルマデス（お米とハーブをブドウの葉で包んだ伝統前菜）",
        "category": "レストラン・名物料理",
        "level": "初級",
        "speaker": "料理",
        "breakdown": [{"word": "Ντολμαδάκια", "meaning": "ブドウの葉包みご飯"}],
        "dish_info": "【地中海の伝統フィンガーフード】お米、玉ねぎ、ミントやディルなどのハーブを柔らかいブドウの葉で一口サイズにきっちり巻き、オリーブオイルとレモンで煮込んだ料理です。"
    },
    {
        "greek": "Καλαμαράκια",
        "reading": "カラマラキア",
        "meaning": "カラマラキア（小イカのサクサクフライ/フリット）",
        "category": "レストラン・名物料理",
        "level": "初級",
        "speaker": "料理",
        "breakdown": [{"word": "Καλαμαράκια", "meaning": "イカのフライ"}],
        "dish_info": "【港町・島タヴェルナの定番】小イカに薄く粉をはたいてオリーブオイルでサッと揚げたもの。衣がサクサクで身は柔らかく、冷えた白ワインやビールと最高に合います。"
    },
    {
        "greek": "Χταπόδι",
        "reading": "フタポディ",
        "meaning": "タコ / 焼きタコ（ギリシャの海鮮名物）",
        "category": "レストラン・名物料理",
        "level": "初級",
        "speaker": "料理",
        "breakdown": [{"word": "Χταπόδι", "meaning": "タコ"}],
        "dish_info": "【海辺のレストラン名物】店の軒先に吊るして天日干ししたタコを炭火で香ばしくグリルしたもの、または赤ワインと酢で柔らかく煮込んだ酢漬け（クシザト）が有名です。"
    },
    {
        "greek": "Σπανακόπιτα",
        "reading": "スパナコピタ",
        "meaning": "スパナコピタ（ほうれん草とフェタチーズのサクサクパイ）",
        "category": "レストラン・名物料理",
        "level": "初級",
        "speaker": "料理",
        "breakdown": [{"word": "Σπανακόπιτα", "meaning": "ほうれん草のパイ"}],
        "dish_info": "【朝食やおやつの定番】極薄のフィロパイ生地の間に、ほうれん草、フェタチーズ、ハーブを挟んで黄金色に焼き上げたパイ。ベーカリーで熱々を買って歩き食べできます。"
    },
    {
        "greek": "Λουκουμάδες",
        "reading": "ルクマデス",
        "meaning": "ルクマデス（揚げたてモチモチのギリシャ風蜂蜜ドーナツ）",
        "category": "レストラン・名物料理",
        "level": "初級",
        "speaker": "料理",
        "breakdown": [{"word": "Λουκουμάδες", "meaning": "ギリシャ風ドーナツ"}],
        "dish_info": "【古代から伝わる国民的スイーツ】丸く揚げたひとくちドーナツに、たっぷりの温かいハチミツとシナモン、刻みクルミをかけて食べるサクサク・モチモチの絶品デザートです。"
    },
    {
        "greek": "Μπακλαβάς",
        "reading": "バクラヴァス",
        "meaning": "バクラヴァ（パイ生地とナッツの濃厚シロップ菓子）",
        "category": "レストラン・名物料理",
        "level": "初級",
        "speaker": "料理",
        "breakdown": [{"word": "Μπακλαβάς", "meaning": "バクラヴァ"}],
        "dish_info": "何層にも重ねた薄いパイ生地の間に刻んだピスタチオやクルミをたっぷり挟み、焼き上がりに甘いシロップを染み込ませた伝統的な濃厚パイ菓子です。"
    },
    {
        "greek": "Ούζο",
        "reading": "ウーゾ",
        "meaning": "ウーゾ（水を注ぐと白濁するアニス風味の伝統蒸留酒）",
        "category": "レストラン・名物料理",
        "level": "初級",
        "speaker": "料理",
        "breakdown": [{"word": "Ούζο", "meaning": "ウーゾ（伝統酒）"}],
        "dish_info": "【ギリシャを象徴するお酒】薬草アニスが香る透明なお酒ですが、水や氷を入れると化学反応で乳白色に変化します。小皿料理（メゼ）をつまみながらチビチビ飲みます。"
    },
    {
        "greek": "Ρετσίνα",
        "reading": "レッチーナ",
        "meaning": "レッチーナ（松脂の独特なアロマが香る伝統白ワイン）",
        "category": "レストラン・名物料理",
        "level": "初級",
        "speaker": "料理",
        "breakdown": [{"word": "Ρετσίνα", "meaning": "松脂ワイン"}],
        "dish_info": "古代ギリシャでワイン樽を密閉するために松脂を使ったことから生まれた名物白ワイン。独特のスッキリした松の香りが脂っこい肉や魚料理と絶妙にマッチします。"
    },
    {
        "greek": "Ψωμί",
        "reading": "プソミ",
        "meaning": "パン（食事用パン・単語）",
        "category": "レストラン・名物料理",
        "level": "初級",
        "speaker": "料理",
        "breakdown": [{"word": "Ψωμί", "meaning": "パン"}],
        "dish_info": "レストランに座ると必ずカゴに入って出てきます。残ったサラダのオリーブオイルやお肉のソースをパンで拭って食べるのがギリシャ流の美味しさです。"
    },
    {
        "greek": "Ψάρι",
        "reading": "プサリ",
        "meaning": "魚 / 魚料理（単語）",
        "category": "レストラン・名物料理",
        "level": "初級",
        "speaker": "料理",
        "breakdown": [{"word": "Ψάρι", "meaning": "魚"}]
    },
    {
        "greek": "Κρέας",
        "reading": "クレアス",
        "meaning": "お肉 / 肉料理（単語）",
        "category": "レストラン・名物料理",
        "level": "初級",
        "speaker": "料理",
        "breakdown": [{"word": "Κρέας", "meaning": "お肉"}]
    },
    {
        "greek": "Ελιές",
        "reading": "エリエス",
        "meaning": "オリーブの実（単語）",
        "category": "レストラン・名物料理",
        "level": "初級",
        "speaker": "料理",
        "breakdown": [{"word": "Ελιές", "meaning": "オリーブ"}],
        "dish_info": "ギリシャのオリーブ（特に紫黒色のカラマタオリーブ）は肉厚でジューシー。おつまみやサラダに欠かせません。"
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
        "greek": "Όλα ήταν καλά;",
        "reading": "オラ イタン カラ？",
        "meaning": "お料理（お味）はいかがでしたか？",
        "category": "レストラン・名物料理",
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

    # === 街の看板・標識（読解特訓） ===
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
    {
        "greek": "ΕΚΠΤΩΣΕΙΣ",
        "reading": "エクプトシス",
        "meaning": "セール / 割引中 / SALE（売店の張り紙）",
        "category": "街の看板・標識",
        "level": "初級",
        "speaker": "看板",
        "breakdown": [{"word": "ΕΚΠΤΩΣΕΙΣ", "meaning": "セール / 値引き"}]
    },
    {
        "greek": "ΑΝΔΡΩΝ",
        "reading": "アンドロン",
        "meaning": "男性用（トイレの扉の標識）",
        "category": "街の看板・標識",
        "level": "初級",
        "speaker": "看板",
        "breakdown": [{"word": "ΑΝΔΡΩΝ", "meaning": "男性用（MEN）"}]
    },
    {
        "greek": "ΓΥΝΑΙΚΩΝ",
        "reading": "イネコン",
        "meaning": "女性用（トイレの扉の標識）",
        "category": "街の看板・標識",
        "level": "初級",
        "speaker": "看板",
        "breakdown": [{"word": "ΓΥΝΑΙΚΩΝ", "meaning": "女性用（WOMEN）"}]
    },
    {
        "greek": "ΦΑΡΜΑΚΕΙΟ",
        "reading": "ファルマキオ",
        "meaning": "薬局（街中の緑色の十字マーク看板）",
        "category": "街の看板・標識",
        "level": "初級",
        "speaker": "看板",
        "breakdown": [{"word": "ΦΑΡΜΑΚΕΙΟ", "meaning": "薬局（PHARMACY）"}]
    },
    {
        "greek": "ΣΤΑΣΗ",
        "reading": "スタスィ",
        "meaning": "停留所 / バス停（道路脇の標識）",
        "category": "街の看板・標識",
        "level": "初級",
        "speaker": "看板",
        "breakdown": [{"word": "ΣΤΑΣΗ", "meaning": "停留所（BUS STOP）"}]
    },
    {
        "greek": "ΠΙΑΤΣΑ ΤΑΞΙ",
        "reading": "ピアツァ タクシ",
        "meaning": "タクシー乗り場（広場や駅前の標識）",
        "category": "街の看板・標識",
        "level": "初級",
        "speaker": "看板",
        "breakdown": [
            {"word": "ΠΙΑΤΣΑ", "meaning": "乗り場 / 広場"},
            {"word": "ΤΑΞΙ", "meaning": "タクシー"}
        ]
    },
    {
        "greek": "ΜΗ ΚΑΠΝΙΖΕΤΕ",
        "reading": "ミ カプニゼテ",
        "meaning": "禁煙（店内や公共スペースの掲示）",
        "category": "街の看板・標識",
        "level": "初級",
        "speaker": "看板",
        "breakdown": [{"word": "ΜΗ ΚΑΠΝΙΖΕΤΕ", "meaning": "タバコは吸わないでください（禁煙）"}]
    },
    {
        "greek": "ΔΩΡΕΑΝ WI-FI",
        "reading": "ドレアン ワイファイ",
        "meaning": "無料Wi-Fiあり（カフェ等の窓のステッカー）",
        "category": "街の看板・標識",
        "level": "初級",
        "speaker": "看板",
        "breakdown": [
            {"word": "ΔΩΡΕΑΝ", "meaning": "無料の"},
            {"word": "WI-FI", "meaning": "Wi-Fi"}
        ]
    },
    {
        "greek": "ΛΙΜΑΝΙ",
        "reading": "リマニ",
        "meaning": "港 / フェリー乗り場（島への船が出る港の看板）",
        "category": "街の看板・標識",
        "level": "初級",
        "speaker": "看板",
        "breakdown": [{"word": "ΛΙΜΑΝΙ", "meaning": "港（PORT）"}]
    },
    {
        "greek": "ΠΛΗΡΟΦΟΡΙΕΣ",
        "reading": "プリロフォリエス",
        "meaning": "案内所 / インフォメーション（駅・空港の窓口）",
        "category": "街の看板・標識",
        "level": "中級",
        "speaker": "看板",
        "breakdown": [{"word": "ΠΛΗΡΟΦΟΡΙΕΣ", "meaning": "案内所（INFORMATION）"}]
    },
    {
        "greek": "ΑΠΑΓΟΡΕΥΕΤΑΙ",
        "reading": "アパゴレヴェテ",
        "meaning": "禁止 / 立ち入り禁止（警告看板）",
        "category": "街の看板・標識",
        "level": "中級",
        "speaker": "看板",
        "breakdown": [{"word": "ΑΠΑΓΟΡΕΥΕΤΑΙ", "meaning": "禁止されています（FORBIDDEN）"}]
    },

    # === タクシー・交通 ===
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
        "greek": "Εισιτήριο",
        "reading": "イシティリオ",
        "meaning": "切符 / 乗車券 / チケット（単語）",
        "category": "タクシー・交通",
        "level": "初級",
        "speaker": "自分",
        "breakdown": [{"word": "Εισιτήριο", "meaning": "切符 / チケット"}]
    },
    {
        "greek": "Λεωφορείο",
        "reading": "レオフォリオ",
        "meaning": "バス（単語）",
        "category": "タクシー・交通",
        "level": "初級",
        "speaker": "自分",
        "breakdown": [{"word": "Λεωφορείο", "meaning": "バス"}]
    },
    {
        "greek": "Μετρό",
        "reading": "メトロ",
        "meaning": "地下鉄（単語）",
        "category": "タクシー・交通",
        "level": "初級",
        "speaker": "自分",
        "breakdown": [{"word": "Μετρό", "meaning": "地下鉄"}]
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
        "greek": "ΑΦΙΞΕΙΣ",
        "reading": "アフィクシス",
        "meaning": "到着ロビー / 到着（空港の電光掲示看板）",
        "category": "空港・飛行機",
        "level": "初級",
        "speaker": "看板",
        "breakdown": [{"word": "ΑΦΙΞΕΙΣ", "meaning": "到着（ARRIVALS）"}]
    },
    {
        "greek": "ΑΝΑΧΩΡΗΣΕΙΣ",
        "reading": "アナホリシス",
        "meaning": "出発ロビー / 出発（空港の電光掲示看板）",
        "category": "空港・飛行機",
        "level": "初級",
        "speaker": "看板",
        "breakdown": [{"word": "ΑΝΑΧΩΡΗΣΕΙΣ", "meaning": "出発（DEPARTURES）"}]
    },
    {
        "greek": "ΑΠΟΣΚΕΥΕΣ",
        "reading": "アポスケヴェス",
        "meaning": "手荷物受取所（バゲッジクレーム看板）",
        "category": "空港・飛行機",
        "level": "初級",
        "speaker": "看板",
        "breakdown": [{"word": "ΑΠΟΣΚΕΥΕΣ", "meaning": "手荷物（BAGGAGE）"}]
    },
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

    # === ホテル・宿泊 ===
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
        "greek": "Δωμάτιο",
        "reading": "ドマティオ",
        "meaning": "部屋 / ルーム（単語）",
        "category": "ホテル",
        "level": "初級",
        "speaker": "自分",
        "breakdown": [{"word": "Δωμάτιο", "meaning": "部屋"}]
    },
    {
        "greek": "Ασανσέρ",
        "reading": "アサンセル",
        "meaning": "エレベーター（単語）",
        "category": "ホテル",
        "level": "初級",
        "speaker": "看板",
        "breakdown": [{"word": "Ασανσέρ", "meaning": "エレベーター"}]
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
    "レストラン・名物料理",
    "街の看板・標識",
    "タクシー・交通",
    "空港・飛行機",
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

    if target["category"] == "街の看板・標識":
        st.session_state.is_listening_mode = False
    else:
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

# 役割・属性ごとのDuolingo風バッジ
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

# 音声再生
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

    if speaker_val == "スタッフ":
        speaker_title = "店員・相手の発言"
    elif speaker_val == "看板":
        speaker_title = "看板・標識"
    elif speaker_val == "料理":
        speaker_title = "名物料理・単語"
    else:
        speaker_title = "フレーズ"

    # 【指定の3行フォーマットは完全維持】
    st.markdown(f"""
    > **🇬🇷 ギリシャ文字:** {q['greek']}  
    > **🗣️ カタカナ発音:** **{q['reading']}**  
    > **🇯🇵 日本語の意味:** **{q['meaning']}**（{speaker_title}）
    """)

    # 【追加：料理や文化の詳しい解説カード】
    dish_info = q.get("dish_info")
    if dish_info:
        st.markdown(f"""
        <div class="dish-card">
          💡 <strong>どんな料理・文化？（グルメ解説）:</strong><br>{dish_info}
        </div>
        """, unsafe_allow_html=True)

    breakdown_list = q.get("breakdown", [])
    if breakdown_list:
        with st.expander("🔍 単語・パーツごとの詳しい解説を見る"):
            for item in breakdown_list:
                st.write(f"- **{item['word']}** : {item['meaning']}")

    if st.button("次の問題へ進む ➔", use_container_width=True, key=f"next_btn_{st.session_state.q_count}"):
        next_question()
        st.rerun()
