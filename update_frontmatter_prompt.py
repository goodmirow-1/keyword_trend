import re

# Read the file
with open('trend_blog_system.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Define the old and new text
old_text = """        [Front-matter 작성 규칙]
        - title: '{keyword}' + (카테고리별 특성에 맞는 매력적인 제목)
        - categories: 반드시 [정보, 분석, 후기] 등 적절한 것 선택 (트렌드 사용 금지)
        - tags: ['{keyword}', 관련태그1, 관련태그2]
        - description: 글의 핵심 내용을 요약한 메타 설명"""

new_text = """        [Front-matter 작성 규칙]
        **중요: 반드시 아래 형식을 정확히 따라야 합니다!**
        
        예시:
        ---
        title: '제목은 여기에'
        categories: [정보, 분석]
        tags: ['태그1', '태그2', '태그3']
        description: 메타 설명은 여기에
        ---
        
        **주의사항:**
        - 시작과 끝 모두 정확히 `---` (하이픈 3개)를 사용해야 합니다
        - `--` (하이픈 2개)는 절대 사용하지 마세요
        - frontmatter를 ```markdown 코드 블록으로 감싸지 마세요
        - frontmatter 다음에는 반드시 빈 줄을 하나 넣으세요
        - title: '{keyword}' + (카테고리별 특성에 맞는 매력적인 제목)
        - categories: 반드시 [정보, 분석, 후기] 등 적절한 것 선택 (트렌드 사용 금지)
        - tags: ['{keyword}', 관련태그1, 관련태그2]
        - description: 글의 핵심 내용을 요약한 메타 설명"""

# Replace
if old_text in content:
    content = content.replace(old_text, new_text)
    print("[OK] Found and replaced frontmatter instructions")
else:
    print("[ERROR] Old text not found - trying alternative approach")
    # Try with regex
    pattern = r'\[Front-matter 작성 규칙\].*?- description: 글의 핵심 내용을 요약한 메타 설명'
    match = re.search(pattern, content, re.DOTALL)
    if match:
        content = content.replace(match.group(0), new_text)
        print("[OK] Found and replaced with regex")
    else:
        print("[ERROR] Could not find the section to replace")
        exit(1)

# Write back
with open('trend_blog_system.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("[OK] File updated successfully!")
