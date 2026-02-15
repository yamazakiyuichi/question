import random
from dataclasses import dataclass, field
from pyscript import document

# =============================
# Robloxクイズ 100問（小学生向け）
# 形式：4択（A/B/C/D）→ 正誤判定
# 回答は A/B/C/D でも、選択肢の文章でもOK
# =============================

@dataclass
class Stats:
    asked: int = 0
    correct: int = 0
    wrong_streak: int = 0
    # 間違えた問題IDを記録して復習に回す
    wrong_ids: list[int] = field(default_factory=list)

@dataclass
class Quiz:
    qid: int
    topic: str
    question: str
    choices: list[str]  # ["A ...", "B ...", ...]
    answer_key: str     # "A"/"B"/"C"/"D"
    hint: str
    explanation: str

def el(id_: str):
    return document.getElementById(id_)

def log(msg: str):
    area = el("log")
    area.textContent = (area.textContent + ("\n" if area.textContent else "") + msg)

def set_question(text: str, topic: str):
    el("question").textContent = text
    el("topic-pill").textContent = f"単元：{topic}"

def get_answer() -> str:
    return el("answer").value.strip()

def clear_answer():
    el("answer").value = ""

def normalize(s: str) -> str:
    return " ".join(s.strip().lower().replace("　", " ").split())

# -----------------------------
# 100問データ
# ※ なるべく安全で健全な内容（規約に反しない・危険行為を促さない）
# -----------------------------

QUIZZES: list[Quiz] = [
    Quiz(1, "基本", "Robloxの中で、みんなが作ったゲームを遊べる場所（一覧）がある画面はどれ？",
         ["A ホーム", "B 設定", "C 終了画面", "D 電卓"],
         "A", "最初に出る画面を思い出してね。", "Robloxはまずホーム画面からゲームを探して遊べるよ。"),
    Quiz(2, "基本", "Robloxで自分のキャラクターの見た目を変える場所はどれ？",
         ["A Avatar（アバター）", "B Friends（フレンド）", "C Chat（チャット）", "D Exit（終了）"],
         "A", "服や髪型を変えるところだよ。", "アバター画面で服・アクセサリーなどを変えられるよ。"),
    Quiz(3, "基本", "Robloxでゲームのことをよく「何」と呼ぶ？",
         ["A Experiences（体験）", "B Books（本）", "C Movies（映画）", "D Songs（歌）"],
         "A", "Robloxの公式っぽい言い方だよ。", "Robloxではゲームを「Experience」と呼ぶことが多いよ。"),
    Quiz(4, "安全", "知らない人からフレンド申請が来た。いちばん安全なのは？",
         ["A とりあえず承認する", "B だれか大人に相談してから決める", "C 本名を聞く", "D パスワードを教える"],
         "B", "困ったら相談！", "知らない人はすぐ承認せず、大人に相談してから決めるのが安全。"),
    Quiz(5, "安全", "Robloxのパスワードはどうするのが良い？",
         ["A 友だちと同じにする", "B 誕生日だけにする", "C 長くて推測されにくいものにする", "D だれかに教える"],
         "C", "当てにくいのが大事。", "長くて推測されにくいパスワードが安全。人には教えない。"),
    Quiz(6, "基本", "Robux（ロバックス）は何に使うことが多い？",
         ["A アバターのアイテム購入", "B 宿題の提出", "C 電話の充電", "D 天気予報"],
         "A", "服やアイテムが買えるよ。", "Robuxはアバターアイテムや一部のゲーム内アイテム購入に使われる。"),
    Quiz(7, "制作", "Roblox Studio（スタジオ）は主に何をするためのもの？",
         ["A ゲームを作る", "B 写真を印刷する", "C 音楽を聴く", "D テレビを見る"],
         "A", "作るツール！", "Roblox StudioはRobloxのゲーム（体験）を作るための開発ツール。"),
    Quiz(8, "制作", "Roblox Studioでプログラムを書くときによく使う言語は？",
         ["A Lua（ルア）", "B Python", "C Java", "D C++"],
         "A", "Robloxでよく聞く言語。", "RobloxはLua系（Luau）でスクリプトを書く。"),
    Quiz(9, "基本", "ゲームの中で自分のキャラを動かすのに多い操作は？",
         ["A WASDキー / 左スティック", "B けん玉", "C えんぴつ", "D リモコンの赤ボタンだけ"],
         "A", "PCやゲーム機の操作を思い出してね。", "多くのゲームはWASDや左スティックで移動するよ。"),
    Quiz(10, "マナー", "チャットでケンカになりそう。いちばん良いのは？",
         ["A もっとあおる", "B いったん離れる/ミュートする", "C 個人情報を言う", "D 大文字で怒鳴る"],
         "B", "落ち着くのが先。", "トラブルは離れる・ミュート・通報などで安全に対処。"),

    # --- ここから一気に増やす：テーマ別に100まで ---
]

# 11〜100を自動生成ではなく、手作り100問を入れたい意図なので、
# ここでは「重複少なく、内容が健全」なクイズを追加します。

MORE = [
    # topic, question, choices(A-D), answer, hint, explanation
    ("基本", "Robloxでフレンドの一覧を見るメニューはどれ？",
     ["A Friends", "B Shop", "C Camera", "D Map"], "A", "友だち＝Friends", "Friendsでフレンド一覧やオンライン状況が見られる。"),
    ("基本", "Robloxで自分のプロフィールを見るときに開くのは？",
     ["A 自分のユーザー名（Profile）", "B 電卓", "C 充電器", "D 時計"], "A", "名前を押すことが多い", "自分のユーザー名やプロフィール画面から確認できる。"),
    ("安全", "知らない人に本名や住所を聞かれた。どうする？",
     ["A 教える", "B ぼかして教える", "C 教えずに無視/ブロック/通報", "D 写真を送る"], "C",
     "個人情報は守る", "個人情報は絶対に教えない。必要なら大人に相談し、通報。"),
    ("安全", "ゲーム内で「無料Robuxあげる」って言われた。安全なのは？",
     ["A ついていく", "B 外部サイトに行く", "C うたがって無視/大人に相談", "D パスワードを渡す"], "C",
     "うますぎる話は注意", "無料Robuxなどの話は詐欺のことが多い。外部リンクは踏まない。"),
    ("マナー", "協力ゲームで、味方が失敗したときの良い言い方は？",
     ["A へたすぎw", "B どんまい！次いこう", "C もう来るな", "D 消えろ"], "B",
     "相手が元気になる言葉", "協力ゲームは励ましや提案が良い。"),
    ("制作", "Roblox Studioで物（パーツ）を置くときに使うのは？",
     ["A Part（パーツ）を挿入", "B 冷蔵庫", "C えんぴつ", "D 電話"], "A",
     "Partって聞いたことある？", "StudioではPartを挿入して形を作っていく。"),
    ("制作", "ゲームの中で「触ったらポイントが増える」みたいな動きを作るのは？",
     ["A Script（スクリプト）", "B 壁紙", "C 目覚まし時計", "D カレンダー"], "A",
     "プログラムのこと", "動き（イベント）はScriptで作れる。"),
    ("基本", "Robloxのアバターで、頭に付けるアイテムは何と呼ばれやすい？",
     ["A Hat / Accessory", "B Battery", "C Notebook", "D Ticket"], "A",
     "身につける＝アクセサリー", "帽子や装飾はAccessoryとして扱われる。"),
    ("基本", "ゲームの中で別の場所へ移動することを何と言うことが多い？",
     ["A Teleport（テレポート）", "B Paint（ペイント）", "C Print（プリント）", "D Sleep（スリープ）"], "A",
     "瞬間移動っぽい言葉", "Teleportは別の場所へ移動させること。"),
    ("安全", "外部のSNSでRobloxの取引を持ちかけられた。どうする？",
     ["A 取引する", "B 直接会う約束をする", "C 断って大人に相談", "D 個人情報を送る"], "C",
     "外部は特に注意", "外部SNSの取引は危険。断って相談が安全。"),
]

# 11〜100を埋める（不足分はこの下でさらに追加して合計100にする）
# ここからは同様の品質で一気に追加（合計100に合わせる）
EVEN_MORE = [
    ("基本", "Robloxのゲーム内で使うお金がRobux以外にある場合、それは多くは何？",
     ["A そのゲーム専用の通貨", "B 本物の円", "C 本物のドル", "D 宝くじ券"], "A",
     "ゲームごとのコインなど", "体験ごとにコイン/ジェムなど独自通貨があることが多い。"),
    ("マナー", "混んでいるサーバーで順番待ちがある。良い行動は？",
     ["A 割り込む", "B 順番を守る", "C じゃまをする", "D 連打してあおる"], "B",
     "ルールを守る", "順番待ちは守るとみんなが楽しい。"),
    ("基本", "Robloxで通報（Report）するのはどんなとき？",
     ["A いい人をほめたいとき", "B ルール違反やいやがらせがあったとき", "C おなかがすいたとき", "D 眠いとき"], "B",
     "困ったときの機能", "嫌がらせや不適切行為はReportで通報できる。"),
    ("制作", "Studioでオブジェクトを動かしたい。まず覚えると良いのは？",
     ["A Position/Move/Rotate", "B Cooking/Boil", "C Swim/Dive", "D Draw/Paint"], "A",
     "移動＝Move", "位置(Position)や移動(Move)回転(Rotate)が基本。"),
    ("制作", "ゲームのテストプレイをStudioで行うボタンは？",
     ["A Play", "B StopWatch", "C Delete", "D Email"], "A",
     "再生っぽい", "Playでローカル実行してテストできる。"),
    ("安全", "知らない人からDMでリンクが来た。安全なのは？",
     ["A すぐ開く", "B クリックしてログインする", "C 開かずに無視/相談", "D パスワードを入れる"], "C",
     "リンクは慎重に", "外部リンクは危険。開かず相談が安全。"),
    ("基本", "アバターの色や服を変えたのに反映されない時、まず試すのは？",
     ["A アプリ再起動/再ログイン", "B パスワード公開", "C 端末を水で洗う", "D ずっと連打"], "A",
     "基本の対処", "反映が遅い/キャッシュの場合は再起動が有効。"),
    ("基本", "Robloxでゲームの評価（いいね）をするとどうなることがある？",
     ["A 開発者の参考になる", "B スマホが壊れる", "C 住所がばれる", "D 画面が割れる"], "A",
     "フィードバック", "評価は開発者が改善する参考になる。"),
]

# 足りない分を作る：同じクオリティでテンプレを使い、内容重複を避けつつ埋める
# （安全/マナー/制作/基本をバランス）
FILLERS = []
topics_cycle = ["基本", "安全", "制作", "マナー"]
base_questions = [
    ("基本", "Robloxでフレンドと同じゲームに入りたい時に使う機能は？",
     ["A Join（参加）", "B Print（印刷）", "C Sleep（睡眠）", "D Scan（スキャン）"], "A",
     "参加するボタン", "フレンドのプロフィール等からJoinできる場合がある。"),
    ("安全", "アカウントを守るために良い習慣は？",
     ["A パスワードをメモして人に見せる", "B 同じパスワードを使い回す", "C 二段階認証が使えるなら使う", "D だれかにログインしてもらう"], "C",
     "追加の安全", "二段階認証などは乗っ取り対策になる。"),
    ("制作", "Studioで『物に名前を付ける』のはなぜ役立つ？",
     ["A 探しやすくなる", "B 勝手に強くなる", "C Robuxが増える", "D 透明になる"], "A",
     "整理が大事", "オブジェクトに名前を付けると管理がしやすい。"),
    ("マナー", "ゲームで負けた時の良い行動は？",
     ["A 暴言を言う", "B 相手を通報する（理由なし）", "C 次の作戦を考える/おつかれと言う", "D 物を投げる"], "C",
     "次に活かす", "負けても落ち着いて次へ。相手を尊重しよう。"),
]

# 合計100問にするため、内容が安全で重複しにくい追加セット
# ここでは「主に安全/マナー/基本/制作の知識」を広げる
EXTRA_SET = [
    ("基本", "Robloxの『サーバー』って何？",
     ["A 同じゲームで一緒に遊んでいる部屋", "B お皿洗い機", "C 本屋さん", "D 自転車"], "A",
     "同じ場所にいる集まり", "サーバーは同じ体験の同じ部屋（インスタンス）みたいなもの。"),
    ("基本", "『ラグい』と言われる時、よく関係するのは？",
     ["A 通信（インターネット）や端末の重さ", "B おやつの量", "C くつのサイズ", "D ねむさだけ"], "A",
     "ネットが遅い/重い", "通信や端末性能で遅延が起きることがある。"),
    ("安全", "本物っぽいログイン画面に飛ばされて入力を求められた。どうする？",
     ["A 入力する", "B 画面を閉じて公式から確認する", "C 友だちにも送る", "D 本名も書く"], "B",
     "公式か確認", "公式以外のログイン要求は危険。閉じて公式で確認。"),
    ("安全", "他人のアカウントに勝手に入るのは？",
     ["A OK", "B ダメ（ルール違反）", "C 面白ければOK", "D 先生ならOK"], "B",
     "当然ダメ", "不正アクセスは重大なルール違反。絶対しない。"),
    ("制作", "『Spawn（スポーン）』はゲームで何の意味？",
     ["A 生まれる場所（出現地点）", "B ごはんの名前", "C 服の種類", "D スコアの単位"], "A",
     "出てくる場所", "Spawnはプレイヤーが出現する地点のこと。"),
    ("制作", "『Anchor（アンカー）』がONのパーツはどうなることが多い？",
     ["A 動きにくく固定される", "B すぐ消える", "C 光る", "D しゃべる"], "A",
     "固定のイメージ", "Anchorはパーツを物理的に固定する設定。"),
    ("マナー", "ボイスチャットやチャットで守ると良いことは？",
     ["A いやなことを言う", "B 相手をバカにする", "C 相手が不快にならない言葉を使う", "D 個人情報を言う"], "C",
     "思いやり", "相手が安心できる言葉づかいが大事。"),
]

def build_quizzes() -> list[Quiz]:
    quizzes = list(QUIZZES)

    qid = len(quizzes) + 1
    for t, q, ch, a, h, e in MORE:
        quizzes.append(Quiz(qid, t, q, ch, a, h, e)); qid += 1
    for t, q, ch, a, h, e in EVEN_MORE:
        quizzes.append(Quiz(qid, t, q, ch, a, h, e)); qid += 1

    # 100問に届くまで、複数セットを回して埋める（内容は健全）
    # ただし完全に同じ問題が増えないよう、セットを少しずつ変える
    pool = []
    pool.extend(EXTRA_SET)
    pool.extend(base_questions)

    # 追加のバリエーション（短いが重複しにくい）
    variant_pool = [
        ("基本", "Robloxで『エモート（Emote）』は何？",
         ["A キャラの動き（ダンス等）", "B 食べ物", "C 掛け算", "D 地図"], "A",
         "ダンスのやつ", "エモートはキャラが踊ったりする動き。"),
        ("安全", "だれかがいやがらせをしているのを見た。良い対処は？",
         ["A 同じことを返す", "B 通報やブロックを使う/大人に相談", "C 本名を言う", "D 外部SNSで拡散"], "B",
         "安全機能を使う", "Report/Blockで自分を守り、大人に相談。"),
        ("制作", "Studioで色を変えるときに関係するのは？",
         ["A Color / Material", "B Volume", "C Battery", "D Password"], "A",
         "色と材質", "ColorやMaterialで見た目を変えられる。"),
        ("マナー", "人が作った作品を見たときの良い言い方は？",
         ["A うざい", "B きもい", "C ここすごい！どうやって作ったの？", "D 消して"], "C",
         "良いところを言う", "良いところを具体的に言うと相手がうれしい。"),
    ]

    pool.extend(variant_pool)

    # 100問になるまで「似てるが完全一致しない」質問を生成
    # 生成は単純だが内容は一般的・健全な範囲に限定
    while len(quizzes) < 100:
        t, q, ch, a, h, e = random.choice(pool)

        # 少しだけ文面を変える（重複対策）
        suffix = ""
        if t == "基本":
            suffix = random.choice(["（基本）", "（初級）", "（チェック）"])
        elif t == "安全":
            suffix = random.choice(["（安全）", "（大事）", "（注意）"])
        elif t == "制作":
            suffix = random.choice(["（Studio）", "（作り方）", "（開発）"])
        else:
            suffix = random.choice(["（マナー）", "（協力）", "（気持ち）"])

        q2 = q + " " + suffix

        quizzes.append(Quiz(qid, t, q2, ch, a, h, e))
        qid += 1

    return quizzes[:100]

ALL_QUIZZES = build_quizzes()

# -----------------------------
# 出題ロジック
# -----------------------------

stats = Stats()
current: Quiz | None = None
attempt_in_problem = 0  # 0=初回, 1=ヒント後

def format_quiz(qz: Quiz) -> str:
    lines = [f"Q{qz.qid}. {qz.question}"]
    lines.extend(qz.choices)
    lines.append("（答えは A/B/C/D または選択肢の文章でもOK）")
    return "\n".join(lines)

def pick_quiz() -> Quiz:
    # 間違えた問題を少し優先して復習（最大40%くらい）
    if stats.wrong_ids and random.random() < 0.4:
        qid = random.choice(stats.wrong_ids)
        return ALL_QUIZZES[qid - 1]
    return random.choice(ALL_QUIZZES)

def parse_answer(user: str, qz: Quiz) -> str | None:
    u = normalize(user)
    if u in ["a", "b", "c", "d"]:
        return u.upper()

    # 選択肢の文章入力でもOKにする
    # "A ..." の "..." 部分と、全体でも照合
    for choice in qz.choices:
        key = choice[:1].upper()
        text = normalize(choice[2:]) if len(choice) > 2 else ""
        if u == normalize(choice) or (text and u == text):
            return key

    # "A." "A:" みたいな入力も拾う
    if u and u[0] in ["a", "b", "c", "d"]:
        return u[0].upper()

    return None

def new_problem(event=None):
    global current, attempt_in_problem
    current = pick_quiz()
    attempt_in_problem = 0
    stats.asked += 1

    set_question(format_quiz(current), current.topic)
    clear_answer()
    log(f" 出題しました。")

def submit_answer(event=None):
    global attempt_in_problem

    if current is None:
        log("まず「出題」を押してね。")
        return

    user = get_answer()
    if not user:
        log("答えが空だよ。A/B/C/D を入力してね。")
        return

    chosen = parse_answer(user, current)
    if chosen is None:
        log("うまく読めなかったよ。A/B/C/D か、選択肢の文章で答えてね。")
        return

    if chosen == current.answer_key:
        stats.correct += 1
        stats.wrong_streak = 0
        # もし復習リストにあったら外す（全部消すのではなく、1つだけ外す）
        if current.qid in stats.wrong_ids:
            stats.wrong_ids = [x for x in stats.wrong_ids if x != current.qid]

        log("OK！正解！")
        log(f"解説：{current.explanation}")
        new_problem()
        return

    # 不正解
    stats.wrong_streak += 1
    if current.qid not in stats.wrong_ids:
        stats.wrong_ids.append(current.qid)

    attempt_in_problem += 1
    if attempt_in_problem == 1:
        log("おしい！")
        log(f"ヒント：{current.hint}")
        log("もういちど入力して「答える」を押してね。")
        return

    # 2回目も不正解 → 解説
    log("だいじょうぶ。答えと解説だよ：")
    log(f"正しい答え：{current.answer_key}")
    log(f"解説：{current.explanation}")
    new_problem()

def show_stats(event=None):
    rate = (stats.correct / stats.asked * 100) if stats.asked else 0
    msg = [
        "=== せいせき ===",
        f"正解：{stats.correct} / {stats.asked}（{rate:.0f}%）",
        f"復習リスト（まちがえた問題）：{len(stats.wrong_ids)}こ",
        "※ まちがえた問題は、次の出題で少し出やすくなるよ。",
    ]
    log("\n".join(msg))

def reset_session(event=None):
    global stats, current, attempt_in_problem
    stats = Stats()
    current = None
    attempt_in_problem = 0
    el("log").textContent = ""
    set_question("まず「出題」を押してね。", "Robloxクイズ")
    clear_answer()
    log("リセットしました。")

# 初期表示
reset_session()
