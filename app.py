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
# 好きなパスワードに変更してください
SECRET_PASSWORD = "0731"

st.set_page_config(page_title="ギリシャ語Duo道場", page_icon="🇬🇷", layout="centered")

# ログイン状態の管理
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# パスワード未入力時のログイン画面
if not st.session_state.authenticated:
    st.title("🔒 ギリシャ語アプリ（保護中）")
    st.write("このアプリはパスワードで保護されています。合言葉を入力してください。")

    pwd_input = st.text_input("パスワード", type="password")

    if st.button("ログインして始める", use_container_width=True):
        if pwd_input == SECRET_PASSWORD:
            st.session_state.authenticated = True
            st.success("認証に成功しました！")
            st.rerun()
        else:
            st.error("パスワードが正しくありません。")

    # パスワードが通るまで、これ以降のコード（ゲーム画面）を一切読み込ませない
    st.stop()

# -------------------------------------------------------------
# 2. 旅行フレーズデータベース（全8場面 × 初・中・上級）
# -------------------------------------------------------------
DATASET = [
    # === 基本挨拶・日常会話 ===
    {
        "greek": "Γεια σας",
        "reading": "ヤ サス",
        "meaning": "こんにちは / さようなら（丁寧）",
        "category": "基本挨拶",
        "level": "初級",
    },
    {
        "greek": "Ευχαριστώ",
        "reading": "エフハリスト",
        "meaning": "ありがとう",
        "category": "基本挨拶",
        "level": "初級",
    },
    {
        "greek": "Παρακαλώ",
        "reading": "パラカロ",
        "meaning": "お願いします / どういたしまして",
        "category": "基本挨拶",
        "level": "初級",
    },
    {
        "greek": "Ναι / Όχι",
        "reading": "ネ / オヒ",
        "meaning": "はい / いいえ（※ネが肯定）",
        "category": "基本挨拶",
        "level": "初級",
    },
    {
        "greek": "Συγγνώμη",
        "reading": "シグノミ",
        "meaning": "すみません / 失礼します",
        "category": "基本挨拶",
        "level": "中級",
    },
    {
        "greek": "Τι κάνετε;",
        "reading": "ティ カネテ？",
        "meaning": "お元気ですか？ / 調子はどう？",
        "category": "基本挨拶",
        "level": "中級",
    },
    {
        "greek": "Μιλάτε αγγλικά;",
        "reading": "ミラテ アングリカ？",
        "meaning": "英語は話せますか？",
        "category": "基本挨拶",
        "level": "中級",
    },
    {
        "greek": "Δεν καταλαβαίνω.",
        "reading": "デン カタラヴェノ",
        "meaning": "わかりません / 理解できません",
        "category": "基本挨拶",
        "level": "上級",
    },
    {
        "greek": "Μπορείτε να το επαναλάβετε;",
        "reading": "ボリテ ナ ト エパナラヴェテ？",
        "meaning": "もう一度言っていただけますか？",
        "category": "基本挨拶",
        "level": "上級",
    },
    # === カフェ ===
    {
        "greek": "Ένα νερό, παρακαλώ.",
        "reading": "エナ ネロ, パラカロ",
        "meaning": "お水を1つお願いします",
        "category": "カフェ",
        "level": "初級",
    },
    {
        "greek": "Έναν καφέ, παρακαλώ.",
        "reading": "エナン カフェ, パラカロ",
        "meaning": "コーヒーを1つお願いします",
        "category": "カフェ",
        "level": "初級",
    },
    {
        "greek": "Έναν φρέντο εσπρέσο, παρακαλώ.",
        "reading": "エナン フレット エスプレッソ, パラカロ",
        "meaning": "アイスエスプレッソを1杯ください（定番）",
        "category": "カフェ",
        "level": "中級",
    },
    {
        "greek": "Έναν φρέντο καπουτσίνο, παρακαλώ.",
        "reading": "エナン フレット カプチーノ, パラカロ",
        "meaning": "アイスカプチーノを1杯ください",
        "category": "カフェ",
        "level": "中級",
    },
    {
        "greek": "Για έξω, παρακαλώ.",
        "reading": "ヤ エクソ, パラカロ",
        "meaning": "テイクアウト（持ち帰り）でお願いします",
        "category": "カフェ",
        "level": "中級",
    },
    {
        "greek": "Σκέτο / Μέτριο / Γλυκό",
        "reading": "スケト / メトリオ / グリコ",
        "meaning": "無糖 / 微糖 / 甘め（コーヒーの甘さ指定）",
        "category": "カフェ",
        "level": "上級",
    },
    {
        "greek": "Μπορώ να έχω λίγο γάλα;",
        "reading": "ボロ ナ エホ リゴ ガラ？",
        "meaning": "ミルクを少しいただけますか？",
        "category": "カフェ",
        "level": "上級",
    },
    # === タクシー・交通 ===
    {
        "greek": "Ταξί!",
        "reading": "タクシ！",
        "meaning": "タクシー！",
        "category": "タクシー・交通",
        "level": "初級",
    },
    {
        "greek": "Στο αεροδρόμιο, παρακαλώ.",
        "reading": "スト アエロドロミオ, パラカロ",
        "meaning": "空港までお願いします",
        "category": "タクシー・交通",
        "level": "初級",
    },
    {
        "greek": "Στο ξενοδοχείο, παρακαλώ.",
        "reading": "スト クセノドヒオ, パラカロ",
        "meaning": "ホテルまでお願いします",
        "category": "タクシー・交通",
        "level": "中級",
    },
    {
        "greek": "Σταματήστε εδώ, παρακαλώ.",
        "reading": "スタマティステ エド, パラカロ",
        "meaning": "ここで止めてください",
        "category": "タクシー・交通",
        "level": "中級",
    },
    {
        "greek": "Πόσο κοστίζει μέχρι εκεί;",
        "reading": "ポソ コスティズィ メフリ エキ？",
        "meaning": "そこまでいくらかかりますか？",
        "category": "タクシー・交通",
        "level": "中級",
    },
    {
        "greek": "Βάλτε το ταξίμετρο, παρακαλώ.",
        "reading": "ヴァルテ ト タクシメトロ, パラカロ",
        "meaning": "メーターを回してください（ぼったくり対策）",
        "category": "タクシー・交通",
        "level": "上級",
    },
    {
        "greek": "Μπορώ να πληρώσω με κάρτα;",
        "reading": "ボロ ナ プリロソ メ カルタ？",
        "meaning": "クレジットカードで支払えますか？",
        "category": "タクシー・交通",
        "level": "上級",
    },
    # === 空港・飛行機 ===
    {
        "greek": "Διαβατήριο",
        "reading": "ディヴァティリオ",
        "meaning": "パスポート",
        "category": "空港・飛行機",
        "level": "初級",
    },
    {
        "greek": "Πού είναι η πύλη επιβίβασης;",
        "reading": "プ イネ イ ピリ エピヴィヴァシス？",
        "meaning": "搭乗ゲートはどこですか？",
        "category": "空港・飛行機",
        "level": "中級",
    },
    {
        "greek": "Αυτή είναι η αποσκευή μου.",
        "reading": "アフティ イネ イ アポスケヴィ ム",
        "meaning": "これは私の手荷物（スーツケース）です",
        "category": "空港・飛行機",
        "level": "中級",
    },
    {
        "greek": "Έχασα την πτήση μου.",
        "reading": "エハサ ティン プティスィ ム",
        "meaning": "飛行機に乗り遅れてしまいました",
        "category": "空港・飛行機",
        "level": "上級",
    },
    {
        "greek": "Δεν βρίσκω τη βαλίτσα μου.",
        "reading": "デン ヴリスコ ティ ヴァリツァ ム",
        "meaning": "預けた荷物が見当たりません（ロストバゲージ）",
        "category": "空港・飛行機",
        "level": "上級",
    },
    # === レストラン・食事 ===
    {
        "greek": "Τον κατάλογο, παρακαλώ.",
        "reading": "トン カタロゴ, パラカロ",
        "meaning": "メニューを見せてください",
        "category": "レストラン",
        "level": "初級",
    },
    {
        "greek": "Τον λογαριασμό, παρακαλώ.",
        "reading": "トン ロガリアズモ, パラカロ",
        "meaning": "お会計をお願いします",
        "category": "レストラン",
        "level": "初級",
    },
    {
        "greek": "Τι προτείνετε;",
        "reading": "ティ プロティネテ？",
        "meaning": "おすすめ料理は何ですか？",
        "category": "レストラン",
        "level": "中級",
    },
    {
        "greek": "Είναι πολύ νόστιμο!",
        "reading": "イネ ポリ ノスティモ！",
        "meaning": "とても美味しいです！",
        "category": "レストラン",
        "level": "中級",
    },
    {
        "greek": "Έχετε τραπέζι για δύο;",
        "reading": "エヘテ トラペズィ ヤ ディオ？",
        "meaning": "2人分の席は空いていますか？",
        "category": "レストラン",
        "level": "上級",
    },
    {
        "greek": "Μπορούμε να πληρώσουμε χωριστά;",
        "reading": "ボルメ ナ プリロスメ ホリスタ？",
        "meaning": "別々に会計（割り勘）できますか？",
        "category": "レストラン",
        "level": "上級",
    },
    # === ホテル・宿泊 ===
    {
        "greek": "Το κλειδί, παρακαλώ.",
        "reading": "ト クリディ, パラカロ",
        "meaning": "部屋の鍵をください",
        "category": "ホテル",
        "level": "初級",
    },
    {
        "greek": "Έχω κάνει κράτηση.",
        "reading": "エホ カニ クラティスィ",
        "meaning": "予約をしています（チェックイン時）",
        "category": "ホテル",
        "level": "中級",
    },
    {
        "greek": "Ποιος είναι ο κωδικός του Wi-Fi;",
        "reading": "ピオス イネ オ コディコス トゥ ワイファイ？",
        "meaning": "Wi-Fiのパスワードは何ですか？",
        "category": "ホテル",
        "level": "中級",
    },
    {
        "greek": "Μπορώ να αφήσω τις αποσκευές μου;",
        "reading": "ボロ ナ アフィソ ティス アポスケヴェス ム？",
        "meaning": "チェックイン前/後に荷物を預けられますか？",
        "category": "ホテル",
        "level": "上級",
    },
    {
        "greek": "Δεν έχει ζεστό νερό στο μπάνιο.",
        "reading": "デン エヒ ゼスト ネロ スト バニョ",
        "meaning": "お風呂の温かいお湯が出ません",
        "category": "ホテル",
        "level": "上級",
    },
    # === 売店・スーパー・買い物 ===
    {
        "greek": "Πόσο κάνει;",
        "reading": "ポソ カニ？",
        "meaning": "これいくらですか？",
        "category": "売店・買い物",
        "level": "初級",
    },
    {
        "greek": "Μια σακούλα, παρακαλώ.",
        "reading": "ミア サクラ, パラカロ",
        "meaning": "レジ袋を1枚ください",
        "category": "売店・買い物",
        "level": "中級",
    },
    {
        "greek": "Μπορώ να το δω αυτό;",
        "reading": "ボロ ナ ト ド アフト？",
        "meaning": "あれを見せてもらってもいいですか？",
        "category": "売店・買い物",
        "level": "中級",
    },
    {
        "greek": "Έχετε άλλο μέγεθος;",
        "reading": "エヘテ アロ メゲソス？",
        "meaning": "他のサイズはありますか？",
        "category": "売店・買い物",
        "level": "上級",
    },
    {
        "greek": "Μπορείτε να κάνετε καλύτερη τιμή;",
        "reading": "ボリテ ナ カネテ カリテリ ティミ？",
        "meaning": "少しおまけ（値引き）してもらえませんか？",
        "category": "売店・買い物",
        "level": "上級",
    },
    # === 緊急・トラブル・施設 ===
    {
        "greek": "Βοήθεια!",
        "reading": "ヴォイシィア！",
        "meaning": "助けて！",
        "category": "緊急・施設",
        "level": "初級",
    },
    {
        "greek": "Πού είναι η τουアλέτα;",
        "greek": "Πού είναι η τουαλέτα;",
        "reading": "プ イネ イ トゥアレタ？",
        "meaning": "トイレはどこにありますか？",
        "category": "緊急・施設",
        "level": "初級",
    },
    {
        "greek": "Πού είναι το φαρμακείο;",
        "reading": "プ イネ ト ファルマキオ？",
        "meaning": "薬局はどこですか？",
        "category": "緊急・施設",
        "level": "中級",
    },
    {
        "greek": "Δεν νιώθω καλά.",
        "reading": "デン ニオソ カラ",
        "meaning": "気分が悪いです / 体調がすぐれません",
        "category": "緊急・施設",
        "level": "中級",
    },
    {
        "greek": "Έχασα το πορτοφόλι μου.",
        "reading": "エハサ ト ポルトフォリ ム",
        "meaning": "財布を落として（盗まれて）しまいました",
        "category": "緊急・施設",
        "level": "上級",
    },
    {
        "greek": "Καλέστε την αστυνομία!",
        "reading": "カレステ ティン アスティノミア！",
        "meaning": "警察を呼んでください！",
        "category": "緊急・施設",
        "level": "上級",
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
# 4. 学習ステータス管理
# -------------------------------------------------------------
if "hearts" not in st.session_state:
    st.session_state.hearts = 5
if "xp" not in st.session_state:
    st.session_state.xp = 0
if "streak" not in st.session_state:
    st.session_state.streak = 0
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
# 5. サイドバー設定
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
    "緊急・施設",
]
selected_cat = st.sidebar.selectbox("どの場面を勉強しますか？", categories)

levels = ["すべての難易度", "初級", "中級", "上級"]
selected_lvl = st.sidebar.selectbox("難易度（レベル）", levels)

current_filter_key = f"{selected_cat}_{selected_lvl}"
filter_changed = False
if st.session_state.last_filter_key != current_filter_key:
    st.session_state.last_filter_key = current_filter_key
    filter_changed = True

st.sidebar.markdown("---")
if st.sidebar.button("🔄 ゲームをリセット", use_container_width=True):
    st.session_state.hearts = 5
    st.session_state.xp = 0
    st.session_state.streak = 0
    filter_changed = True

# ログアウトボタン
if st.sidebar.button("🔒 ログアウト", use_container_width=True):
    st.session_state.authenticated = False
    st.rerun()

# -------------------------------------------------------------
# 6. 問題抽出ロジック
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

    wrong_options = [q["meaning"] for q in DATASET if q["meaning"] != target["meaning"]]
    choices = random.sample(wrong_options, min(3, len(wrong_options))) + [target["meaning"]]
    random.shuffle(choices)
    st.session_state.choices = choices
    st.session_state.answered = False

if filter_changed or st.session_state.current_q is None:
    next_question()

# -------------------------------------------------------------
# 7. メイン学習画面
# -------------------------------------------------------------
st.title("🇬🇷 ギリシャ語特訓アプリ")

st.info(f"📍 **設定中のモード:** 【{selected_cat}】 ｜ 難易度: **{selected_lvl}**")

if st.session_state.hearts <= 0:
    st.error("💔 ハートがゼロになりました！")
    st.subheader(f"獲得スコア: {st.session_state.xp} XP")
    if st.button("🔄 ハートを満タンにして再挑戦", use_container_width=True):
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

audio_bytes = get_greek_audio(q["greek"])
st.audio(audio_bytes, format="audio/mp3")

if st.session_state.is_listening_mode:
    st.caption("🎧 **耳で聴く特訓！ 音声を聞いて正しい意味を選んでください**")
    st.subheader("「 ❓ ❓ ❓ 」")
else:
    st.caption(f"ジャンル: 【{q['category']}】 / 難易度: {q['level']}")
    st.subheader(f"「 {q['greek']} 」")

st.write("")

if not st.session_state.answered:
    for choice in st.session_state.choices:
        if st.button(choice, use_container_width=True):
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

    st.markdown(f"""
    > **🇬🇷 ギリシャ文字:** {q['greek']}  
    > **🗣️ カタカナ発音:** **{q['reading']}**  
    > **🇯🇵 日本語の意味:** {q['meaning']}
    """)

    if st.button("次の問題へ進む ➔", use_container_width=True):
        next_question()
        st.rerun()
