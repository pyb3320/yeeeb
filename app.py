import streamlit as st
import re
from datetime import datetime

# ============================================================
# Streamlit 교육용 학습지
# - AI Studio 화면을 Streamlit 스타일로 재현하기 위한 기본 구조
# - 2쪽 학습지 / 11개 빈칸 / 자동채점 / 결과 저장
# - Google Sheets 연동은 아래 GOOGLE SHEETS 설정을 넣으면 활성화
# ============================================================

st.set_page_config(
    page_title="AI 학습지",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# -----------------------------
# 기본 스타일
# -----------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Noto Sans KR', sans-serif;
}

.stApp {
    background: #f6f8fb;
}

.block-container {
    max-width: 1180px;
    padding-top: 1.5rem;
    padding-bottom: 3rem;
}

.hero {
    background: linear-gradient(135deg, #eef5ff 0%, #ffffff 55%, #f4f0ff 100%);
    border: 1px solid #dce7f5;
    border-radius: 22px;
    padding: 28px 32px;
    margin-bottom: 20px;
}

.hero-title {
    font-size: 30px;
    font-weight: 800;
    color: #172033;
    margin-bottom: 8px;
}

.hero-sub {
    font-size: 15px;
    color: #657085;
}

.info-card {
    background: white;
    border: 1px solid #e4e8ef;
    border-radius: 18px;
    padding: 20px;
    margin: 12px 0;
}

.section-title {
    font-size: 20px;
    font-weight: 800;
    color: #202938;
    margin-bottom: 12px;
}

.word-bank {
    background: #f8f9fc;
    border: 1px solid #e5e8ef;
    border-radius: 16px;
    padding: 18px;
    margin: 12px 0 20px 0;
}

.word {
    display: inline-block;
    background: #ffffff;
    border: 1px solid #d8deea;
    border-radius: 10px;
    padding: 7px 13px;
    margin: 4px;
    font-size: 14px;
    font-weight: 600;
}

.answer-box {
    background: #ffffff;
    border: 1px solid #e2e7ef;
    border-radius: 16px;
    padding: 18px;
    margin: 10px 0;
}

.score-card {
    background: linear-gradient(135deg, #f2f7ff, #ffffff);
    border: 1px solid #cfdff6;
    border-radius: 18px;
    padding: 22px;
    text-align: center;
}

.score-number {
    font-size: 42px;
    font-weight: 800;
    color: #2463eb;
}

.small-muted {
    color: #788397;
    font-size: 13px;
}

.correct {
    color: #14804a;
    font-weight: 700;
}

.wrong {
    color: #d14343;
    font-weight: 700;
}

.footer {
    text-align: center;
    color: #8a94a6;
    font-size: 12px;
    margin-top: 40px;
}
</style>
""", unsafe_allow_html=True)


# -----------------------------
# 상태 초기화
# -----------------------------
if "page" not in st.session_state:
    st.session_state.page = 1

if "submitted" not in st.session_state:
    st.session_state.submitted = False

if "scores" not in st.session_state:
    st.session_state.scores = [0] * 11

if "total_score" not in st.session_state:
    st.session_state.total_score = 0


# -----------------------------
# 정답 설정
# 기존 HTML의 정답으로 교체
# -----------------------------
ANSWER = {
    1: "",
    2: "",
    3: "",
    4: "",
    5: "",
    6: "",
    7: "",
    8: "",
    9: "",
    10: "",
    11: "",
}


# -----------------------------
# 공백 제거 후 비교
# -----------------------------
def normalize(text):
    if text is None:
        return ""
    text = str(text).strip().lower()
    text = re.sub(r"\s+", "", text)
    return text


def check_answer(number, user_answer):
    correct_answer = ANSWER.get(number, "")

    # 정답이 비어 있으면 임시로 채점하지 않음
    if normalize(correct_answer) == "":
        return 0

    return 1 if normalize(user_answer) == normalize(correct_answer) else 0


# -----------------------------
# Google Sheets 저장
# -----------------------------
def save_to_google_sheet(data):
    """
    Streamlit Cloud의 Secrets에 다음 형식으로 Google 서비스 계정 정보를 넣으면 사용 가능.

    [gcp_service_account]
    type = "service_account"
    project_id = "..."
    private_key_id = "..."
    private_key = "-----BEGIN PRIVATE KEY-----\\n...\\n-----END PRIVATE KEY-----\\n"
    client_email = "..."
    client_id = "..."
    auth_uri = "https://accounts.google.com/o/oauth2/auth"
    token_uri = "https://oauth2.googleapis.com/token"
    auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
    client_x509_cert_url = "..."

    [google_sheet]
    spreadsheet_id = "구글시트ID"
    worksheet_name = "Sheet1"
    """

    try:
        import gspread
        from google.oauth2.service_account import Credentials

        if "gcp_service_account" not in st.secrets:
            return False, "Google 서비스 계정 설정이 없습니다."

        if "google_sheet" not in st.secrets:
            return False, "Google Sheet 설정이 없습니다."

        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]

        credentials = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=scopes,
        )

        client = gspread.authorize(credentials)

        spreadsheet_id = st.secrets["google_sheet"]["spreadsheet_id"]
        worksheet_name = st.secrets["google_sheet"].get(
            "worksheet_name", "Sheet1"
        )

        sheet = client.open_by_key(spreadsheet_id).worksheet(worksheet_name)

        sheet.append_row(data, value_input_option="USER_ENTERED")

        return True, "저장되었습니다."

    except Exception as e:
        return False, f"Google Sheets 저장 오류: {e}"


# -----------------------------
# 상단 헤더
# -----------------------------
st.markdown("""
<div class="hero">
    <div class="hero-title">📝 AI 학습 활동지</div>
    <div class="hero-sub">
        학습 내용을 확인하고 빈칸을 완성한 뒤 자동채점 결과를 확인해 보세요.
    </div>
</div>
""", unsafe_allow_html=True)


# -----------------------------
# 학생 정보
# -----------------------------
with st.container():
    st.markdown('<div class="section-title">학생 정보</div>', unsafe_allow_html=True)

    c1, c2, c3 = st.columns([1, 1, 2])

    with c1:
        class_name = st.text_input(
            "반",
            placeholder="예: 1",
            key="class_name",
        )

    with c2:
        student_number = st.text_input(
            "번호",
            placeholder="예: 15",
            key="student_number",
        )

    with c3:
        student_name = st.text_input(
            "이름",
            placeholder="이름을 입력하세요",
            key="student_name",
        )


# -----------------------------
# 페이지 선택
# -----------------------------
tab1, tab2 = st.tabs(["① 학습 활동", "② 생각 정리"])


# ============================================================
# PAGE 1
# ============================================================
with tab1:
    st.markdown(
        '<div class="info-card"><div class="section-title">1. 핵심 개념 확인</div>'
        '<p>아래 학습 내용을 읽고 빈칸에 알맞은 내용을 입력하세요.</p></div>',
        unsafe_allow_html=True,
    )

    # 실제 AI Studio HTML의 내용을 이 부분에 넣으면 됨
    st.markdown("""
    <div class="info-card">
        <b>학습 내용</b><br><br>
        이 영역에는 기존 AI Studio 학습지의 설명 문장을 그대로 넣을 수 있습니다.
        <br>
        <span class="small-muted">
        ※ 현재 코드는 UI 구조를 먼저 구현한 버전입니다.
        </span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(
        '<div class="word-bank"><b>단어 보관함</b><br>'
        '<span class="word">핵심어 1</span>'
        '<span class="word">핵심어 2</span>'
        '<span class="word">핵심어 3</span>'
        '<span class="word">핵심어 4</span>'
        '<span class="word">핵심어 5</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    # 1~6번
    for i in range(1, 7):
        st.markdown(
            f'<div class="answer-box"><b>{i}번</b></div>',
            unsafe_allow_html=True,
        )

        st.text_input(
            f"{i}번 답",
            key=f"answer_{i}",
            label_visibility="collapsed",
            placeholder="답을 입력하세요.",
        )


# ============================================================
# PAGE 2
# ============================================================
with tab2:
    st.markdown(
        '<div class="info-card"><div class="section-title">2. 학습 내용 적용하기</div>'
        '<p>배운 내용을 활용하여 다음 문항에 답하세요.</p></div>',
        unsafe_allow_html=True,
    )

    for i in range(7, 12):
        st.markdown(
            f'<div class="answer-box"><b>{i}번</b></div>',
            unsafe_allow_html=True,
        )

        st.text_input(
            f"{i}번 답",
            key=f"answer_{i}",
            label_visibility="collapsed",
            placeholder="답을 입력하세요.",
        )

    st.markdown("---")

    st.markdown(
        '<div class="section-title">활동 기록</div>',
        unsafe_allow_html=True,
    )

    activity1 = st.text_area(
        "활동 1",
        placeholder="활동하면서 생각한 점이나 근거를 적어보세요.",
        key="activity1",
        height=100,
    )

    activity2 = st.text_area(
        "활동 2",
        placeholder="친구의 의견을 듣고 새롭게 생각한 점을 적어보세요.",
        key="activity2",
        height=100,
    )

    self_check = st.text_area(
        "자기 점검",
        placeholder="이번 활동을 스스로 돌아보고 적어보세요.",
        key="self_check",
        height=100,
    )


# -----------------------------
# 채점 버튼
# -----------------------------
st.markdown("---")

col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    submit = st.button(
        "✅ 자동 채점",
        type="primary",
        use_container_width=True,
    )

with col2:
    reset = st.button(
        "↺ 초기화",
        use_container_width=True,
    )

with col3:
    show_answer = st.button(
        "💡 정답 보기",
        use_container_width=True,
    )


# -----------------------------
# 초기화
# -----------------------------
if reset:
    for i in range(1, 12):
        st.session_state[f"answer_{i}"] = ""

    st.session_state.submitted = False
    st.session_state.scores = [0] * 11
    st.session_state.total_score = 0

    st.rerun()


# -----------------------------
# 정답 보기
# -----------------------------
if show_answer:
    st.markdown(
        '<div class="info-card"><div class="section-title">정답</div>',
        unsafe_allow_html=True,
    )

    for i in range(1, 12):
        answer = ANSWER[i]

        if normalize(answer):
            st.write(f"{i}번 : {answer}")
        else:
            st.write(f"{i}번 : 정답을 코드에 입력하세요.")

    st.markdown("</div>", unsafe_allow_html=True)


# -----------------------------
# 자동 채점
# -----------------------------
if submit:
    scores = []

    for i in range(1, 12):
        user_answer = st.session_state.get(f"answer_{i}", "")
        scores.append(check_answer(i, user_answer))

    st.session_state.scores = scores
    st.session_state.total_score = sum(scores)
    st.session_state.submitted = True

    score_rate = round(
        st.session_state.total_score / 11 * 100, 1
    )

    # Google Sheets 저장용 데이터
    answers = [
        st.session_state.get(f"answer_{i}", "")
        for i in range(1, 12)
    ]

    save_data = [
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        class_name,
        student_number,
        student_name,
        *answers,
        *scores,
        st.session_state.total_score,
        score_rate,
        activity1,
        activity2,
        self_check,
    ]

    ok, message = save_to_google_sheet(save_data)

    if ok:
        st.success("채점 결과가 저장되었습니다.")
    else:
        st.info(
            "채점은 완료되었습니다. Google Sheets 저장은 설정 후 사용할 수 있습니다."
        )

    st.rerun()


# -----------------------------
# 결과 표시
# -----------------------------
if st.session_state.submitted:
    total = st.session_state.total_score
    rate = round(total / 11 * 100, 1)

    st.markdown("---")
    st.markdown(
        '<div class="section-title">채점 결과</div>',
        unsafe_allow_html=True,
    )

    r1, r2, r3 = st.columns(3)

    with r1:
        st.markdown(
            f"""
            <div class="score-card">
                <div class="small-muted">총점</div>
                <div class="score-number">{total} / 11</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with r2:
        st.markdown(
            f"""
            <div class="score-card">
                <div class="small-muted">점수율</div>
                <div class="score-number">{rate}%</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with r3:
        correct = sum(st.session_state.scores)
        wrong = 11 - correct

        st.markdown(
            f"""
            <div class="score-card">
                <div class="small-muted">정답 / 오답</div>
                <div class="score-number" style="font-size:30px;">
                    {correct} / {wrong}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("### 문항별 결과")

    for i, score in enumerate(st.session_state.scores, start=1):
        if score == 1:
            st.markdown(
                f'<div class="correct">✓ {i}번 정답</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div class="wrong">✕ {i}번 오답 또는 미입력</div>',
                unsafe_allow_html=True,
            )


st.markdown(
    '<div class="footer">AI 학습 활동지 · Streamlit</div>',
    unsafe_allow_html=True,
)
