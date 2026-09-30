# -*- coding: utf-8 -*-
"""중학교 1학년 정보 - 데이터의 구조화와 분석 인터랙티브 활동지

PDF의 A4 활동지 레이아웃을 최대한 유지하면서
직접 입력 + 단어 드래그&드롭 + 자동채점 + Google Sheets 저장을 지원합니다.

필수: Streamlit 1.51+
"""

from datetime import datetime
import streamlit as st

st.set_page_config(
    page_title="데이터의 구조화와 분석 활동지",
    page_icon="📘",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Streamlit 바깥 여백을 줄여 PDF 같은 종이 레이아웃으로 보이게 함.
st.markdown(
    """
    <style>
    #MainMenu, footer { visibility:hidden; }
    header[data-testid="stHeader"] { height:0 !important; background:transparent; }
    .block-container { max-width:1180px !important; padding:8px 12px 24px !important; }
    [data-testid="stAppViewContainer"] { background:#eef1f5; }
    </style>
    """,
    unsafe_allow_html=True,
)

ANSWERS = {
    "1": "데이터",
    "2": "특성",
    "3": "정리 및 배열",
    "4": "통일된 모양",
    "5": "쉽게 찾을",
    "6": "내용 요소 간의 관계",
    "7": "효율적으로 관리",
    "8": "기준",
    "9": "세로줄과 가로줄",
    "10": "점, 선, 도형",
    "11": "소프트웨어 개발 전문가",
    "12": "시스템 SW 개발자",
    "13": "운영체제 프로그래머",
    "14": "임베디드 프로그래머",
    "15": "응용 SW 개발자",
    "16": "응용 SW 프로그래머",
    "17": "네트워크 프로그래머",
    "18": "컴퓨터 및 모바일 게임 프로그래머",
}


def save_to_google_sheet(payload: dict):
    """Google Sheets Secrets가 있으면 한 행으로 저장합니다."""
    try:
        import gspread
        from google.oauth2.service_account import Credentials

        if "gcp_service_account" not in st.secrets:
            return False, "Google 서비스 계정 Secrets가 없습니다."
        if "google_sheet" not in st.secrets:
            return False, "Google Sheet Secrets가 없습니다."

        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
        credentials = Credentials.from_service_account_info(
            dict(st.secrets["gcp_service_account"]), scopes=scopes
        )
        client = gspread.authorize(credentials)
        spreadsheet_id = st.secrets["google_sheet"]["spreadsheet_id"]
        worksheet_name = st.secrets["google_sheet"].get("worksheet_name", "Sheet1")
        worksheet = client.open_by_key(spreadsheet_id).worksheet(worksheet_name)

        blanks = payload.get("blanks", {})
        import json
        list_rows = payload.get("listRows", [])
        table_rows = payload.get("tableRows", [])
        experience_list_rows = payload.get("experienceListRows", [])
        experience_table_rows = payload.get("experienceTableRows", [])
        experience_diagram_rows = payload.get("experienceDiagramRows", [])
        checks = payload.get("selfChecks", {})

        row = [
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            payload.get("grade", "1"),
            payload.get("className", ""),
            payload.get("number", ""),
            payload.get("name", ""),
            *[blanks.get(str(i), "") for i in range(1, 14)],
            payload.get("score", 0),
            payload.get("structure", "표"),
            json.dumps(list_rows, ensure_ascii=False),
            json.dumps(table_rows, ensure_ascii=False),
            json.dumps(experience_list_rows, ensure_ascii=False),
            json.dumps(experience_table_rows, ensure_ascii=False),
            json.dumps(experience_diagram_rows, ensure_ascii=False),
            json.dumps(checks, ensure_ascii=False),
        ]
        worksheet.append_row(row, value_input_option="USER_ENTERED")
        return True, "Google Sheets에 저장되었습니다."
    except Exception as exc:
        return False, f"Google Sheets 저장 오류: {exc}"


# ------------------------------------------------------------
# PDF와 비슷한 화면을 만드는 Custom Component V2
# ------------------------------------------------------------
HTML = r'''
<div id="worksheet-root">

  <!-- ==================== 앞면 ==================== -->
  <section class="sheet sheet-front" data-page="1">
    <header class="sheet-header">
      <div class="header-left">
        <div class="badge">중학교 정보과 활동지 [앞면]</div>
        <h1>활동지 - 데이터의 구조화 <span>(목록형과 표 만들기)</span></h1>
      </div>
      <div class="student-card">
        <span>1학년</span>
        <input id="className" class="line-input tiny" inputmode="numeric" value="1">
        <span>반</span>
        <input id="studentNo" class="line-input tiny" inputmode="numeric" placeholder="1">
        <span>번</span>
        <span>이름:</span>
        <input id="studentName" class="line-input name" placeholder="홍길동">
      </div>
    </header>

    <div class="rule"></div>

    <section class="word-panel">
      <div class="word-guide">💡 <b>【빈칸 넣기 단어 보관함】</b> 아래 단어를 빈칸으로 드래그하거나 클릭하여 채워보세요!</div>
      <div class="word-guide-sub">(맞으면 연두색, 틀리면 빨간색이 표시됩니다.)</div>
      <div id="wordBank" class="word-bank"></div>
    </section>

    <h2><span class="circle-num">1</span>데이터를 왜 구조화해야 할까?</h2>

    <section class="concept-box blue-box">
      <div class="box-title">✣ [교과서 핵심 개념] 데이터 구조화의 정의</div>
      <div class="sentence">
        전달하려고 하는
        <span class="drop blank" data-id="1" data-answer="데이터" contenteditable="true" spellcheck="false"></span>
        의 내용 요소들을
        <span class="drop blank" data-id="2" data-answer="특성" contenteditable="true" spellcheck="false"></span>
        에 맞게
        <span class="drop blank" data-id="3" data-answer="정리 및 배열" contenteditable="true" spellcheck="false"></span>
        하여
        <span class="drop blank" data-id="4" data-answer="통일된 모양" contenteditable="true" spellcheck="false"></span>
        으로 표현하는 것을 말한다.
      </div>
    </section>

    <section class="reason-box">
      <div class="reason-head">
        <b>데이터 구조화를 하는 주요 이유 4가지</b>
        <span>(교과서 63쪽~65쪽)</span>
      </div>
      <div class="reason-row"><span class="reason-no">①</span><span>원하는 데이터를</span>
        <span class="drop blank" data-id="5" data-answer="쉽게 찾을" contenteditable="true" spellcheck="false"></span>
        <span>수 있다. (예: 학번으로 구조화된 학생 검색, 도서관 청구기호)</span>
      </div>
      <div class="reason-row"><span class="reason-no">②</span>
        <span class="drop blank wide" data-id="6" data-answer="내용 요소 간의 관계" contenteditable="true" spellcheck="false"></span>
        <span>를 쉽게 이해할 수 있다. (예: 가족 가계도, 회사 조직도)</span>
      </div>
      <div class="reason-row"><span class="reason-no">③</span>
        <span>빠지거나 잘못된 데이터(오류 및 결측치)를 쉽게 파악할 수 있다. (예: 시간표 중복·누락 확인)</span>
      </div>
      <div class="reason-row"><span class="reason-no">④</span><span>데이터를</span>
        <span class="drop blank" data-id="7" data-answer="효율적으로 관리" contenteditable="true" spellcheck="false"></span>
        <span>할 수 있으며, 분석하여 더 나은 의사 결정을 내릴 수 있다.</span>
      </div>
    </section>

    <h2><span class="circle-num">2</span>데이터는 어떤 방법으로 구조화할 수 있을까? <span class="subtitle">(3대 구조 비교)</span></h2>

    <section class="compare-table">
      <table>
        <thead><tr><th style="width:20%">구조 형태</th><th style="width:55%">특징 및 구조화 원리</th><th style="width:25%">대표적인 실생활 예</th></tr></thead>
        <tbody>
          <tr>
            <td class="type-list">☷ <b>1. 목록 (List)</b></td>
            <td>
              <div>• 일정한 <span class="drop blank small" data-id="8" data-answer="기준" contenteditable="true" spellcheck="false"></span> 에 맞추어 데이터를 순서대로 나열한 구조</div>
              <div class="good">• 장점: 구조가 간단하고 일관성이 있어 작성이 빠름</div>
            </td>
            <td>건물의 층별 안내도, 시간별 일정표, 요리 순서(레시피)</td>
          </tr>
          <tr>
            <td class="type-table">▦ <b>2. 표 (Table)</b></td>
            <td>
              <div>• 서로 다른 두 기준인 <span class="drop blank" data-id="9" data-answer="세로줄과 가로줄" contenteditable="true" spellcheck="false"></span> (행과 열)로 나누어 격자로 나타낸 구조</div>
              <div class="good">• 장점: 데이터 간의 비교와 수정, 통계 계산이 매우 쉬움</div>
            </td>
            <td>학급 시간표, 성적표, 용돈 기입장, 버스 시간표</td>
          </tr>
          <tr>
            <td class="type-diagram">⌯ <b>3. 다이어그램</b></td>
            <td>
              <div>• <span class="drop blank" data-id="10" data-answer="점, 선, 도형" contenteditable="true" spellcheck="false"></span>, 화살표, 그래프 등을 사용하여 관계를 그림으로 시각화</div>
              <div class="good">• 형태: 계층형(가계도), 네트워크/망형(노선도), 그래프·차트형(비교)</div>
            </td>
            <td>가족 가계도, 지하철 노선도, 과목 점수 막대그래프</td>
          </tr>
        </tbody>
      </table>
    </section>

    <section class="practice-block">
      <div class="practice-title blue-title">
        <span class="practice-icon blue">▣</span>
        <b>[활동 1] 목록(List)형 데이터 만들기: 우리 반 학급 1인 1역할 체크리스트</b>
      </div>
      <div class="practice-note">* 일정한 기준(시간 순서 또는 중요도)에 맞춰 순서대로 나열합니다. 1번은 샘플이며 2번부터 자유롭게 작성하세요.</div>
      <div class="dynamic-area" id="activity1ListArea"></div>
      <button class="add-row-btn" id="addListBtn">＋ 목록 항목 추가</button>
    </section>

    <section class="practice-block">
      <div class="practice-title green-title">
        <span class="practice-icon green">▣</span>
        <b>[활동 2] 표(Table) 만들기 실습: 우리 모둠 친구 데이터 정리</b>
      </div>
      <div class="practice-note">* 가로줄(행: 친구)과 세로줄(열: 항목)로 구성된 2차원 표입니다. 1번은 샘플이며 필요한 만큼 행을 추가하세요.</div>
      <div class="dynamic-table-wrap">
        <table class="student-table" id="activity2Table">
          <thead><tr><th>번호</th><th>친구 이름</th><th>생일 (월/일)</th><th>취미 / 특기</th><th>역할 또는 한 줄 메모</th><th class="delete-col">삭제</th></tr></thead>
          <tbody id="activity2TableBody"></tbody>
        </table>
      </div>
      <button class="add-row-btn green-add" id="addTableBtn">＋ 표 행 추가</button>
    </section>

    <footer class="sheet-footer">
      <span>중학교 1학년 정보 &lt;데이터의 구조화와 분석&gt;</span>
      <span>- 1 - (앞면: 목록 &amp; 표)</span>
      <button class="footer-nav" data-go="2">뒷면으로 이어집니다 ➡</button>
    </footer>
  </section>

  <!-- ==================== 뒷면 ==================== -->
  <section class="sheet sheet-back hidden" data-page="2">
    <header class="sheet-header">
      <div class="header-left">
        <div class="badge">중학교 정보과 활동지 [뒷면]</div>
        <h1>활동지 - 데이터의 구조화 <span>(다이어그램과 그래프 완성)</span></h1>
      </div>
      <div class="book-info">교과서 66~67쪽 연계 탐구</div>
    </header>

    <div class="rule"></div>

    <section class="activity-heading">
      <span class="practice-icon purple">▣</span>
      <b>[활동 3] 다이어그램 만들기: (가) 글을 읽고 (나) 계층형 다이어그램 빈칸 채우기</b>
    </section>

    <section class="reading-box">
      <div class="box-title">[ (가) 교과서 본문 줄글 제시문 ]</div>
      <p>"소프트웨어 개발 전문가는 <b>시스템 SW 개발자</b>와 <b>응용 SW 개발자</b>로 나뉜다. 시스템 SW 개발자는 <b>운영체제 프로그래머</b>와 <b>임베디드 프로그래머</b>가 있다. 응용 SW 개발자는 <b>응용 SW 프로그래머</b>, <b>네트워크 프로그래머</b>, <b>컴퓨터 및 모바일 게임 프로그래머</b>가 있다."</p>
    </section>

    <section class="diagram-box">
      <div class="diagram-guide">[ (나) 계층형 구조도 (트리 다이어그램) - 빈칸에 단어를 끌어다 놓으세요 ]</div>
      <div class="page2-bank" id="page2Bank"><span class="page2-label">단어 보관함</span></div>

      <div class="tree">
        <div class="tree-level top-level">
          <div class="hierarchy-node root-hierarchy">
            <div class="node-label">최상위 분류</div>
            <span class="drop blank hierarchy-drop" data-id="11" data-answer="소프트웨어 개발 전문가" contenteditable="true" spellcheck="false"></span>
          </div>
        </div>
        <div class="hierarchy-main-line"></div>
        <div class="tree-level branch-level">
          <div class="hierarchy-branch system-branch">
            <div class="hierarchy-node">
              <div class="node-label">분류 1 · 시스템</div>
              <span class="drop blank hierarchy-drop" data-id="12" data-answer="시스템 SW 개발자" contenteditable="true" spellcheck="false"></span>
            </div>
            <div class="child-line"></div>
            <div class="child-grid two-child">
              <div class="leaf hierarchy-leaf">
                <div class="node-label">하위 직무</div>
                <span class="drop blank leaf-drop" data-id="13" data-answer="운영체제 프로그래머" contenteditable="true" spellcheck="false"></span>
              </div>
              <div class="leaf hierarchy-leaf">
                <div class="node-label">하위 직무</div>
                <span class="drop blank leaf-drop" data-id="14" data-answer="임베디드 프로그래머" contenteditable="true" spellcheck="false"></span>
              </div>
            </div>
          </div>
          <div class="hierarchy-branch application-branch">
            <div class="hierarchy-node purple-hierarchy">
              <div class="node-label">분류 2 · 응용</div>
              <span class="drop blank hierarchy-drop" data-id="15" data-answer="응용 SW 개발자" contenteditable="true" spellcheck="false"></span>
            </div>
            <div class="child-line purple-child-line"></div>
            <div class="child-grid three-child">
              <div class="leaf hierarchy-leaf purple-leaf">
                <div class="node-label">하위 직무</div>
                <span class="drop blank leaf-drop" data-id="16" data-answer="응용 SW 프로그래머" contenteditable="true" spellcheck="false"></span>
              </div>
              <div class="leaf hierarchy-leaf purple-leaf">
                <div class="node-label">하위 직무</div>
                <span class="drop blank leaf-drop" data-id="17" data-answer="네트워크 프로그래머" contenteditable="true" spellcheck="false"></span>
              </div>
              <div class="leaf hierarchy-leaf purple-leaf">
                <div class="node-label">하위 직무</div>
                <span class="drop blank leaf-drop" data-id="18" data-answer="컴퓨터 및 모바일 게임 프로그래머" contenteditable="true" spellcheck="false"></span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <section class="activity-heading space-top">
      <span class="practice-icon purple">▣</span>
      <b>[활동 4] 민호의 체험학습 계획을 내가 원하는 형태로 구조화해 보자</b>
    </section>

    <section class="yellow-box">
      "4월에는 아름다운 봄꽃을 보러 <b>경복궁, 창덕궁, 종묘</b> 등을 방문할 예정이다. 서울 <b>지하철 3호선</b>을 탄다. 5월에는 가족과 함께 <b>지하철 2호선</b>을 타고 미술관이 있는 <b>덕수궁</b>에 간다. 6월에는 선조들의 얼을 기리고자 <b>전쟁기념관</b>과 <b>국립중앙박물관</b>을 방문하며 <b>지하철 4호선</b>을 탄다."
    </section>

    <section class="structure-choice">
      <b>구조화 형태 선택:</b>
      <div class="choice-buttons">
        <button data-structure="목록">☷ 1. 목록(리스트)</button>
        <button data-structure="표" class="selected">▦ 2. 표(테이블)</button>
        <button data-structure="다이어그램">♧ 3. 다이어그램(노선망)</button>
      </div>
    </section>

    <section id="structureOutput" class="structure-output">
      <div class="output-title">[ 표(Table)로 구조화한 체험학습 계획 ]</div>
      <div id="experienceEditor" class="experience-editor"></div>
    </section>

    <section class="check-box">
      <div class="check-title">✣ 스스로 배움 점검하기 <span>(성취기준 도달 확인)</span><small>배운 내용을 되돌아보며 체크해보세요</small></div>
      <label><input type="checkbox" id="check1"> 1. 데이터 구조화의 뜻과 구조화가 필요한 4가지 이유를 설명할 수 있는가?</label>
      <label><input type="checkbox" id="check2"> 2. 실생활 데이터의 성격에 맞춰 목록, 표, 다이어그램 중 가장 효과적인 형태를 선택할 수 있는가?</label>
      <label><input type="checkbox" id="check3"> 3. 줄글 형태의 복잡한 데이터를 목록, 표, 계층형/네트워크/차트 다이어그램으로 직접 체계화할 수 있는가?</label>
    </section>

    <div class="result-area">
      <div id="scoreText" class="score-text"></div>
      <button id="gradeBtn" class="primary-btn">✅ 자동 채점 및 저장</button>
      <button id="clearBtn" class="secondary-btn">초기화</button>
    </div>

    <footer class="sheet-footer">
      <button class="footer-nav" data-go="1">⬅ 앞면으로</button>
      <span>- 2 - (뒷면: 다이어그램 &amp; 차트)</span>
      <span class="finish">수고하셨습니다! 👍</span>
    </footer>
  </section>
</div>
'''

CSS = r'''
:host { display:block; width:100%; }
* { box-sizing:border-box; }
#worksheet-root {
  --ink:#10213b; --line:#b9cbe0; --blue:#1e68dc; --soft:#f5f9ff;
  font-family:"Noto Sans KR","Malgun Gothic",Arial,sans-serif;
  color:var(--ink); font-size:14px; line-height:1.52;
  background:#eef1f5; padding:16px 8px 28px;
}
.sheet {
  width:min(980px,100%); min-height:1390px; margin:0 auto 22px; padding:28px 30px 22px;
  background:#fff; border-radius:2px; box-shadow:0 8px 28px rgba(34,55,86,.10);
}
.hidden { display:none !important; }
.sheet-header { display:flex; justify-content:space-between; gap:18px; align-items:flex-start; }
.header-left { min-width:0; }
.badge { display:inline-block; color:#1264df; border:1px solid #8db8f1; background:#eff7ff; border-radius:5px; padding:4px 9px; font-size:12px; font-weight:900; }
h1 { margin:4px 0 0; font-size:25px; line-height:1.22; letter-spacing:-.8px; font-weight:900; }
h1 span { font-weight:800; }
.student-card,.book-info { border:1px solid var(--line); background:#f8fbff; border-radius:5px; padding:7px 10px; font-size:12px; color:#344965; white-space:nowrap; }
.student-card { display:flex; align-items:center; gap:6px; }
.line-input { border:0; border-bottom:1px solid #8fa3bc; background:transparent; color:#1b3150; outline:none; font:inherit; padding:1px 2px; }
.line-input.tiny { width:24px; text-align:center; }
.line-input.name { width:72px; }
.rule { height:3px; background:#102038; margin:12px 0 10px; }
.word-panel { border:1px solid #b9d1ee; border-radius:7px; background:#f7fbff; padding:8px 10px 7px; }
.word-guide { color:#155695; font-size:11px; font-weight:800; }
.word-guide-sub { color:#6c8097; font-size:10px; margin-top:2px; }
.word-bank,.page2-bank { display:flex; flex-wrap:wrap; gap:4px; margin-top:4px; }
.word { user-select:none; cursor:grab; border:1px solid #6ba4df; background:#fff; color:#155ea6; padding:2px 7px; border-radius:4px; font-size:11px; font-weight:900; }
.word:active { cursor:grabbing; }
h2 { font-size:19px; margin:12px 0 6px; line-height:1.3; font-weight:900; letter-spacing:-.3px; }
.subtitle { font-weight:800; }
.circle-num { display:inline-flex; align-items:center; justify-content:center; width:24px; height:24px; margin-right:5px; background:#1b63db; color:#fff; border-radius:50%; font-size:14px; vertical-align:2px; }
.concept-box,.reason-box,.compare-table,.practice-block,.reading-box,.diagram-box,.yellow-box,.structure-choice,.structure-output,.check-box { border:1px solid var(--line); border-radius:7px; overflow:hidden; }
.blue-box { border-color:#78b1f3; background:#f5f9ff; padding:11px 12px 10px; }
.box-title { color:#184f92; font-weight:900; margin-bottom:5px; }
.sentence { font-size:15px; }
.drop { display:inline-flex; min-width:72px; min-height:28px; align-items:center; justify-content:center; border:2px solid #97a9c0; border-radius:5px; background:#fbfcfd; color:#7b8799; padding:2px 7px; vertical-align:middle; outline:none; font-weight:800; white-space:normal; text-align:center; }
.drop:focus { border-color:#2978e8; box-shadow:0 0 0 2px #dceaff; }
.drop::after { content:"●"; position:absolute; right:4px; top:2px; font-size:8px; line-height:1; color:#d76666; }
.drop { position:relative; padding-right:15px; }
.drop.correct::after { color:#42a968; }
.drop.wrong::after { color:#d76666; }

.drop.dragover { background:#e6f1ff; border-color:#2d78ea; }
.drop.correct { background:#ecfff2; border-color:#58ae73; color:#277245; }
.drop.wrong { background:#fff0f0; border-color:#d77474; color:#9a3030; }
.drop.wide { min-width:150px; }
.drop.small { min-width:58px; }
.reason-box { margin-top:7px; }
.reason-head { display:flex; justify-content:space-between; align-items:center; padding:5px 9px; background:#edf3f9; font-size:12px; color:#344e6d; }
.reason-row { display:flex; align-items:center; flex-wrap:wrap; gap:6px; padding:6px 10px; border-top:1px solid #dde5ef; font-size:12px; }
.reason-no { width:22px; color:#0f66dc; font-weight:900; }
.compare-table table,.student-table,.experience-table { width:100%; border-collapse:collapse; table-layout:fixed; }
th,td { border:1px solid #b9cbe0; }
.compare-table th,.student-table th,.experience-table th { background:#edf3f8; padding:5px 7px; font-size:11px; text-align:left; }
.compare-table td { padding:7px 8px; font-size:11px; vertical-align:top; }
.type-list { color:#173d9e; }
.type-table { color:#2629a0; }
.type-diagram { color:#7f1ce0; }
.good { color:#0c8d62; margin-top:3px; font-weight:700; }
.practice-block { margin-top:9px; position:relative; }
.practice-title { padding:7px 9px 3px; font-size:16px; line-height:1.3; }
.blue-title { color:#11294c; } .green-title { color:#114c37; }
.practice-icon { display:inline-flex; width:22px; height:22px; border-radius:50%; color:#fff; align-items:center; justify-content:center; margin-right:5px; font-size:12px; }
.practice-icon.blue { background:#1767d7; } .practice-icon.green { background:#15936a; } .practice-icon.purple { background:#7a22ec; }
.practice-note { padding:3px 9px 4px; font-size:11px; color:#536b84; background:#f8fbfe; }
.note-right { position:absolute; top:36px; right:10px; font-size:11px; font-weight:900; }
.blue-note { color:#1265dc; } .green-note { color:#159168; }
.list-grid { display:grid; grid-template-columns:36px 1fr 1fr; border-top:1px solid #d8e1ec; padding:6px; gap:5px; background:#fbfdff; }
.cell,.cell-edit { min-height:28px; border:1px solid #b9cbe0; border-radius:4px; background:#fff; padding:5px 8px; font:inherit; font-size:11px; }
.numcell { border:0; background:transparent; color:#1c62d8; font-weight:900; text-align:center; }
.sample { background:#fbfdff; font-weight:700; }
.cell-edit { outline:none; width:100%; }
.cell-edit:focus { border-color:#2b79e7; box-shadow:0 0 0 2px #e2efff; }
.student-table th,.student-table td { text-align:center; }
.student-table td { padding:4px; font-size:11px; }
.student-table input,.experience-table input { width:100%; border:0; background:transparent; outline:none; text-align:center; font:inherit; color:#42566f; min-height:25px; }
.sheet-footer { display:flex; justify-content:space-between; align-items:center; gap:12px; color:#8093ac; font-size:11px; border-top:1px solid #cfd9e5; margin-top:16px; padding-top:7px; }
.footer-nav { border:0; background:transparent; color:#1765d5; font:inherit; font-weight:900; cursor:pointer; padding:0; }
.finish { color:#159168; font-weight:900; }
.activity-heading { margin:0 0 6px; font-size:17px; line-height:1.35; }
.activity-heading.space-top { margin-top:12px; }
.reading-box { padding:9px 11px; background:#f8fafc; }
.reading-box p { margin:0; font-size:13px; line-height:1.7; }
.diagram-box { margin-top:8px; border-color:#b8b6ff; background:linear-gradient(#fbfbff,#f7f8ff); padding:9px 10px 12px; }
.diagram-guide { text-align:center; color:#4f388a; font-size:12px; font-weight:900; }
.page2-bank { justify-content:center; align-items:center; margin-bottom:6px; }
.page2-label { color:#6b7890; font-size:10px; font-weight:700; }
.tree { padding:12px 6px 4px; }
.node-label { color:#68778d; font-size:10px; margin-bottom:3px; font-weight:800; letter-spacing:-.1px; }
.tree-level { display:flex; justify-content:center; }
.top-level { position:relative; }
.hierarchy-node { width:min(330px,90%); border:2px solid #7da8e5; border-radius:12px; background:#fff; padding:8px 10px 10px; text-align:center; box-shadow:0 2px 0 rgba(73,116,173,.06); }
.root-hierarchy { border-color:#4f91df; background:#f8fbff; }
.hierarchy-drop { width:100%; min-height:44px; border:1px dashed #96abc4; background:#fff; font-size:13px; color:#27476d; }
.hierarchy-main-line { width:3px; height:24px; background:#9eb6d4; margin:0 auto; position:relative; }
.hierarchy-main-line::before { content:""; position:absolute; left:50%; top:0; width:min(72%,620px); height:2px; background:#9eb6d4; transform:translateX(-50%); }
.branch-level { display:grid; grid-template-columns:1fr 1fr; gap:26px; position:relative; max-width:900px; margin:0 auto; }
.hierarchy-branch { position:relative; padding-top:14px; }
.hierarchy-branch::before { content:""; position:absolute; top:0; left:50%; width:2px; height:14px; background:#9eb6d4; }
.hierarchy-node.purple-hierarchy { border-color:#b59de9; background:#fcfaff; }
.child-line { height:18px; width:2px; background:#9eb6d4; margin:0 auto; }
.purple-child-line { background:#baa0e7; }
.child-grid { position:relative; display:grid; gap:8px; }
.child-grid::before { content:""; position:absolute; top:0; left:12%; right:12%; height:2px; background:#b7c6d8; }
.two-child { grid-template-columns:1fr 1fr; }
.three-child { grid-template-columns:repeat(3,1fr); }
.hierarchy-leaf { margin-top:11px; min-width:0; border:1px solid #c6d5e5; background:#fff; border-radius:9px; padding:6px; text-align:center; box-shadow:0 1px 0 rgba(50,80,110,.04); }
.purple-leaf { border-color:#dacff0; }
.leaf-drop { width:100%; min-height:46px; border:1px dashed #acbdd0; background:#fbfdff; color:#3b526b; font-size:11px; }
.yellow-box { margin-top:6px; background:#fffdf1; border-color:#f0c83f; padding:9px 11px; font-size:12px; line-height:1.7; }
.structure-choice { margin-top:6px; padding:7px 9px; background:#eef4f9; display:flex; justify-content:space-between; align-items:center; gap:10px; }
.choice-buttons { display:flex; gap:5px; flex-wrap:wrap; }
.choice-buttons button,.primary-btn,.secondary-btn { border-radius:5px; padding:6px 9px; font:inherit; font-size:11px; font-weight:900; cursor:pointer; }
.choice-buttons button { border:1px solid #b8c8dc; background:#fff; color:#274260; }
.choice-buttons button.selected { background:#1b68db; color:#fff; border-color:#1b68db; }
.structure-output { margin-top:6px; padding:7px 9px 8px; }
.output-title { font-size:12px; font-weight:800; margin-bottom:5px; }
.experience-table th,.experience-table td { text-align:center; }
.experience-table td { padding:4px; height:30px; font-size:11px; }
.example-month { color:#2459bb; font-weight:900; }
.check-box { margin-top:9px; background:#f5f8fc; padding:9px 11px; }
.check-title { font-size:15px; font-weight:900; margin-bottom:5px; }
.check-title span { color:#55708d; font-size:11px; font-weight:700; margin-left:4px; }
.check-title small { float:right; color:#61758d; font-size:10px; font-weight:600; }
.check-box label { display:block; margin:5px 0; font-size:12px; }
.check-box input { width:17px; height:17px; vertical-align:-3px; margin-right:4px; }
.result-area { display:flex; justify-content:flex-end; align-items:center; gap:6px; margin-top:9px; min-height:36px; }
.score-text { margin-right:auto; color:#1b5cae; font-weight:900; font-size:12px; }
.primary-btn { color:#fff; background:#1e68dc; border:1px solid #1e68dc; }
.secondary-btn { background:#fff; color:#48627f; border:1px solid #b9c9dc; }

.dynamic-area { padding:6px; background:#fbfdff; border-top:1px solid #d8e1ec; }
.dynamic-list-row { display:grid; grid-template-columns:36px 1fr 1fr 34px; gap:5px; align-items:center; margin-bottom:5px; }
.dynamic-list-row:last-child { margin-bottom:0; }
.row-num { color:#1767d7; font-weight:900; text-align:center; }
.cell-edit { width:100%; min-height:30px; border:1px solid #b9cbe0; border-radius:4px; background:#fff; padding:5px 8px; font:inherit; font-size:11px; outline:none; }
.cell-edit:focus { border-color:#2b79e7; box-shadow:0 0 0 2px #e2efff; }
.sample-cell { background:#f7fbff; border:1px solid #d2dfec; border-radius:4px; padding:6px 8px; font-size:11px; font-weight:700; }
.dynamic-table-wrap { overflow-x:auto; border-top:1px solid #d8e1ec; }
.student-table .delete-col { width:44px; }
.student-table input { min-height:30px; }
.delete-btn { border:0; background:transparent; color:#b56b6b; cursor:pointer; font-size:12px; font-weight:900; }
.add-row-btn { margin:6px 8px 8px; border:1px solid #a8c3e4; background:#f4f8fd; color:#1962c9; border-radius:5px; padding:5px 9px; font:inherit; font-size:11px; font-weight:900; cursor:pointer; }
.green-add { color:#168760; border-color:#acd6c4; background:#f3fbf7; }
.experience-editor { padding:7px; }
.editor-note { color:#60748e; font-size:10px; margin-bottom:6px; }
.plan-list { display:flex; flex-direction:column; gap:6px; }
.plan-list-row { display:grid; grid-template-columns:34px 65px 1fr 120px 1fr 34px; gap:5px; align-items:center; }
.plan-input { width:100%; min-height:30px; border:1px solid #b9cbe0; border-radius:4px; background:#fff; padding:5px 7px; outline:none; font:inherit; font-size:11px; }
.plan-table { width:100%; border-collapse:collapse; table-layout:fixed; }
.plan-table th,.plan-table td { border:1px solid #bfd0e1; padding:4px; }
.plan-table th { background:#edf3f8; color:#36516e; font-size:11px; }
.plan-table input { width:100%; border:0; min-height:28px; outline:none; text-align:center; font:inherit; font-size:11px; background:transparent; }
.plan-table .sample-row { background:#f7fbff; }
.plan-diagram { display:flex; flex-direction:column; gap:8px; }
.plan-diagram-row { display:grid; grid-template-columns:55px 16px 1fr 34px; align-items:center; gap:6px; }
.plan-month-node { border:2px solid #8ab1eb; background:#f5f9ff; border-radius:8px; padding:7px 4px; text-align:center; font-size:11px; font-weight:900; color:#1c5fb8; }
.plan-line { height:2px; background:#9bb4d1; position:relative; }
.plan-line::after { content:""; position:absolute; right:-1px; top:-3px; width:0; height:0; border-left:7px solid #9bb4d1; border-top:4px solid transparent; border-bottom:4px solid transparent; }
.plan-node-card { display:grid; grid-template-columns:1fr 110px 1fr; gap:5px; border:1px solid #cbd7e4; border-radius:7px; background:#fff; padding:5px; }
.plan-node-card input { width:100%; min-height:30px; border:1px solid #d5dfeb; border-radius:4px; outline:none; padding:5px; font:inherit; font-size:10px; }
.plan-node-card input:focus { border-color:#7aa9e9; box-shadow:0 0 0 2px #e5f0ff; }

.simple-list-view,.simple-diagram-view { margin-top:5px; padding:8px; border:1px solid #d4deea; border-radius:5px; background:#fbfdff; font-size:11px; line-height:1.8; }
.simple-diagram-view .diag-line { display:grid; grid-template-columns:60px 1fr 80px; gap:6px; padding:5px 0; border-bottom:1px dashed #d5dfeb; }
.simple-diagram-view .diag-line:last-child { border-bottom:0; }
.simple-diagram-view em { font-style:normal; text-align:center; color:#2459bb; }
@media (max-width:760px) {
  #worksheet-root { font-size:12px; padding:5px 2px 20px; }
  .sheet { min-height:auto; padding:18px 12px 16px; }
  .sheet-header { flex-direction:column; }
  h1 { font-size:20px; }
  .student-card { white-space:normal; }
  .reason-row { flex-wrap:wrap; }
  .branch-level { gap:10px; }
  .hierarchy-node { width:92%; }
  .three-child { grid-template-columns:1fr; }
  .three-child::before { display:none; }
  .two-child { grid-template-columns:1fr; }
  .two-child::before { display:none; }
  .structure-choice { align-items:flex-start; flex-direction:column; }
  .note-right { position:static; padding:0 9px 4px; }
  .sheet-footer { flex-wrap:wrap; }
  .student-table { min-width:720px; }
  .student-table { display:block; overflow-x:auto; }
}
'''

JS = r'''
export default function(component) {
  const { parentElement, setStateValue, setTriggerValue, data } = component;
  const root = parentElement.querySelector('#worksheet-root');
  if (!root) return () => {};

  const front = root.querySelector('.sheet-front');
  const back = root.querySelector('.sheet-back');

  const answers = {
    "1":"데이터", "2":"특성", "3":"정리 및 배열", "4":"통일된 모양",
    "5":"쉽게 찾을", "6":"내용 요소 간의 관계", "7":"효율적으로 관리",
    "8":"기준", "9":"세로줄과 가로줄", "10":"점, 선, 도형",
    "11":"소프트웨어 개발 전문가", "12":"시스템 SW 개발자", "13":"운영체제 프로그래머",
    "14":"임베디드 프로그래머", "15":"응용 SW 개발자", "16":"응용 SW 프로그래머",
    "17":"네트워크 프로그래머", "18":"컴퓨터 및 모바일 게임 프로그래머"
  };

  const words = [
    '데이터','특성','정리 및 배열','통일된 모양','쉽게 찾을',
    '내용 요소 간의 관계','효율적으로 관리','기준','세로줄과 가로줄','점, 선, 도형'
  ];
  const page2Words = ['네트워크 프로그래머','소프트웨어 개발 전문가','임베디드 프로그래머','응용 SW 프로그래머','시스템 SW 개발자','컴퓨터 및 모바일 게임 프로그래머','운영체제 프로그래머','응용 SW 개발자'];
  const initial = data?.initial || {};
  const clone = v => JSON.parse(JSON.stringify(v));
  const esc = (v) => String(v ?? '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
  const norm = v => String(v ?? '').trim().toLowerCase().replace(/\s+/g,'');

  let activity1Rows = Array.isArray(initial.listRows) && initial.listRows.length ? clone(initial.listRows) : [['아침 환기 및 창문 열기 (샘플)','매일 등교 직후 8:30 창문 개방']];
  let activity2Rows = Array.isArray(initial.tableRows) && initial.tableRows.length ? clone(initial.tableRows) : [['김민준(샘플)','03월 15일','축구, 코딩','1번 / 체육부장']];
  let experienceListRows = Array.isArray(initial.experienceListRows) && initial.experienceListRows.length ? clone(initial.experienceListRows) : [['4월','경복궁, 창덕궁, 종묘','지하철 3호선','봄꽃 감상 및 역사 탐방']];
  let experienceTableRows = Array.isArray(initial.experienceTableRows) && initial.experienceTableRows.length ? clone(initial.experienceTableRows) : [['4월 (예시)','경복궁, 창덕궁, 종묘','지하철 3호선','봄꽃 감상 및 역사 탐방']];
  let experienceDiagramRows = Array.isArray(initial.experienceDiagramRows) && initial.experienceDiagramRows.length ? clone(initial.experienceDiagramRows) : [['4월','경복궁, 창덕궁, 종묘','지하철 3호선','봄꽃 감상 및 역사 탐방']];
  let currentPage = Number(initial.page || 1);
  let currentStructure = initial.structure || '표';

  function addWord(parent, text) {
    const span = document.createElement('span');
    span.className = 'word'; span.textContent = text; span.draggable = true;
    span.addEventListener('dragstart', e => { e.dataTransfer.setData('text/plain', text); e.dataTransfer.effectAllowed='copy'; });
    span.addEventListener('click', () => {
      const active = root.querySelector('.drop:focus') || root.querySelector('.drop.selected-drop');
      if (active) { active.textContent=text; updateBlankStatus(active,true); sync(); }
    });
    parent.appendChild(span);
  }

  function updateBlankStatus(el, showEmptyAsWrong=true) {
    const val=el.textContent.trim();
    el.classList.remove('correct','wrong');
    if (!val) { if (showEmptyAsWrong) el.classList.add('wrong'); return false; }
    const ok=norm(val)===norm(answers[el.dataset.id]);
    el.classList.add(ok?'correct':'wrong');
    return ok;
  }

  function bindDrop(el) {
    if (el.dataset.bound) return;
    el.dataset.bound='1';
    el.addEventListener('focus',()=>{ root.querySelectorAll('.selected-drop').forEach(x=>x.classList.remove('selected-drop')); el.classList.add('selected-drop'); });
    el.addEventListener('click',()=>{ root.querySelectorAll('.selected-drop').forEach(x=>x.classList.remove('selected-drop')); el.classList.add('selected-drop'); });
    el.addEventListener('dragover',e=>{ e.preventDefault(); el.classList.add('dragover'); });
    el.addEventListener('dragleave',()=>el.classList.remove('dragover'));
    el.addEventListener('drop',e=>{ e.preventDefault(); el.classList.remove('dragover'); const text=e.dataTransfer.getData('text/plain'); if(text){el.textContent=text; updateBlankStatus(el,true); sync();} });
    el.addEventListener('input',()=>{ updateBlankStatus(el,true); sync(); });
    el.addEventListener('keydown',e=>{if(e.key==='Enter') e.preventDefault();});
  }

  function value(id) { const el=root.querySelector('#'+id); if(!el) return ''; if(el.type==='checkbox') return !!el.checked; return el.isContentEditable?el.textContent.trim():(el.value??''); }

  function renderActivity1() {
    const area=root.querySelector('#activity1ListArea'); if(!area) return; area.innerHTML='';
    activity1Rows.forEach((row,index)=>{
      const wrap=document.createElement('div'); wrap.className='dynamic-list-row';
      const sample=index===0;
      wrap.innerHTML=`<div class="row-num">${index+1}.</div>${sample?`<div class="sample-cell">${esc(row[0])}</div><div class="sample-cell">${esc(row[1])}</div>`:`<input class="cell-edit list-a" value="${esc(row[0])}"><input class="cell-edit list-b" value="${esc(row[1])}">`}<button class="delete-btn" data-list-delete="${index}">${sample?'—':'🗑'}</button>`;
      area.appendChild(wrap);
      if(!sample){ wrap.querySelector('.list-a').addEventListener('input',e=>{activity1Rows[index][0]=e.target.value;sync();}); wrap.querySelector('.list-b').addEventListener('input',e=>{activity1Rows[index][1]=e.target.value;sync();}); }
    });
    area.querySelectorAll('[data-list-delete]').forEach(btn=>btn.addEventListener('click',()=>{const i=Number(btn.dataset.listDelete);if(i===0)return;activity1Rows.splice(i,1);renderActivity1();sync();}));
  }

  function renderActivity2() {
    const body=root.querySelector('#activity2TableBody'); if(!body) return; body.innerHTML='';
    activity2Rows.forEach((row,index)=>{
      const tr=document.createElement('tr');
      if(index===0){ tr.innerHTML=`<td>1</td><td><b>${esc(row[0]||'김민준(샘플)')}</b></td><td>${esc(row[1]||'03월 15일')}</td><td>${esc(row[2]||'축구, 코딩')}</td><td>${esc(row[3]||'1번 / 체육부장')}</td><td>—</td>`; }
      else { tr.innerHTML=`<td>${index+1}</td><td><input class=a2-name value="${esc(row[0])}"></td><td><input class=a2-birth value="${esc(row[1])}"></td><td><input class=a2-hobby value="${esc(row[2])}"></td><td><input class=a2-memo value="${esc(row[3])}"></td><td><button class=delete-btn data-table-delete="${index}">🗑</button></td>`;
        ['a2-name','a2-birth','a2-hobby','a2-memo'].forEach((cls,col)=>tr.querySelector('.'+cls).addEventListener('input',e=>{activity2Rows[index][col]=e.target.value;sync();})); }
      body.appendChild(tr);
    });
    body.querySelectorAll('[data-table-delete]').forEach(btn=>btn.addEventListener('click',()=>{const i=Number(btn.dataset.tableDelete);if(i===0)return;activity2Rows.splice(i,1);renderActivity2();sync();}));
  }

  function editableInput(value, cls, idx, col) { return `<input class="${cls}" data-idx="${idx}" data-col="${col}" value="${esc(value||'')}">`; }
  function bindModelInputs(scope,model){
    scope.querySelectorAll('input[data-idx][data-col]').forEach(el=>el.addEventListener('input',e=>{const i=Number(e.target.dataset.idx),c=Number(e.target.dataset.col);model[i][c]=e.target.value;sync();}));
    scope.querySelectorAll('[data-model-delete]').forEach(btn=>btn.addEventListener('click',()=>{const i=Number(btn.dataset.modelDelete);if(i===0)return;model.splice(i,1);renderStructure(currentStructure);sync();}));
  }

  function renderStructure(type) {
    currentStructure=type;
    const output=root.querySelector('#structureOutput'), editor=root.querySelector('#experienceEditor'), title=output.querySelector('.output-title');
    editor.innerHTML='';
    if(type==='목록'){
      title.textContent='[ 목록(List)으로 구조화한 체험학습 계획 ]';
      const wrap=document.createElement('div');wrap.className='plan-list';
      wrap.innerHTML='<div class="editor-note">1번 항목은 샘플입니다. 2번부터 학생이 직접 입력하고 필요한 만큼 항목을 추가하세요.</div>';
      experienceListRows.forEach((row,index)=>{const r=document.createElement('div');r.className='plan-list-row';
        if(index===0) r.innerHTML=`<div class=row-num>1.</div><div class=sample-cell>${esc(row[0])}</div><div class=sample-cell>${esc(row[1])}</div><div class=sample-cell>${esc(row[2])}</div><div class=sample-cell>${esc(row[3])}</div><button class=delete-btn>—</button>`;
        else r.innerHTML=`<div class=row-num>${index+1}.</div>${editableInput(row[0],'plan-input',index,0)}${editableInput(row[1],'plan-input',index,1)}${editableInput(row[2],'plan-input',index,2)}${editableInput(row[3],'plan-input',index,3)}<button class=delete-btn data-model-delete="${index}">🗑</button>`;
        wrap.appendChild(r);});
      const add=document.createElement('button');add.className='add-row-btn';add.textContent='＋ 목록 항목 추가';wrap.appendChild(add);editor.appendChild(wrap);bindModelInputs(editor,experienceListRows);add.addEventListener('click',()=>{experienceListRows.push(['','','','']);renderStructure('목록');sync();});
    } else if(type==='표'){
      title.textContent='[ 표(Table)로 구조화한 체험학습 계획 ]';
      const wrap=document.createElement('div');wrap.innerHTML='<div class=editor-note>1번 행은 샘플입니다. 2번부터 학생이 직접 채우고 필요한 만큼 행을 추가하세요.</div>';
      const table=document.createElement('table');table.className='plan-table';table.innerHTML='<thead><tr><th>일정(월)</th><th>방문 목적지(장소)</th><th>이용 교통수단</th><th>체험 목적 및 세부 내용</th><th class=delete-col>삭제</th></tr></thead><tbody></tbody>';
      const body=table.querySelector('tbody');
      experienceTableRows.forEach((row,index)=>{const tr=document.createElement('tr');if(index===0){tr.className='sample-row';tr.innerHTML=`<td>${esc(row[0])}</td><td>${esc(row[1])}</td><td>${esc(row[2])}</td><td>${esc(row[3])}</td><td>—</td>`;}else{tr.innerHTML=`<td>${editableInput(row[0],'plan-table-input',index,0)}</td><td>${editableInput(row[1],'plan-table-input',index,1)}</td><td>${editableInput(row[2],'plan-table-input',index,2)}</td><td>${editableInput(row[3],'plan-table-input',index,3)}</td><td><button class=delete-btn data-model-delete="${index}">🗑</button></td>`;}body.appendChild(tr);});
      wrap.appendChild(table);const add=document.createElement('button');add.className='add-row-btn green-add';add.textContent='＋ 표 행 추가';wrap.appendChild(add);editor.appendChild(wrap);bindModelInputs(editor,experienceTableRows);add.addEventListener('click',()=>{experienceTableRows.push(['','','','']);renderStructure('표');sync();});
    } else {
      title.textContent='[ 다이어그램(노선망)으로 구조화한 체험학습 계획 ]';
      const wrap=document.createElement('div');wrap.className='plan-diagram';const note=document.createElement('div');note.className='editor-note';note.textContent='1번은 샘플입니다. 2번부터 학생이 직접 노드를 만들고 필요한 만큼 추가하세요.';wrap.appendChild(note);
      experienceDiagramRows.forEach((row,index)=>{const r=document.createElement('div');r.className='plan-diagram-row';
        r.innerHTML=`<div class=plan-month-node>${index===0?esc(row[0]):editableInput(row[0],'plan-input',index,0)}</div><div class=plan-line></div><div class=plan-node-card>${index===0?`<div class=sample-cell>${esc(row[1])}</div><div class=sample-cell>${esc(row[2])}</div><div class=sample-cell>${esc(row[3])}</div>`:`${editableInput(row[1],'plan-input',index,1)}${editableInput(row[2],'plan-input',index,2)}${editableInput(row[3],'plan-input',index,3)}`}</div><button class=delete-btn data-model-delete="${index}">${index===0?'—':'🗑'}</button>`;
        wrap.appendChild(r);});
      const add=document.createElement('button');add.className='add-row-btn';add.textContent='＋ 다이어그램 항목 추가';wrap.appendChild(add);editor.appendChild(wrap);bindModelInputs(editor,experienceDiagramRows);add.addEventListener('click',()=>{experienceDiagramRows.push(['','','','']);renderStructure('다이어그램');sync();});
    }
  }

  function collect(){
    const blanks={};root.querySelectorAll('.drop[data-id]').forEach(el=>blanks[el.dataset.id]=el.textContent.trim());
    return {grade:'1',className:value('className'),number:value('studentNo'),name:value('studentName'),blanks,
      listRows:clone(activity1Rows),tableRows:clone(activity2Rows),experienceListRows:clone(experienceListRows),experienceTableRows:clone(experienceTableRows),experienceDiagramRows:clone(experienceDiagramRows),experienceRows:clone(experienceTableRows),structure:currentStructure,
      selfChecks:{q1:value('check1'),q2:value('check2'),q3:value('check3')},page:currentPage,score:0,timestamp:new Date().toISOString()};
  }
  function sync(){setStateValue('payload',collect());}
  function setPage(page){currentPage=page;front.classList.toggle('hidden',page!==1);back.classList.toggle('hidden',page!==2);setStateValue('page',page);window.scrollTo({top:0,behavior:'smooth'});sync();}

  const bank=root.querySelector('#wordBank');if(bank&&!bank.dataset.ready){words.forEach(w=>addWord(bank,w));bank.dataset.ready='1';}
  const bank2=root.querySelector('#page2Bank');if(bank2&&!bank2.dataset.ready){page2Words.forEach(w=>addWord(bank2,w));bank2.dataset.ready='1';}
  root.querySelectorAll('.drop').forEach(bindDrop);
  root.querySelectorAll('input[type="checkbox"]').forEach(el=>el.addEventListener('change',sync));

  renderActivity1();renderActivity2();renderStructure(currentStructure);

  if(initial.className!==undefined)root.querySelector('#className').value=initial.className||'1';
  if(initial.number!==undefined)root.querySelector('#studentNo').value=initial.number||'';
  if(initial.name!==undefined)root.querySelector('#studentName').value=initial.name||'';
  const initialBlanks=initial.blanks||{};
  root.querySelectorAll('.drop[data-id]').forEach(el=>{const v=initialBlanks[el.dataset.id];if(v)el.textContent=v;updateBlankStatus(el,true);});
  if(initial.selfChecks){root.querySelector('#check1').checked=!!initial.selfChecks.q1;root.querySelector('#check2').checked=!!initial.selfChecks.q2;root.querySelector('#check3').checked=!!initial.selfChecks.q3;}

  root.querySelectorAll('[data-go]').forEach(btn=>btn.addEventListener('click',()=>setPage(Number(btn.dataset.go))));
  root.querySelectorAll('.choice-buttons button').forEach(btn=>btn.addEventListener('click',()=>{root.querySelectorAll('.choice-buttons button').forEach(b=>b.classList.remove('selected'));btn.classList.add('selected');renderStructure(btn.dataset.structure);sync();}));
  root.querySelector(`.choice-buttons button[data-structure="${currentStructure}"]`)?.classList.add('selected');
  root.querySelector('#addListBtn')?.addEventListener('click',()=>{activity1Rows.push(['','']);renderActivity1();sync();});
  root.querySelector('#addTableBtn')?.addEventListener('click',()=>{activity2Rows.push(['','','','']);renderActivity2();sync();});

  root.querySelector('#gradeBtn').addEventListener('click',()=>{
    let score=0;root.querySelectorAll('.drop[data-id]').forEach(el=>{if(updateBlankStatus(el,true))score++;});
    const payload=collect();payload.score=score;setStateValue('payload',payload);setTriggerValue('save',payload);
    root.querySelector('#scoreText').textContent=`빈칸 ${score} / ${Object.keys(answers).length} 정답 · 맞으면 초록, 틀리거나 비어 있으면 빨간색으로 표시됩니다.`;
  });
  root.querySelector('#clearBtn').addEventListener('click',()=>{
    root.querySelectorAll('.drop').forEach(el=>{el.textContent='';el.classList.remove('correct','dragover','selected-drop');el.classList.add('wrong');});
    root.querySelectorAll('input').forEach(el=>{if(el.id==='className')el.value='1';else if(el.type==='checkbox')el.checked=false;else el.value='';});
    activity1Rows=[['아침 환기 및 창문 열기 (샘플)','매일 등교 직후 8:30 창문 개방']];activity2Rows=[['김민준(샘플)','03월 15일','축구, 코딩','1번 / 체육부장']];
    experienceListRows=[['4월','경복궁, 창덕궁, 종묘','지하철 3호선','봄꽃 감상 및 역사 탐방']];experienceTableRows=[['4월 (예시)','경복궁, 창덕궁, 종묘','지하철 3호선','봄꽃 감상 및 역사 탐방']];experienceDiagramRows=[['4월','경복궁, 창덕궁, 종묘','지하철 3호선','봄꽃 감상 및 역사 탐방']];currentStructure='표';
    renderActivity1();renderActivity2();renderStructure('표');root.querySelectorAll('.choice-buttons button').forEach(b=>b.classList.remove('selected'));root.querySelector('.choice-buttons button[data-structure="표"]')?.classList.add('selected');root.querySelector('#scoreText').textContent='';sync();
  });

  setPage(currentPage);sync();return ()=>{};
}
'''

# V2는 iframe 없이 Streamlit 본문에 바로 붙고 JS도 실행되므로,
# 이전 v1 iframe에서 빈 화면처럼 보이던 문제를 피합니다.
worksheet_component = st.components.v2.component(
    "data_structure_worksheet_v2",
    html=HTML,
    css=CSS,
    js=JS,
    isolate_styles=True,
)

if "worksheet_data" not in st.session_state:
    st.session_state.worksheet_data = {
        "grade":"1", "className":"1", "number":"", "name":"", "blanks":{},
        "listRows":[["아침 환기 및 창문 열기 (샘플)","매일 등교 직후 8:30 창문 개방"]],
        "tableRows":[["김민준(샘플)","03월 15일","축구, 코딩","1번 / 체육부장"]],
        "experienceListRows":[["4월","경복궁, 창덕궁, 종묘","지하철 3호선","봄꽃 감상 및 역사 탐방"]],
        "experienceTableRows":[["4월 (예시)","경복궁, 창덕궁, 종묘","지하철 3호선","봄꽃 감상 및 역사 탐방"]],
        "experienceDiagramRows":[["4월","경복궁, 창덕궁, 종묘","지하철 3호선","봄꽃 감상 및 역사 탐방"]],
        "experienceRows":[], "structure":"표",
        "selfChecks":{"q1":False,"q2":False,"q3":False}, "page":1, "score":0
    }

# V2의 default에는 "상태(state)"만 등록할 수 있습니다.
# save는 JS에서 setTriggerValue()로 보내는 "trigger"이므로
# default에 넣거나 on_save_change를 지정하면 BidiComponentInvalidDefaultKeyError가 발생합니다.
result = worksheet_component(
    key="worksheet",
    data={"initial": st.session_state.worksheet_data},
    default={"payload": st.session_state.worksheet_data},
    on_payload_change=lambda: None,
    width="stretch",
    height="content",
)

# 자동채점 버튼의 trigger가 Python으로 들어오면 저장합니다.
save_payload = getattr(result, "save", None)
if save_payload:
    st.session_state.worksheet_data = save_payload
    ok, message = save_to_google_sheet(save_payload)
    if ok:
        st.toast(message, icon="✅")
    else:
        st.toast("채점은 완료되었습니다. Google Sheets는 Secrets 설정 후 연결됩니다.", icon="ℹ️")
