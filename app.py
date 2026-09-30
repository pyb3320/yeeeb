import streamlit as st
import streamlit.components.v1 as components
from pathlib import Path
from datetime import datetime

st.set_page_config(
    page_title="통계와 데이터 - 데이터의 구조화",
    page_icon="📊",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
.stApp { background:#ffffff; }
.block-container { max-width:900px; padding:1rem 1rem 2rem; }
header[data-testid="stHeader"] { background:transparent; }
div[data-testid="stToolbar"] { display:none; }
</style>
""", unsafe_allow_html=True)

COMPONENT_HTML = COMPONENT_HTML = '<!doctype html>\n<html lang="ko">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1">\n<script src="https://unpkg.com/streamlit-component-lib/dist/index.js"></script>\n<style>\n*{box-sizing:border-box}\nbody{margin:0;background:white;font-family:Arial,"Noto Sans KR",sans-serif;color:#172033;font-size:13px}\n#app{width:100%;padding:10px 12px 18px}\n.topline{display:flex;justify-content:space-between;align-items:flex-start;gap:10px}\n.badge{display:inline-block;color:#1769aa;background:#f3f8ff;border:1px solid #9cc4ef;border-radius:3px;padding:3px 7px;font-size:10px;font-weight:700}\nh1{font-size:18px;margin:5px 0 8px;font-weight:800}\n.student{border:1px solid #b8cce5;background:#f8fbff;border-radius:4px;padding:5px 8px;font-size:11px;white-space:nowrap}\n.student input{width:25px;border:0;border-bottom:1px solid #9fb3cc;background:transparent;text-align:center;outline:0}\n.student .name{width:60px}\n.notice{border:1px solid #b6cde8;background:#f7fbff;border-radius:7px;padding:8px 10px;color:#17528b;font-size:10px;line-height:1.55;margin-bottom:8px}\n.words{margin-top:4px}\n.word{display:inline-block;padding:2px 6px;margin:2px;border:1px solid #70a7df;border-radius:3px;background:white;color:#125da0;font-weight:700;cursor:grab;user-select:none}\n.section-title{font-weight:800;font-size:15px;margin:8px 0 4px;color:#15263c}\n.num{display:inline-flex;width:17px;height:17px;border-radius:50%;background:#1769e8;color:white;align-items:center;justify-content:center;font-size:10px;margin-right:5px}\n.box{border:1px solid #86b8f2;border-radius:6px;background:#f8fbff;padding:8px 10px;margin-bottom:7px;line-height:1.6}\n.drop{display:inline-block;min-width:42px;height:24px;vertical-align:middle;border:1px solid #9db7d4;border-radius:3px;background:white;padding:2px 7px;margin:0 2px;color:#2f4966;outline:0}\n.drop:focus{border-color:#2979e8;box-shadow:0 0 0 2px #dceaff}\n.drop.dragover{background:#eaf3ff;border-color:#2979e8}\n.grid{border:1px solid #b7cce2;border-radius:6px;overflow:hidden}\n.grid table{width:100%;border-collapse:collapse;table-layout:fixed}\n.grid th,.grid td{border:1px solid #b7cce2;padding:6px 7px;vertical-align:top;font-size:10px;line-height:1.45}\n.grid th{background:#eef5fb;text-align:left;font-weight:800}\n.grid th:nth-child(1){width:20%}.grid th:nth-child(2){width:53%}.grid th:nth-child(3){width:27%}\n.mini-title{font-weight:800;color:#185ea9;margin-bottom:2px}\n.bullet{color:#2774c9;font-weight:800}\n.practice{border:1px solid #c2d4e9;border-radius:6px;margin-top:9px;overflow:hidden}\n.practice-head{background:#f2f7fc;padding:6px 8px;font-weight:800;color:#173c67}\n.row{display:grid;grid-template-columns:25px 1fr 1fr 25px;gap:6px;padding:5px 7px;border-top:1px solid #d7e2ef;align-items:center}\n.rownum{font-weight:700;color:#1c5da2;text-align:center}\n.row input{height:28px;border:1px solid #b7c9df;border-radius:4px;padding:4px 8px;font-size:11px;outline:0;width:100%}\n.row input:focus{border-color:#2979e8;box-shadow:0 0 0 2px #e5f0ff}\n.del{color:#b3bdc9;cursor:pointer;text-align:center}\nbutton{border:1px solid #70a7df;background:#fff;color:#1769aa;border-radius:4px;padding:4px 8px;cursor:pointer;font-size:10px}\nbutton:hover{background:#edf5ff}\n.actions{display:flex;justify-content:flex-end;gap:6px;margin-top:9px}\n#result{margin-top:8px;padding:8px;border-radius:6px;background:#f4f8fd;border:1px solid #c6d9ee;font-weight:700;display:none}\n@media(max-width:650px){\n body{font-size:12px}.topline{display:block}.student{margin-top:5px;width:max-content}\n .grid th:nth-child(3),.grid td:nth-child(3){display:none}\n .row{grid-template-columns:22px 1fr 1fr 20px}\n}\n</style>\n</head>\n<body>\n<div id="app">\n  <div class="topline">\n    <div>\n      <span class="badge">중학교 정보과 활동지</span>\n      <h1>통계와 데이터 - 데이터의 구조화 (목록형과 표 만들기)</h1>\n    </div>\n    <div class="student">\n      1학년 <input id="cls" value="1"> 반 <input id="num" value=""> 번&nbsp;\n      이름: <input id="name" class="name" value="">\n    </div>\n  </div>\n\n  <div class="notice">\n    💡 <b>【빈칸 넣기 단어 보관함】</b> 아래 단어를 빈칸으로 드래그하거나 클릭하여 채워보세요!\n    <span style="float:right;color:#67819c">※맞으면 연두색, 틀리면 빨간색 등이 표시됩니다.</span>\n    <div class="words" id="words"></div>\n  </div>\n\n  <div class="section-title"><span class="num">1</span>데이터를 왜 구조화해야 할까?</div>\n  <div class="box">\n    <b>♧ [교과서 핵심 개념] 데이터 구조화의 정의</b><br>\n    전달하려고 하는 <span class="drop" data-answer="데이터" contenteditable="true"></span>\n    의 내용 요소들을 <span class="drop" data-answer="특성" contenteditable="true"></span>\n    에 맞게 <span class="drop" data-answer="정리 및 배열" contenteditable="true"></span>\n    하여 <span class="drop" data-answer="통일된 모양" contenteditable="true"></span>\n    으로 표현하는 것을 말한다.\n  </div>\n\n  <div class="box">\n    <b>데이터 구조화를 하는 주요 이유 4가지</b>\n    <div style="margin-top:4px">\n      ① 원하는 데이터를 <span class="drop" data-answer="쉽게 찾을" contenteditable="true"></span>\n      수 있다. (예: 학생으로 구조화한 학생 검색, 도서관 장서 찾기)<br>\n      ② <span class="drop" data-answer="내용 요소 간의 관계" contenteditable="true"></span>\n      를 쉽게 이해할 수 있다. (예: 가족 가계도, 회사 조직도)<br>\n      ③ 빠지거나 잘못된 데이터(오류 및 결측치)를 쉽게 파악할 수 있다. (예: 시간표 중복·누락 확인)<br>\n      ④ 데이터를 <span class="drop" data-answer="효율적으로 관리" contenteditable="true"></span>\n      할 수 있으며, 분석하여 더 나은 의사 결정을 내릴 수 있다.\n    </div>\n  </div>\n\n  <div class="section-title"><span class="num">2</span>데이터는 어떤 방법으로 구조화할 수 있을까? (3대 구조 비교)</div>\n  <div class="grid">\n    <table>\n      <thead><tr><th>구조 형태</th><th>특징 및 구조화 원리</th><th>대표적인 실생활 예</th></tr></thead>\n      <tbody>\n      <tr>\n        <td>☷ <b>1. 목록 (List)</b></td>\n        <td><div class="mini-title">· 인정 및 구조화 원리</div>\n          <span class="drop" data-answer="기준" contenteditable="true"></span>\n          에 맞추어 데이터를 순서대로 나열한 구조<br>\n          <span class="bullet">· 장점:</span> 구조가 단순하고 일관성이 있어 작성이 빠름</td>\n        <td>건물의 층별 안내, 시간별 일정표, 요리 순서 (레시피)</td>\n      </tr>\n      <tr>\n        <td>▦ <b>2. 표 (Table)</b></td>\n        <td>· 서로 다른 두 기준인 <span class="drop" data-answer="세로줄과 가로줄" contenteditable="true"></span>\n          을 행과 열로 나누어 격자로 배열<br>\n          <span class="bullet">· 장점:</span> 데이터 간의 비교와 수치, 통계 계산이 매우 쉬움</td>\n        <td>학급 시간표, 성적표, 응급기관 서비스 시간표</td>\n      </tr>\n      <tr>\n        <td>⌘ <b>3. 다이어그램</b></td>\n        <td>· <span class="drop" data-answer="점, 선, 도형" contenteditable="true"></span>을 사용하여 관계를 그림으로 시각화<br>\n          <span class="bullet">· 형태:</span> 계층형(가계도), 네트워크형(노선도), 그래프·차트형(비교)</td>\n        <td>가족 가계도, 지하철 노선도, 과목별 성적 막대그래프</td>\n      </tr>\n      </tbody>\n    </table>\n  </div>\n\n  <div class="practice">\n    <div class="practice-head">③ [활동 1] 목록(List)형 데이터 만들기: 우리 반 학급 1인 1역할 정리\n      <button id="add1" style="float:right">＋ 항목 추가</button>\n    </div>\n    <div id="rows1"></div>\n  </div>\n\n  <div class="practice">\n    <div class="practice-head" style="color:#158b62">④ [활동 2] 표(Table)형 데이터 만들기: 우리 모둠 친구 데이터 정리\n      <button id="add2" style="float:right">＋ 행 추가</button>\n    </div>\n    <div id="rows2"></div>\n  </div>\n\n  <div class="actions">\n    <button id="clear">초기화</button>\n    <button id="score">자동 채점 및 저장</button>\n  </div>\n  <div id="result"></div>\n</div>\n\n<script>\nconst words=["데이터","특성","정리 및 배열","통일된 모양","쉽게 찾을","내용 요소 간의 관계","효율적으로 관리","기준","세로줄과 가로줄","점, 선, 도형"];\nconst wordBox=document.getElementById(\'words\');\nwords.forEach((w,i)=>{\n const s=document.createElement(\'span\'); s.className=\'word\'; s.textContent=w; s.draggable=true; s.dataset.word=w;\n s.addEventListener(\'dragstart\',e=>e.dataTransfer.setData(\'text/plain\',w));\n s.addEventListener(\'click\',()=>insertWord(w));\n wordBox.appendChild(s);\n});\n\nfunction insertWord(w){\n const el=document.activeElement;\n if(el && el.classList.contains(\'drop\')){el.textContent=w; el.dispatchEvent(new Event(\'input\',{bubbles:true}));}\n}\ndocument.querySelectorAll(\'.drop\').forEach(el=>{\n el.addEventListener(\'dragover\',e=>{e.preventDefault();el.classList.add(\'dragover\')});\n el.addEventListener(\'dragleave\',()=>el.classList.remove(\'dragover\'));\n el.addEventListener(\'drop\',e=>{e.preventDefault();el.classList.remove(\'dragover\');el.textContent=e.dataTransfer.getData(\'text/plain\')});\n el.addEventListener(\'keydown\',e=>{if(e.key===\'Enter\')e.preventDefault()});\n});\n\nfunction addRow(target, type){\n const wrap=document.getElementById(target);\n const n=wrap.children.length+1;\n const row=document.createElement(\'div\'); row.className=\'row\';\n if(type===1){\n   row.innerHTML=`<div class="rownum">${n}.</div><input class="list-a" placeholder="활동 역할/항목 이름 입력"><input class="list-b" placeholder="세부 실천 내용 또는 시간/장소"><div class="del">♜</div>`;\n }else{\n   row.innerHTML=`<div class="rownum">${n}.</div><input class="table-a" placeholder="이름"><input class="table-b" placeholder="특징/정보 입력"><div class="del">♜</div>`;\n }\n row.querySelector(\'.del\').onclick=()=>{row.remove(); renumber(wrap)};\n wrap.appendChild(row);\n}\nfunction renumber(wrap){[...wrap.children].forEach((r,i)=>r.querySelector(\'.rownum\').textContent=(i+1)+\'.\')}\n\nfor(let i=0;i<3;i++){addRow(\'rows1\',1);addRow(\'rows2\',2)}\ndocument.getElementById(\'add1\').onclick=()=>addRow(\'rows1\',1);\ndocument.getElementById(\'add2\').onclick=()=>addRow(\'rows2\',2);\n\nfunction getData(){\n const answers=[...document.querySelectorAll(\'.drop\')].map(x=>x.textContent.trim());\n const list=[...document.querySelectorAll(\'#rows1 .row\')].map(r=>[r.querySelector(\'.list-a\').value,r.querySelector(\'.list-b\').value]);\n const table=[...document.querySelectorAll(\'#rows2 .row\')].map(r=>[r.querySelector(\'.table-a\').value,r.querySelector(\'.table-b\').value]);\n return {\n  cls:document.getElementById(\'cls\').value,\n  num:document.getElementById(\'num\').value,\n  name:document.getElementById(\'name\').value,\n  answers,list,table,\n  timestamp:new Date().toISOString()\n };\n}\nfunction sendToStreamlit(payload){\n if(window.Streamlit && Streamlit.setComponentValue) Streamlit.setComponentValue(payload);\n}\ndocument.getElementById(\'score\').onclick=()=>{\n const data=getData();\n let correct=0;\n document.querySelectorAll(\'.drop\').forEach(el=>{\n   const ok=el.textContent.trim()===el.dataset.answer;\n   el.style.background=ok?\'#edfff3\':\'#fff0f0\';\n   el.style.borderColor=ok?\'#62b77c\':\'#e07a7a\';\n   if(ok) correct++;\n });\n const result=document.getElementById(\'result\');\n result.style.display=\'block\';\n result.textContent=`빈칸 ${correct}개 정답 / 총 ${document.querySelectorAll(\'.drop\').length}개`;\n data.score=correct;\n sendToStreamlit(data);\n};\ndocument.getElementById(\'clear\').onclick=()=>{\n document.querySelectorAll(\'.drop\').forEach(x=>{x.textContent=\'\';x.style.background=\'white\';x.style.borderColor=\'#9db7d4\'});\n document.querySelectorAll(\'input\').forEach(x=>{if(![\'cls\',\'num\',\'name\'].includes(x.id))x.value=\'\'});\n document.getElementById(\'result\').style.display=\'none\';\n};\nfunction resize(){\n if(window.Streamlit && Streamlit.setFrameHeight) Streamlit.setFrameHeight(document.body.scrollHeight+15);\n}\nif(window.Streamlit){\n Streamlit.events.addEventListener(Streamlit.RENDER_EVENT, resize);\n Streamlit.setComponentReady();\n Streamlit.setFrameHeight(document.body.scrollHeight+15);\n}\n</script>\n</body>\n</html>'

COMPONENT_DIR = Path(__file__).parent / ".worksheet_component"
COMPONENT_DIR.mkdir(exist_ok=True)
(COMPONENT_DIR / "index.html").write_text(COMPONENT_HTML, encoding="utf-8")

worksheet = components.declare_component(
    "data_structure_worksheet",
    path=str(COMPONENT_DIR),
)

value = worksheet(key="worksheet_v1", default=None)

if value:
    st.session_state["last_result"] = value

    try:
        import gspread
        from google.oauth2.service_account import Credentials

        if "gcp_service_account" in st.secrets and "google_sheet" in st.secrets:
            scopes = [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive",
            ]
            credentials = Credentials.from_service_account_info(
                st.secrets["gcp_service_account"],
                scopes=scopes,
            )
            gc = gspread.authorize(credentials)
            spreadsheet_id = st.secrets["google_sheet"]["spreadsheet_id"]
            worksheet_name = st.secrets["google_sheet"].get("worksheet_name", "Sheet1")
            ws = gc.open_by_key(spreadsheet_id).worksheet(worksheet_name)

            answers = value.get("answers", [])
            row = [
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                value.get("cls", ""),
                value.get("num", ""),
                value.get("name", ""),
                *answers,
                value.get("score", 0),
                str(value.get("list", [])),
                str(value.get("table", [])),
            ]
            ws.append_row(row, value_input_option="USER_ENTERED")
            st.success("채점 결과와 활동 내용이 Google Sheets에 저장되었습니다.")
    except Exception as e:
        if "gcp_service_account" in st.secrets:
            st.warning(f"Google Sheets 저장 설정을 확인하세요: {e}")

st.caption("통계와 데이터 · 데이터의 구조화 활동지")
