"""
KNOT 자동 품질 검사 스크립트 (lint_check.py)
용도: 유틸리티 웹 HTML 파일의 애드센스 정책 준수 및 구조 완결성 자동 검증
실행: python 03_lint/lint_check.py --target 02_wiki/02A_products/
"""

import os
import re
import sys
import json
import argparse
import datetime

# ─── 검사 규칙 정의 ─────────────────────────────────────────────────

REQUIRED_ELEMENTS = {
    "ld_json": r'application/ld\+json',
    "adsense_leaderboard": r'Top_Leaderboard|leaderboard|728x90',
    "adsense_in_article": r'In.Article_Sticky|in.article|336x280',
    "adsense_skyscraper": r'Aside_SkyScraper|skyscraper|160x600',
    "viewport_meta": r'<meta[^>]+viewport',
    "charset_utf8": r'charset.*utf-8|charset.*UTF-8',
    "title_tag": r'<title>.+</title>',
    "lang_attribute": r'<html[^>]+lang=',
}

POLICY_VIOLATIONS = {
    "adult_content": r'\b(porn|xxx|adult|nude|sex)\b',
    "gambling_keywords": r'\b(casino|poker|bet|gambling|slots)\b',
    "drug_keywords": r'\b(cocaine|heroin|meth|drug dealer)\b',
    "copyright_marks": r'©\s*(?:Disney|Marvel|Netflix|Google|Apple)\b',
    "fake_adsense": r'onclick.*window\.location|fake.*ad|ad.*fake',
}

BROKEN_LINK_PATTERNS = [
    r'href=["\']#["\']',
    r'href=["\']["\']',
    r'src=["\']["\']',
]


# ─── 검사 함수 ──────────────────────────────────────────────────────

def check_file(filepath: str) -> dict:
    result = {
        "file": filepath,
        "passed": [],
        "failed": [],
        "violations": [],
        "warnings": [],
        "score": 0,
    }

    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    # 필수 요소 검사
    for name, pattern in REQUIRED_ELEMENTS.items():
        if re.search(pattern, content, re.IGNORECASE):
            result["passed"].append(name)
        else:
            result["failed"].append(name)

    # 정책 위반 검사
    for name, pattern in POLICY_VIOLATIONS.items():
        if re.search(pattern, content, re.IGNORECASE):
            result["violations"].append(name)

    # 깨진 링크 검사
    for pattern in BROKEN_LINK_PATTERNS:
        matches = re.findall(pattern, content, re.IGNORECASE)
        if matches:
            result["warnings"].append(f"깨진 링크 의심: {pattern} ({len(matches)}건)")

    # 점수 계산
    total_checks = len(REQUIRED_ELEMENTS)
    passed_count = len(result["passed"])
    violation_penalty = len(result["violations"]) * 20
    result["score"] = max(0, int((passed_count / total_checks) * 100) - violation_penalty)

    return result


def scan_directory(target_dir: str) -> list:
    results = []
    for root, _, files in os.walk(target_dir):
        for fname in files:
            if fname.endswith(".html"):
                fpath = os.path.join(root, fname)
                results.append(check_file(fpath))
    return results


def print_report(results: list):
    print("\n" + "=" * 60)
    print("  KNOT LINT REPORT")
    print(f"  실행 시각: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    if not results:
        print("[안내] 검사할 HTML 파일이 없습니다. BUILD_UTILITY_WEB을 먼저 실행하세요.")
        return

    overall_pass = True
    for r in results:
        fname = os.path.basename(r["file"])
        status = "✅ PASS" if r["score"] >= 80 and not r["violations"] else "❌ FAIL"
        if status == "❌ FAIL":
            overall_pass = False

        print(f"\n파일: {fname}")
        print(f"  점수: {r['score']}/100  {status}")

        if r["passed"]:
            print(f"  통과: {', '.join(r['passed'])}")
        if r["failed"]:
            print(f"  미비: {', '.join(r['failed'])}")
        if r["violations"]:
            print(f"  ⚠️  정책 위반: {', '.join(r['violations'])}")
        if r["warnings"]:
            for w in r["warnings"]:
                print(f"  ⚠️  경고: {w}")

    print("\n" + "=" * 60)
    final = "✅ 전체 통과 — 배포 준비 완료" if overall_pass else "❌ 수정 필요 — 위 항목을 해결 후 재검사"
    print(f"  최종 결과: {final}")
    print("=" * 60 + "\n")

    # 결과를 JSON으로도 저장
    report_path = os.path.join("03_lint", "last_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"[Linter] 상세 리포트 저장: {report_path}")


# ─── 진입점 ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="KNOT 유틸리티 웹 품질 검사")
    parser.add_argument("--target", default="02_wiki/02A_products/",
                        help="검사할 디렉토리 (기본: 02_wiki/02A_products/)")
    args = parser.parse_args()

    target = args.target
    if not os.path.exists(target):
        print(f"[오류] 대상 디렉토리 없음: {target}")
        sys.exit(1)

    print(f"[Linter] 검사 시작: {target}")
    results = scan_directory(target)
    print_report(results)
