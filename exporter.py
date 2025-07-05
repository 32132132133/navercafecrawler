"""exporter.py
데이터 저장 전용 모듈.

NaverCafeCrawler 가 수집한 posts
data 를 엑셀로 내보내는 로직을 독립시켰다.
기존 save_to_excel 의 기능을 거의 그대로 유지한다.
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import List, Dict, Any

import pandas as pd

from config import Config

__all__ = ["CafeDataExporter"]


class CafeDataExporter:
    """posts_data(list[dict]) 를 다양한 시트로 엑셀 파일에 저장한다."""

    @staticmethod
    def save_all(posts_data: List[Dict[str, Any]], filename: str | None = None) -> str | bool:
        """주요 진입점.

        Parameters
        ----------
        posts_data : list[dict]
            크롤러가 수집한 게시글/댓글/이미지 정보를 담은 list.
        filename : str | None
            사용자가 지정한 파일명; None 이면 자동으로 timestamp 를 붙인다.

        Returns
        -------
        str | bool
            저장된 파일 전체 경로. 실패하면 False.
        """
        if not posts_data:
            print("❌ 저장할 데이터가 없습니다.")
            return False

        try:
            if not filename:
                timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                filename = f"cafe_posts_{timestamp}.xlsx"

            # ensure output dir
            os.makedirs(Config.OUTPUT_DIR, exist_ok=True)
            filepath = os.path.join(Config.OUTPUT_DIR, filename)

            print(f"💾 엑셀 파일 저장 중: {filepath}")
            print(f"📊 저장 데이터: {len(posts_data)}개 게시글")

            with pd.ExcelWriter(filepath, engine="openpyxl") as writer:
                CafeDataExporter._save_posts_sheet(writer, posts_data)
                CafeDataExporter._save_comments_sheet(writer, posts_data)
                CafeDataExporter._save_images_sheet(writer, posts_data)
                CafeDataExporter._save_statistics_sheet(writer, posts_data)

            print(f"✅ 저장 완료: {filepath}")
            print(f"📁 파일 크기: {os.path.getsize(filepath) / 1024 / 1024:.2f} MB")
            return filepath
        except Exception as e:
            print(f"❌ 엑셀 저장 중 오류 발생: {e}")
            return False

    # ------------------------------------------------------------------
    # 내부 헬퍼
    # ------------------------------------------------------------------

    @staticmethod
    def _save_posts_sheet(writer, posts_data: List[Dict[str, Any]]):
        rows = []
        for idx, post in enumerate(posts_data, 1):
            row = {
                "번호": idx,
                "제목": post.get("title", ""),
                "작성자": post.get("author", ""),
                "날짜": post.get("date", ""),
                "조회수": post.get("views", ""),
                "키워드": post.get("keyword", ""),
                "URL": post.get("url", ""),
                "수집시간": post.get("collection_time", ""),
                "내용길이": len(post.get("full_content", "")),
                "댓글수": len(post.get("comments", [])),
                "이미지수": len(post.get("images", [])),
                "첨부파일수": len(post.get("attachments", [])),
                "내용미리보기": (post.get("full_content", "") or post.get("content", ""))[:100]
                + ("..." if len(post.get("full_content", "") or post.get("content", "")) > 100 else ""),
            }
            if Config.EXTRACT_FULL_CONTENT and post.get("full_content"):
                row["전체내용"] = post.get("full_content", "")
            rows.append(row)

        if not rows:
            return
        df = pd.DataFrame(rows)
        df.to_excel(writer, sheet_name="게시글정보", index=False)
        CafeDataExporter._adjust_column_width(writer.sheets["게시글정보"], df)
        print(f"    ✅ 게시글 정보 시트 저장 완료: {len(rows)}개")

    @staticmethod
    def _save_comments_sheet(writer, posts_data):
        rows = []
        for post_idx, post in enumerate(posts_data, 1):
            title = post.get("title", f"게시글 {post_idx}")
            for comment in post.get("comments", []):
                rows.append(
                    {
                        "게시글번호": post_idx,
                        "게시글제목": title[:50] + ("..." if len(title) > 50 else ""),
                        "댓글번호": comment.get("index", ""),
                        "댓글작성자": comment.get("author", ""),
                        "댓글내용": comment.get("content", ""),
                        "댓글날짜": comment.get("date", ""),
                        "게시글URL": post.get("url", ""),
                    }
                )
        if rows:
            df = pd.DataFrame(rows)
            df.to_excel(writer, sheet_name="댓글정보", index=False)
            CafeDataExporter._adjust_column_width(writer.sheets["댓글정보"], df)
            print(f"    ✅ 댓글 정보 시트 저장 완료: {len(rows)}개")
        else:
            print("    ℹ️ 댓글 데이터 없음 - 댓글 시트 생략")

    @staticmethod
    def _save_images_sheet(writer, posts_data):
        rows = []
        for post_idx, post in enumerate(posts_data, 1):
            title = post.get("title", f"게시글 {post_idx}")
            for img_idx, image in enumerate(post.get("images", []), 1):
                rows.append(
                    {
                        "게시글번호": post_idx,
                        "게시글제목": title[:50] + ("..." if len(title) > 50 else ""),
                        "이미지번호": img_idx,
                        "이미지URL": image.get("url", ""),
                        "이미지설명": image.get("alt", ""),
                        "이미지크기": image.get("size", ""),
                        "게시글URL": post.get("url", ""),
                    }
                )
        if rows:
            df = pd.DataFrame(rows)
            df.to_excel(writer, sheet_name="이미지정보", index=False)
            CafeDataExporter._adjust_column_width(writer.sheets["이미지정보"], df)
            print(f"    ✅ 이미지 정보 시트 저장 완료: {len(rows)}개")
        else:
            print("    ℹ️ 이미지 데이터 없음 - 이미지 시트 생략")

    @staticmethod
    def _save_statistics_sheet(writer, posts_data):
        total_posts = len(posts_data)
        total_comments = sum(len(p.get("comments", [])) for p in posts_data)
        total_images = sum(len(p.get("images", [])) for p in posts_data)

        rows = [
            {"항목": "총 게시글 수", "값": total_posts, "설명": "수집된 전체 게시글 수"},
            {"항목": "총 댓글 수", "값": total_comments, "설명": "수집된 전체 댓글 수"},
            {"항목": "총 이미지 수", "값": total_images, "설명": "수집된 전체 이미지 수"},
            {
                "항목": "평균 댓글 수",
                "값": f"{total_comments/total_posts:.1f}" if total_posts else 0,
                "설명": "게시글당 평균 댓글 수",
            },
            {
                "항목": "평균 이미지 수",
                "값": f"{total_images/total_posts:.1f}" if total_posts else 0,
                "설명": "게시글당 평균 이미지 수",
            },
            {"항목": "데이터 수집 완료", "값": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "설명": "저장 시각"},
        ]

        df = pd.DataFrame(rows)
        df.to_excel(writer, sheet_name="통계분석", index=False)
        CafeDataExporter._adjust_column_width(writer.sheets["통계분석"], df)
        print("    ✅ 통계 분석 시트 저장 완료")

    # ------------------------------------------------------------------
    # utils
    # ------------------------------------------------------------------
    @staticmethod
    def _adjust_column_width(worksheet, dataframe):
        try:
            for idx, column in enumerate(dataframe.columns, 1):
                col_letter = worksheet.cell(row=1, column=idx).column_letter
                max_len = max(dataframe[column].astype(str).map(len).max(), len(str(column)))
                worksheet.column_dimensions[col_letter].width = min(max_len + 2, 50)
        except Exception:
            # 열 조정 실패해도 로직 중단은 하지 않음
            pass 