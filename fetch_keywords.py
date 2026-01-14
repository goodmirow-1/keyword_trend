# -*- coding: utf-8 -*-
"""
Streamlit에서 안전하게 키워드를 가져오는 헬퍼 스크립트
stdout에는 순수 JSON만 출력 (로그 제거)
"""
import sys
import json
import os

if __name__ == "__main__":
    # 출력 인코딩 설정
    if sys.platform == 'win32':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    
    # stdout을 임시로 devnull로 리다이렉트 (로그 억제)
    import io
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()  # 로그를 버퍼에 저장 (출력 안 함)
    
    try:
        from trend_blog_system import TrendBlogSystem
        
        system = TrendBlogSystem()
        keywords = system.get_trending_keywords()
        
        # stdout 복원
        sys.stdout = old_stdout
        
        # 순수 JSON만 출력
        print(json.dumps(keywords, ensure_ascii=False))
        
    except Exception as e:
        # stdout 복원
        sys.stdout = old_stdout
        
        # 에러를 stderr로 출력
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)
