from trend_blog_system import TrendBlogSystem

def test_specific_keyword():
    system = TrendBlogSystem()
    keyword = "갤럭시 S25 울트라 스펙"
    
    print(f"Testing generation for keyword: {keyword}")
    
    # 1. Generate content
    content = system.generate_blog_content(keyword)
    
    if content:
        # 2. Save file
        filepath = system.save_blog_post(keyword, content)
        print(f"Successfully generated and saved to: {filepath}")
    else:
        print("Failed to generate content.")

if __name__ == "__main__":
    test_specific_keyword()
