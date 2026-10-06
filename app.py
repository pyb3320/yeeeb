# -*- coding: utf-8 -*-
"""중학교 1학년 정보 - 데이터의 구조화와 분석 인터랙티브 활동지

학생 학번(4자리)+이름 로그인, Google Sheets 저장/불러오기,
활동지별 퍼센트 현황, PDF와 유사한 활동지 UI를 제공합니다.
"""
from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Any

import streamlit as st

st.set_page_config(page_title="2026 서라벌 정보", page_icon="📘", layout="wide", initial_sidebar_state="collapsed")

# Google Sheets 주소는 Secrets에 넣지 않고 코드에 고정합니다.
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1phUIj-pYwo5kWrVOKPJHF3R5UazmGqgjlVbWo1CD_7Q/edit?gid=0#gid=0"
SUBMISSION_SHEET = "제출기록"
SUMMARY_SHEET = "학생별현황"
ACCOUNT_SHEET = "학생계정"
DATA_SHEET = "학습데이터"
QUESTION_SHEET = "활동지1문항"
# 교사용 비밀번호 초기화 코드. Streamlit Secrets의 [app].teacher_reset_code가 있으면 그 값을 우선 사용합니다.
DEFAULT_TEACHER_RESET_CODE = "2026"
# 현재 제작된 활동지는 1개만 운영합니다.
# 이후 활동지를 추가할 때 이 사전만 확장하면 됩니다.
ACTIVITY_SHEETS = {
    "활동지1": "활동지1",
}

BLANK_ANSWERS = {
    "1":"데이터", "2":"특성", "3":"정리 및 배열", "4":"통일된 모양",
    "5":"쉽게 찾을", "6":"내용 요소 간의 관계", "7":"효율적으로 관리",
    "8":"기준", "9":"세로줄과 가로줄", "10":"점, 선, 도형",
    "11":"소프트웨어 개발 전문가", "12":"시스템 SW 개발자", "13":"운영체제 프로그래머",
    "14":"임베디드 프로그래머", "15":"응용 SW 개발자", "16":"응용 SW 프로그래머",
    "17":"네트워크 프로그래머", "18":"컴퓨터 및 모바일 게임 프로그래머",
}

st.markdown("""
<style>
#MainMenu, footer { visibility:hidden; }
header[data-testid="stHeader"] { height:0 !important; background:transparent; }
.block-container { max-width:1180px !important; padding:8px 12px 28px !important; }
[data-testid="stAppViewContainer"] { background:#eef1f5; }
.login-card { background:#fff; border:1px solid #d7dfeb; border-radius:18px; padding:24px; margin:12px auto 18px; max-width:760px; box-shadow:0 8px 28px rgba(34,55,86,.08); }
.login-title { font-size:26px; font-weight:900; color:#12233c; }
.login-sub { color:#66758b; font-size:13px; margin-top:4px; }
.badge-ok { display:inline-block; padding:6px 10px; border-radius:99px; background:#eaf8ef; color:#168146; font-weight:800; font-size:12px; }
.history-card { background:#fff; border:1px solid #d7dfeb; border-radius:14px; padding:14px 16px; }
.metric-caption { font-size:12px; color:#6e7d91; }
.metric-value { font-size:30px; font-weight:900; color:#1b63d6; }
</style>
""", unsafe_allow_html=True)



def _as_dict(value: Any) -> dict:
    try:
        return dict(value)
    except Exception:
        return {}


def _secret_dict(name: str) -> dict:
    try:
        return dict(st.secrets.get(name, {}))
    except Exception:
        return {}


def get_google_client():
    """Google Sheets용 gspread 클라이언트를 생성합니다."""
    import gspread
    from gspread.exceptions import APIError
    from google.oauth2.service_account import Credentials

    creds_info = _secret_dict("gcp_service_account")
    if not creds_info:
        raise RuntimeError(
            "Streamlit Secrets에 [gcp_service_account]가 없습니다. "
            "서비스 계정 JSON 내용을 해당 섹션에 넣어 주세요."
        )

    required = ["type", "project_id", "private_key", "client_email"]
    missing = [k for k in required if not creds_info.get(k)]
    if missing:
        raise RuntimeError(
            "[gcp_service_account]에서 빠진 항목: " + ", ".join(missing)
        )

    private_key = str(creds_info.get("private_key", ""))
    creds_info["private_key"] = private_key.replace("\\n", "\n")

    scopes = ["https://www.googleapis.com/auth/spreadsheets"]

    try:
        creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
        return gspread.authorize(creds)
    except Exception as exc:
        raise RuntimeError(f"서비스 계정 인증에 실패했습니다: {exc}") from exc


def get_spreadsheet():
    """고정된 Google Sheets URL을 서비스 계정으로 엽니다."""
    try:
        gc = get_google_client()
        # URL에는 gid, #gid 같은 부가 파라미터가 있어도 문서 ID만 추출됩니다.
        sh = gc.open_by_url(SPREADSHEET_URL)
        ensure_worksheets(sh)
        return sh
    except Exception as exc:
        # gspread는 권한 부족 시 PermissionError로 변환합니다.
        import gspread
        from gspread.exceptions import APIError

        email = "확인 불가"
        try:
            email = str(_secret_dict("gcp_service_account").get("client_email", "확인 불가"))
        except Exception:
            pass

        if isinstance(exc, PermissionError):
            raise RuntimeError(
                "Google Sheets 접근 권한이 없습니다.\n\n"
                f"현재 앱이 사용하는 서비스 계정: {email}\n\n"
                "Google Sheets에서 [공유] → 위 서비스 계정 이메일을 추가하고 [편집자] 권한을 주세요. "
                "또한 Google Sheets API가 Google Cloud 프로젝트에서 사용 설정되어 있어야 합니다.\n\n"
                f"연결 대상: {SPREADSHEET_URL}"
            ) from exc

        # APIError는 HTTP 상태를 포함해 진단 가능한 메시지를 유지합니다.
        if isinstance(exc, APIError):
            raise RuntimeError(f"Google Sheets API 오류: {exc}") from exc

        raise RuntimeError(f"Google Sheets 연결 실패: {exc}") from exc


def column_letter(n:int) -> str:
    out=""
    while n:
        n, r = divmod(n-1, 26)
        out = chr(65+r)+out
    return out


def get_or_create_ws(sh, title, rows=2000, cols=60):
    try:
        return sh.worksheet(title)
    except Exception:
        return sh.add_worksheet(title=title, rows=rows, cols=cols)


def ensure_worksheets(sh):
    """필요한 탭을 준비하고 기존 학생계정 형식을 자동 보정합니다."""
    # 현재는 "데이터의 구조화(활동지1)" 한 개만 운영합니다.
    # 교사용 기록에는 답안 원문/OX 판정 없이 빈칸 수, 정답 수, 퍼센트만 저장합니다.
    submission_headers = [
        "제출시각", "학번", "이름",
        "활동지1_빈칸수", "활동지1_정답수", "활동지1_퍼센트"
    ]
    summary_headers = [
        "학번", "이름",
        "활동지1_빈칸수", "활동지1_정답수", "활동지1_퍼센트",
        "최근제출"
    ]
    account_headers = ["학번", "이름", "비밀번호", "가입일시", "상태", "비밀번호변경일시"]
    data_headers = [
        "제출시각", "학번", "이름",
        "활동지1_빈칸수", "활동지1_정답수", "활동지1_퍼센트",
        "payload_json"
    ]
    activity_headers = [
        "제출시각", "학번", "이름",
        "빈칸수", "정답수", "퍼센트"
    ]
    # 학생이 활동지1 빈칸에 넣었던 내용을 문항별로 직접 확인하고 복원하기 위한 탭
    question_headers = [
        "제출시각", "학번", "이름",
        *[f"문항{i}" for i in range(1, len(BLANK_ANSWERS) + 1)]
    ]

    specs = [
        (SUBMISSION_SHEET, submission_headers, 3000, 10, False),
        (SUMMARY_SHEET, summary_headers, 1000, 10, False),
        (ACCOUNT_SHEET, account_headers, 1000, 10, False),
        (DATA_SHEET, data_headers, 3000, 12, True),
        (QUESTION_SHEET, question_headers, 3000, 30, False),
        (ACTIVITY_SHEETS["활동지1"], activity_headers, 2000, 8, False),
    ]

    for title, headers, rows, cols, should_hide in specs:
        try:
            ws = sh.worksheet(title)
            created = False
        except Exception:
            ws = sh.add_worksheet(title=title, rows=rows, cols=cols)
            created = True

        if created:
            ws.update(range_name=f"A1:{column_letter(len(headers))}1", values=[headers])
        else:
            # 현재 버전의 헤더로 통일합니다. 기존 데이터 행은 삭제하지 않습니다.
            ws.update(range_name=f"A1:{column_letter(len(headers))}1", values=[headers])
        if title == ACCOUNT_SHEET:
            # 기존 학생계정 탭도 새 헤더를 사용합니다. 데이터 행은 아래에서 자동 보정합니다.
            try:
                existing = ws.get_all_values()

                # 이전 버전: [학번, 이름, 가입일시, 상태]
                # 새 버전:    [학번, 이름, 비밀번호, 가입일시, 상태, 비밀번호변경일시]
                for r_idx, row in enumerate(existing[1:], start=2):
                    if not row or not str(row[0]).strip():
                        continue
                    # 새 형식은 6칸 이상이고 3열이 비밀번호이므로 그대로 둡니다.
                    if len(row) >= 6:
                        continue
                    sid = str(row[0]).strip()
                    name = str(row[1]).strip() if len(row) > 1 else ""
                    joined = str(row[2]).strip() if len(row) > 2 else ""
                    status = str(row[3]).strip() if len(row) > 3 else "사용"
                    migrated = [sid, name, "", joined, status or "사용", ""]
                    ws.update(range_name=f"A{r_idx}:F{r_idx}", values=[migrated])
            except Exception:
                # 접근 오류는 get_spreadsheet에서 실제 오류로 처리합니다.
                raise

        if should_hide:
            try:
                ws.hide()
            except Exception:
                pass


def validate_password(password: str) -> str:
    pw = str(password or "").strip()
    if not pw:
        raise ValueError("비밀번호를 입력하세요.")
    if len(pw) < 4 or len(pw) > 20:
        raise ValueError("비밀번호는 4~20자리로 입력하세요.")
    return pw


def get_teacher_reset_code() -> str:
    try:
        app_secret = _secret_dict("app")
        code = str(app_secret.get("teacher_reset_code", "")).strip()
        if code:
            return code
    except Exception:
        pass
    return DEFAULT_TEACHER_RESET_CODE


def register_student(student_id: str, student_name: str, password: str):
    """학생 계정을 Google Sheets에 생성합니다. 비밀번호는 요청에 따라 평문으로 저장합니다."""
    sid = str(student_id).strip()
    name = str(student_name).strip()
    try:
        pw = validate_password(password)
    except ValueError as exc:
        return False, str(exc)

    if not re.fullmatch(r"\d{4}", sid):
        return False, "학번은 숫자 4자리로 입력하세요."
    if not name:
        return False, "이름을 입력하세요."

    try:
        sh = get_spreadsheet()
        ws = sh.worksheet(ACCOUNT_SHEET)
        rows = ws.get_all_values()
        for row in rows[1:]:
            old_sid = str(row[0]).strip() if row else ""
            old_name = str(row[1]).strip() if len(row) > 1 else ""
            if old_sid == sid:
                if old_name == name:
                    return False, "중복된 학번입니다. 이미 만들어진 학생 계정이 있습니다. [로그인] 탭에서 로그인하세요."
                return False, f"중복된 학번입니다. {sid}번은 이미 다른 이름({old_name})으로 등록되어 있습니다."

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ws.append_row([sid, name, pw, now, "사용", now], value_input_option="USER_ENTERED")
        return True, "학생 계정이 만들어졌습니다. 이제 로그인할 수 있습니다."
    except Exception as exc:
        return False, str(exc)


def verify_student_login(student_id: str, student_name: str, password: str):
    """학생계정 탭을 기준으로 로그인합니다.

    학생계정 행이 실제로 존재해야 로그인할 수 있습니다.
    계정 행을 Google Sheets에서 삭제하면 이전 제출기록이 남아 있어도 로그인할 수 없습니다.
    """
    sid = str(student_id).strip()
    name = str(student_name).strip()
    pw = str(password or "").strip()

    if not re.fullmatch(r"\d{4}", sid):
        return False, "학번은 숫자 4자리로 입력하세요."
    if not name:
        return False, "이름을 입력하세요."
    if not pw:
        return False, "비밀번호를 입력하세요."

    try:
        sh = get_spreadsheet()
        ws = sh.worksheet(ACCOUNT_SHEET)
        rows = ws.get_all_values()
        for row in rows[1:]:
            if row and str(row[0]).strip() == sid:
                registered_name = str(row[1]).strip() if len(row) > 1 else ""
                registered_password = str(row[2]).strip() if len(row) > 2 else ""
                status = str(row[4]).strip() if len(row) > 4 else "사용"

                if registered_name != name:
                    return False, "학번은 존재하지만 등록된 이름과 다릅니다."
                if status and status != "사용":
                    return False, "사용할 수 없는 학생 계정입니다. 선생님에게 문의하세요."
                if not registered_password:
                    return False, "이 계정에는 비밀번호가 아직 설정되지 않았습니다. 선생님에게 비밀번호 초기화를 요청하세요."
                if registered_password != pw:
                    return False, "비밀번호가 올바르지 않습니다."
                return True, "로그인되었습니다."

        # 중요: 계정을 삭제한 학생은 제출기록이 남아 있어도 자동 재등록하지 않습니다.
        return False, "등록된 학생 계정이 없습니다. 먼저 '학생 계정 만들기'에서 계정을 만들어 주세요."
    except Exception as exc:
        return False, str(exc)


def reset_student_password(student_id: str, student_name: str, teacher_code: str, new_password: str):
    """교사용 초기화 코드로 학생 비밀번호를 변경합니다."""
    sid = str(student_id).strip()
    name = str(student_name).strip()
    code = str(teacher_code or "").strip()
    try:
        pw = validate_password(new_password)
    except ValueError as exc:
        return False, str(exc)

    if code != get_teacher_reset_code():
        return False, "교사용 비밀번호 초기화 코드가 올바르지 않습니다."
    if not re.fullmatch(r"\d{4}", sid):
        return False, "학번은 숫자 4자리로 입력하세요."
    if not name:
        return False, "이름을 입력하세요."

    try:
        sh = get_spreadsheet()
        ws = sh.worksheet(ACCOUNT_SHEET)
        rows = ws.get_all_values()
        for r_idx, row in enumerate(rows[1:], start=2):
            if row and str(row[0]).strip() == sid:
                registered_name = str(row[1]).strip() if len(row) > 1 else ""
                if registered_name != name:
                    return False, "학번은 존재하지만 등록된 이름과 다릅니다."
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ws.update(range_name=f"C{r_idx}:F{r_idx}", values=[[pw, row[3] if len(row) > 3 else now, row[4] if len(row) > 4 else "사용", now]])
                return True, "비밀번호가 초기화되었습니다. 학생계정 탭에서 현재 비밀번호를 확인할 수 있습니다."
        return False, "등록된 학생 계정이 없습니다."
    except Exception as exc:
        return False, str(exc)


def norm(v:Any) -> str:
    return re.sub(r"\s+", "", str(v or "").strip().lower())


def calculate_percentages(payload:dict) -> dict:
    """현재 제작된 '데이터의 구조화와 분석' 활동지 1개만 채점합니다.

    전체 18개 빈칸(앞면 10 + 뒷면 계층형 다이어그램 8)을 기준으로
    맞힌 개수 / 18 * 100 으로 활동지1 퍼센트를 계산합니다.
    """
    blanks = payload.get("blanks", {}) or {}
    correct = 0
    total = len(BLANK_ANSWERS)
    for key, answer in BLANK_ANSWERS.items():
        user = blanks.get(str(key), "")
        if norm(user) and norm(user) == norm(answer):
            correct += 1

    pct = round(correct / total * 100, 1) if total else 0.0
    return {
        "activity1": pct,
        "activity1_correct": correct,
        "activity1_blank_count": total,
        "activity1_total": total,
        "overall": pct,
        "objective_correct": correct,
        "objective_total": total,
    }


def get_sheet_diagnostic():
    """UI-safe diagnostic. Does not print private keys."""
    try:
        sh = get_spreadsheet()
        return {"ok": True, "title": getattr(sh, "title", ""), "url": SPREADSHEET_URL}
    except Exception as exc:
        return {"ok": False, "error": str(exc), "url": SPREADSHEET_URL}


def account_is_active(student_id: str, student_name: str) -> bool:
    """현재 학생 계정이 Google Sheets에 실제로 존재하고 '사용' 상태인지 확인합니다."""
    try:
        sh = get_spreadsheet()
        rows = sh.worksheet(ACCOUNT_SHEET).get_all_values()
        sid = str(student_id).strip()
        name = str(student_name).strip()
        for row in rows[1:]:
            if not row:
                continue
            if str(row[0]).strip() == sid and str(row[1]).strip() == name:
                status = str(row[4]).strip() if len(row) > 4 else "사용"
                return not status or status == "사용"
        return False
    except Exception:
        return False


def save_submission(payload:dict):
    """학생 답안 원문은 숨김 복원 탭에만 보관하고, 교사용 탭에는 퍼센트만 저장합니다."""
    p = calculate_percentages(payload)
    sid = str(payload.get("studentId", "")).strip()
    name = str(payload.get("name", "")).strip()
    if not account_is_active(sid, name):
        return False, "학생 계정이 존재하지 않거나 사용 중지되었습니다. 다시 로그인해 주세요.", p

    try:
        sh = get_spreadsheet()
    except Exception as exc:
        return False, str(exc), p

    try:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sid = str(payload.get("studentId", "")).strip()
        name = str(payload.get("name", "")).strip()

        # 1) 교사용 제출기록: 답안 원문/OX 판정 없이 퍼센트와 정답수만 저장
        submission_row = [
            now, sid, name,
            p["activity1_blank_count"], p["activity1_correct"], f"{p['activity1']}%"
        ]
        get_or_create_ws(sh, SUBMISSION_SHEET, rows=3000, cols=10).append_row(
            submission_row, value_input_option="USER_ENTERED"
        )

        # 2) 학생별현황: 현재는 활동지1만 표시
        summary = get_or_create_ws(sh, SUMMARY_SHEET, rows=1000, cols=8)
        data = summary.get_all_values()
        target = None
        for r_idx, r in enumerate(data[1:], start=2):
            if r and str(r[0]).strip() == sid:
                target = r_idx
                break

        srow = [
            sid, name,
            p["activity1_blank_count"], p["activity1_correct"], f"{p['activity1']}%", now
        ]
        if target:
            summary.update(range_name=f"A{target}:F{target}", values=[srow])
        else:
            summary.append_row(srow, value_input_option="USER_ENTERED")

        # 3) 학생 복원용 데이터: 다음 로그인 때 예전 학습지 상태를 복원할 때만 사용
        data_ws = get_or_create_ws(sh, DATA_SHEET, rows=3000, cols=10)
        data_row = [
            now, sid, name,
            p["activity1_blank_count"], p["activity1_correct"], f"{p['activity1']}%",
            json.dumps(payload, ensure_ascii=False)
        ]
        data_ws.append_row(data_row, value_input_option="USER_ENTERED")
        try:
            data_ws.hide()
        except Exception:
            pass

        # 4) 활동지1 탭: 퍼센트 중심
        activity_ws = get_or_create_ws(sh, ACTIVITY_SHEETS["활동지1"], rows=2000, cols=8)
        activity_ws.append_row(
            [
                now, sid, name,
                p["activity1_blank_count"], p["activity1_correct"], f"{p['activity1']}%"
            ],
            value_input_option="USER_ENTERED"
        )

        # 5) 활동지1문항: 학생이 각 빈칸에 실제로 넣은 내용을 문항별로 저장
        #    교사가 Google Sheets에서 학생 답안을 확인하거나, 다음 로그인 때 복원할 때 사용
        question_ws = get_or_create_ws(
            sh, QUESTION_SHEET, rows=3000, cols=len(BLANK_ANSWERS) + 5
        )
        blanks = payload.get("blanks", {}) or {}
        question_row = [now, sid, name] + [str(blanks.get(str(i), "") or "") for i in range(1, len(BLANK_ANSWERS) + 1)]
        question_ws.append_row(question_row, value_input_option="USER_ENTERED")

        return True, "제출 및 저장이 완료되었습니다.", p
    except Exception as exc:
        return False, f"Google Sheets 저장 오류: {exc}", p


def load_student_submissions(student_id:str, student_name:str="") -> list[dict]:
    """로그인 학생의 이전 활동지1을 불러옵니다.

    - '활동지1문항' 탭에서 문항별 실제 입력값을 읽습니다.
    - '학습데이터' 탭에 전체 학습지 payload가 있으면 함께 복원합니다.
    - 따라서 예전에 빈칸에 어떤 내용을 넣었는지 그대로 다시 볼 수 있습니다.
    """
    try:
        sh = get_spreadsheet()
    except Exception as exc:
        st.session_state["sheet_error"] = str(exc)
        raise RuntimeError(str(exc)) from exc

    sid = str(student_id).strip()
    name = str(student_name).strip()

    # 먼저 전체 payload(목록/표/다이어그램 포함)를 가져옵니다. 없으면 빈 학습지에서 시작합니다.
    payload_by_time: dict[str, dict] = {}
    try:
        rows = sh.worksheet(DATA_SHEET).get_all_values()
        for row in rows[1:]:
            if len(row) < 5:
                continue
            if str(row[1]).strip() != sid:
                continue
            if name and str(row[2]).strip() != name:
                continue
            saved_at = str(row[0]).strip()
            raw_payload = row[6] if len(row) >= 7 else (row[4] if len(row) > 4 else "")
            if not raw_payload:
                continue
            try:
                payload = json.loads(str(raw_payload))
            except Exception:
                continue
            if isinstance(payload, dict):
                payload_by_time[saved_at] = payload
    except Exception:
        # 전체 payload 탭을 읽지 못하더라도 활동지1문항 탭으로 빈칸 복원은 시도합니다.
        payload_by_time = {}

    try:
        qrows = sh.worksheet(QUESTION_SHEET).get_all_values()
    except Exception as exc:
        st.session_state["sheet_error"] = str(exc)
        raise RuntimeError(f"활동지1문항 탭을 읽을 수 없습니다: {exc}") from exc

    if len(qrows) <= 1:
        return []

    result = []
    for row in qrows[1:]:
        if len(row) < 3:
            continue
        if str(row[1]).strip() != sid:
            continue
        if name and str(row[2]).strip() != name:
            continue

        saved_at = str(row[0]).strip()
        # 활동지1문항 탭에서 문항1~18을 복원
        blanks = {}
        for idx in range(1, len(BLANK_ANSWERS) + 1):
            col = idx + 2
            blanks[str(idx)] = str(row[col]).strip() if len(row) > col else ""

        payload = dict(payload_by_time.get(saved_at, {}))
        if not payload:
            payload = empty_payload(sid, name)
        else:
            payload = dict(payload)

        payload["studentId"] = sid
        payload["name"] = name
        payload["blanks"] = blanks

        # 이 기록의 점수는 현재 저장된 빈칸으로 다시 계산합니다.
        p = calculate_percentages(payload)
        payload["_saved_at"] = saved_at
        payload["_activity_percent"] = {"activity1": f"{p['activity1']}%"}
        payload["_activity_blank_count"] = p["activity1_blank_count"]
        payload["_activity_correct"] = p["activity1_correct"]
        payload["score"] = p["activity1_correct"]
        result.append(payload)

    # 같은 저장시각이 중복되면 마지막 기록 하나만 사용
    unique = {}
    for item in result:
        unique[str(item.get("_saved_at", ""))] = item
    result = list(unique.values())
    result.sort(key=lambda x: str(x.get("_saved_at", "")), reverse=True)
    return result


def empty_payload(sid,name):
    return {"grade":"1","studentId":sid,"number":sid,"name":name,"blanks":{},
            "listRows":[["아침 환기 및 창문 열기 (샘플)","매일 등교 직후 8:30 창문 개방"]],
            "tableRows":[["김민준(샘플)","03월 15일","축구, 코딩","1번 / 체육부장"]],
            "experienceListRows":[["4월","경복궁, 창덕궁, 종묘","지하철 3호선","봄꽃 감상 및 역사 탐방"]],
            "experienceTableRows":[["4월 (예시)","경복궁, 창덕궁, 종묘","지하철 3호선","봄꽃 감상 및 역사 탐방"]],
            "experienceDiagramRows":[["4월","경복궁, 창덕궁, 종묘","지하철 3호선","봄꽃 감상 및 역사 탐방"]],
            "structure":"표","selfChecks":{"q1":False,"q2":False,"q3":False},"page":1,"score":0}


# ============================================================
# 로그인 / 계정
# ============================================================
for k, v in {
    "logged_in": False,
    "student_id": "",
    "student_name": "",
    "history": [],
    "worksheet_data": {},
    "loaded_history_index": 0,
    "last_saved_event": "",
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

with st.expander("Google Sheets 연결 상태 확인", expanded=False):
    st.caption("Google Sheets 주소는 app.py에 고정되어 있고, 인증정보만 Streamlit Secrets에서 가져옵니다.")
    if st.button("연결 테스트", key="sheet_test_safe", width="stretch"):
        diag = get_sheet_diagnostic()
        if diag.get("ok"):
            st.success("Google Sheets 연결 성공")
            st.caption(f"연결된 문서: {diag.get('title') or '(제목 확인 불가)'}")
        else:
            st.error(diag.get("error", "연결 실패"))


if not st.session_state.logged_in:
    st.markdown(
        '<div class="login-card">'
        '<div class="login-title">📘 2026 서라벌 정보</div>'
        '<div class="login-sub">학생 계정을 만들고, 같은 학번과 이름, 비밀번호로 계속 로그인하여 이전 학습지를 확인하세요.</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    login_tab, signup_tab, reset_tab = st.tabs(["🔐 로그인", "✨ 학생 계정 만들기", "🔄 비밀번호 초기화"])

    with login_tab:
        with st.form("login_form"):
            c1, c2 = st.columns(2)
            sid = c1.text_input("학번 (4자리)", max_chars=4, placeholder="예: 1102")
            name = c2.text_input("이름", placeholder="예: 홍길동")
            login_password = c1.text_input("비밀번호", type="password", placeholder="비밀번호를 입력하세요")
            submit_login = st.form_submit_button("로그인", type="primary", width="stretch")
        if submit_login:
            ok, message = verify_student_login(sid, name, login_password)
            if not ok:
                st.error(message)
            else:
                try:
                    history = load_student_submissions(sid.strip(), name.strip())
                except Exception as exc:
                    st.error(str(exc))
                    st.stop()
                st.session_state.logged_in = True
                st.session_state.student_id = sid.strip()
                st.session_state.student_name = name.strip()
                st.session_state.history = history
                st.session_state.worksheet_data = history[0] if history else empty_payload(sid.strip(), name.strip())
                st.session_state.loaded_history_index = 0
                st.rerun()

    with signup_tab:
        st.info("학생 계정은 학번 4자리 + 이름 + 비밀번호로 만듭니다. 같은 학번은 한 번만 등록할 수 있습니다. 계정 정보는 Google Sheets의 '학생계정' 탭에 정리됩니다.")
        with st.form("signup_form"):
            c1, c2 = st.columns(2)
            new_sid = c1.text_input("새 학번 (4자리)", max_chars=4, placeholder="예: 1102")
            new_name = c2.text_input("이름", placeholder="예: 홍길동")
            new_password = c1.text_input("비밀번호", type="password", placeholder="4~20자리")
            new_password2 = c2.text_input("비밀번호 확인", type="password", placeholder="한 번 더 입력하세요")
            create_account = st.form_submit_button("학생 계정 만들기", type="primary", width="stretch")
        if create_account:
            if new_password != new_password2:
                st.error("비밀번호가 서로 다릅니다.")
                st.stop()
            ok, message = register_student(new_sid, new_name, new_password)
            if ok:
                st.success(message)
                sid_clean = new_sid.strip()
                name_clean = new_name.strip()
                try:
                    history = load_student_submissions(sid_clean, name_clean)
                except Exception:
                    history = []
                st.session_state.logged_in = True
                st.session_state.student_id = sid_clean
                st.session_state.student_name = name_clean
                st.session_state.history = history
                st.session_state.worksheet_data = history[0] if history else empty_payload(sid_clean, name_clean)
                st.session_state.loaded_history_index = 0
                st.session_state.last_saved_event = ""
                st.rerun()
            else:
                st.error(message)
                st.info("이미 계정이 있다면 위의 [🔐 로그인] 탭으로 이동하여 같은 학번과 이름으로 로그인하세요. 로그인하면 저장된 이전 학습지를 자동으로 불러옵니다.")
    with reset_tab:
        st.info("비밀번호를 잊은 경우 선생님이 초기화할 수 있습니다. 초기화한 비밀번호는 Google Sheets의 '학생계정' 탭에서 확인할 수 있습니다. 초기화 코드는 Streamlit Secrets의 [app].teacher_reset_code를 권장합니다.")
        with st.form("reset_password_form"):
            c1, c2 = st.columns(2)
            reset_sid = c1.text_input("학번 (4자리)", max_chars=4, placeholder="예: 1102")
            reset_name = c2.text_input("이름", placeholder="예: 홍길동")
            reset_code = c1.text_input("교사용 초기화 코드", type="password")
            reset_pw = c2.text_input("새 비밀번호", type="password", placeholder="4~20자리")
            reset_pw2 = c1.text_input("새 비밀번호 확인", type="password")
            reset_submit = st.form_submit_button("비밀번호 초기화", type="primary", width="stretch")
        if reset_submit:
            if reset_pw != reset_pw2:
                st.error("새 비밀번호가 서로 다릅니다.")
            else:
                ok, message = reset_student_password(reset_sid, reset_name, reset_code, reset_pw)
                if ok:
                    st.success(message)
                else:
                    st.error(message)

    st.stop()

st.markdown(
    f'<span class="badge-ok">로그인됨 · {st.session_state.student_id} · {st.session_state.student_name}</span>',
    unsafe_allow_html=True,
)

col_logout, col_refresh = st.columns([1, 1])
if col_logout.button("로그아웃", use_container_width=True):
    for key, value in [("logged_in", False), ("student_id", ""), ("student_name", ""), ("history", []), ("worksheet_data", {})]:
        st.session_state[key] = value
    st.rerun()
if col_refresh.button("🔄 내 학습기록 새로 불러오기", use_container_width=True):
    try:
        st.session_state.history = load_student_submissions(
            st.session_state.student_id,
            st.session_state.student_name,
        )
        if st.session_state.history:
            st.session_state.worksheet_data = st.session_state.history[0]
            st.session_state.loaded_history_index = 0
        st.rerun()
    except Exception as exc:
        st.error(str(exc))


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
        <span>학번</span><b id="loginStudentId">-</b>
        <span>이름:</span><b id="loginStudentName">-</b>
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
    return {grade:'1',studentId:initial.studentId||'',className:initial.className||'',number:initial.number||'',name:initial.name||'',blanks,
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

  if(initial.studentId!==undefined){const sid=root.querySelector('#loginStudentId');if(sid)sid.textContent=initial.studentId||'-';}
  if(initial.name!==undefined){const nm=root.querySelector('#loginStudentName');if(nm)nm.textContent=initial.name||'-';}
  const initialBlanks=initial.blanks||{};
  root.querySelectorAll('.drop[data-id]').forEach(el=>{const v=initialBlanks[el.dataset.id]||'';el.textContent=v;updateBlankStatus(el,true);});
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
    root.querySelectorAll('input[type="checkbox"]').forEach(el=>{el.checked=false;});
    activity1Rows=[['아침 환기 및 창문 열기 (샘플)','매일 등교 직후 8:30 창문 개방']];
    activity2Rows=[['김민준(샘플)','03월 15일','축구, 코딩','1번 / 체육부장']];
    experienceListRows=[['4월','경복궁, 창덕궁, 종묘','지하철 3호선','봄꽃 감상 및 역사 탐방']];
    experienceTableRows=[['4월 (예시)','경복궁, 창덕궁, 종묘','지하철 3호선','봄꽃 감상 및 역사 탐방']];
    experienceDiagramRows=[['4월','경복궁, 창덕궁, 종묘','지하철 3호선','봄꽃 감상 및 역사 탐방']];
    currentStructure='표';
    renderActivity1();renderActivity2();renderStructure('표');
    root.querySelectorAll('.choice-buttons button').forEach(b=>b.classList.remove('selected'));
    root.querySelector('.choice-buttons button[data-structure="표"]')?.classList.add('selected');
    root.querySelector('#scoreText').textContent='';sync();
  });

  setPage(currentPage);sync();return ()=>{};
}
'''

worksheet_component = st.components.v2.component(
    "data_structure_worksheet_v2",
    html=HTML, css=CSS, js=JS, isolate_styles=True,
)


with st.container():
    result = worksheet_component(
        key="worksheet",
        data={"initial": st.session_state.worksheet_data},
        default={"payload": st.session_state.worksheet_data},
        on_payload_change=lambda: None,
        width="stretch",
        height="content",
    )

# ============================================================
# 제출 처리
# ============================================================
save_payload = getattr(result, "save", None)
if save_payload:
    save_payload = dict(save_payload)
    save_payload["studentId"] = st.session_state.student_id
    save_payload["number"] = st.session_state.student_id
    save_payload["name"] = st.session_state.student_name

    save_event = str(save_payload.get("timestamp", ""))
    # 같은 trigger가 재렌더링될 때 중복 저장하지 않음
    if save_event and save_event != st.session_state.last_saved_event:
        st.session_state.last_saved_event = save_event
        st.session_state.worksheet_data = save_payload
        ok, message, pcts = save_submission(save_payload)
        if ok:
            try:
                st.session_state.history = load_student_submissions(
                    st.session_state.student_id,
                    st.session_state.student_name,
                )
            except Exception:
                pass
            st.success(message)
            st.info(
                f"활동지 1: {pcts['activity1']}% · "
                f"빈칸 {pcts['activity1_blank_count']}개 · "
                f"정답 {pcts['activity1_correct']}개"
            )
        else:
            st.error(message)


# ============================================================
# 학생 본인 학습기록
# - 교사용 시트에는 퍼센트만 표시
# - 학생 화면에는 이전 기록의 날짜/퍼센트만 표시
# - 실제 이전 학습지 내용은 '학습지 열기' 버튼으로 복원
# ============================================================
st.markdown("---")
st.subheader("📚 내 학습 기록")
history = st.session_state.history

if not history:
    st.info("아직 제출한 학습지가 없습니다. 학습지를 작성한 뒤 '자동 채점 및 저장'을 눌러 주세요.")
else:
    labels = [f"{i+1}회차 · {h.get('_saved_at', '')}" for i, h in enumerate(history)]
    selected = st.selectbox(
        "확인할 제출 기록",
        labels,
        index=min(st.session_state.loaded_history_index, len(labels)-1),
        key="history_select",
    )
    idx = labels.index(selected)
    h = history[idx]
    saved_pct = h.get("_activity_percent", {})

    ht1 = st.tabs(["활동지 1"])[0]
    with ht1:
        st.markdown(
            f'<div class="history-card">'
            f'<div class="metric-caption">활동지 1 · 데이터의 구조화와 분석</div>'
            f'<div class="metric-value">{saved_pct.get("activity1", "-")}</div>'
            f'<div class="metric-caption">빈칸 {h.get("_activity_blank_count", len(BLANK_ANSWERS))}개 · 정답 {h.get("_activity_correct", h.get("score", "-"))}개 · 제출: {h.get("_saved_at", "-")}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown("### 전체 기록")
    st.write(
        f"제출일시: **{h.get('_saved_at', '-')}** · "
        f"활동지1: **{saved_pct.get('activity1', '-')}** · "
        f"빈칸 **{h.get('_activity_blank_count', len(BLANK_ANSWERS))}개** · "
        f"정답 **{h.get('_activity_correct', h.get('score', '-'))}개**"
    )
    st.caption("학생의 이전 빈칸 입력 내용은 저장된 활동지1문항 기록을 이용해 학습지 화면에 다시 복원합니다. 교사용 현황표에는 정답수와 퍼센트만 표시합니다.")

    if st.button("📖 선택한 이전 학습지를 화면에 불러오기", type="primary", width="stretch"):
        st.session_state.worksheet_data = h
        st.session_state.loaded_history_index = idx
        st.rerun()
