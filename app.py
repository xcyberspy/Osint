from flask import Flask, render_template, request, jsonify
from playwright.sync_api import sync_playwright

app = Flask(__name__)

def classify_site(link, title):
    link_rawer = link.lower() if link else ""
    title_rawer = title.lower() if title else ""

    social_sites = {
        "Facebook": ["facebook.com", "fb.com"],
        "YouTube": ["youtube.com", "youtu.be"],
        "Telegram": ["t.me", "telegram.org"],
        "Instagram": ["instagram.com"],
        "Twitter": ["twitter.com", "x.com"]
    }

    for site, keywords in social_sites.items():
         if any(keyword in link_rawer or keyword in title_rawer for keyword in keywords):
             return site

    education_sites = {
        "Udemy": ["udemy.com"],
        "Coursera": ["coursera.org"]
    }
    for site, keywords in education_sites.items():
         if any(keyword in link_rawer or keyword in title_rawer for keyword in keywords):
             return site

    news_sites = ["cnn.com", "bbc.com", "aljazeera.net"]
    for news in news_sites:
        if news in link_rawer:
            return "News Site"

    if "mailto:" in link_rawer or "@" in title_rawer:
        return "Email Contact"

    if "tel:" in link_rawer:
        return "Phone Number"

    official_sites = [".gov", ".edu", ".org"]
    for ext in official_sites:
        if ext in link_rawer:
            return "Official/Government Site"

    if "github.com" in link_rawer or "gitlab.com" in link_rawer:
        return "Code Repository"

    return "Website"

def osint_ex(query, num_pages=1):
    all_results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        search_url = f"https://duckduckgo.com/?q={query}&ia=web"
        page.goto(search_url, timeout=60000, wait_until="domcontentloaded")
        
       
        for i in range(num_pages):
            try:
                page.wait_for_selector('article', state="attached", timeout=20000)
                results = page.query_selector_all('article')
                for result in results:
                    try:
                        title_element = result.query_selector('h2 a')
                        link_element = result.query_selector('h2 a')
                        image_element = result.query_selector('img')

                        if title_element and link_element:
                            title = title_element.inner_text()
                            link = link_element.get_attribute('href')
                            image = image_element.get_attribute('src') if image_element else ""
                            site_type = classify_site(link, title)
                            all_results.append({
                                "title": title,
                                "link": link,
                                "image": image,
                                "type": site_type
                            })
                    except:
                        continue

                next_button = page.query_selector('button#more-results')
                if next_button:
                    next_button.click()
                    page.wait_for_timeout(4000)
                else:
                    break
            except:
                break
        browser.close()
        return all_results

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    query = request.form['query']
    num_pages = int(request.form.get('num_pages', 1))
    num_pages = max(1, min(num_pages, 10)) 
    results = osint_ex(query, num_pages)
    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)