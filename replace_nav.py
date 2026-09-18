import re
import glob

css_new = '''        .global-nav {
            position: fixed;
            left: 1.5rem;
            top: 50%;
            transform: translateY(-50%);
            background: rgba(30, 41, 59, 0.7);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 16px;
            z-index: 1000;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
            transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            width: 58px;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            padding: 12px 0;
        }

        .global-nav:hover {
            width: 260px;
            background: rgba(30, 41, 59, 0.95);
        }

        .global-nav-container {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }

        .global-nav-container::-webkit-scrollbar {
            display: none;
        }

        .global-nav a {
            color: #94a3b8;
            text-decoration: none;
            font-size: 0.95rem;
            font-weight: 500;
            padding: 10px 12px;
            margin: 0 8px;
            border-radius: 10px;
            transition: all 0.2s ease;
            display: flex;
            align-items: center;
            white-space: nowrap;
            height: 44px;
        }

        .global-nav a .nav-icon {
            font-size: 1.25rem;
            margin-right: 16px;
            min-width: 1.25rem;
            text-align: center;
        }

        .global-nav a .nav-text {
            opacity: 0;
            transition: opacity 0.2s ease;
        }

        .global-nav:hover a .nav-text {
            opacity: 1;
            transition-delay: 0.1s;
        }

        .global-nav a:hover {
            color: #f8fafc;
            background: rgba(255, 255, 255, 0.1);
        }

        .global-nav a.active {
            color: #10b981;
            background: rgba(16, 185, 129, 0.15);
        }

        body {
            padding-top: 20px !important;
            padding-left: 80px !important; /* Make room for the floating bar */
        }'''

html_new = '''    <div class="global-nav">
        <div class="global-nav-container">
            <a href="/" id="nav-bioclip"><span class="nav-icon">📸</span><span class="nav-text">AI 鸟类识别 (专业离线版)</span></a>
            <a href="/index" id="nav-index"><span class="nav-icon">🌐</span><span class="nav-text">AI 鸟类识别 (在线备用版)</span></a>
            <a href="/kestrel" id="nav-kestrel"><span class="nav-icon">🏷️</span><span class="nav-text">Kestrel 批量打标</span></a>
            <a href="/publisher" id="nav-publisher"><span class="nav-icon">📝</span><span class="nav-text">Bilibili 发布助手</span></a>
        </div>
    </div>'''

files = glob.glob('*.html')
for file in files:
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Replace CSS
    css_pattern = re.compile(r'        \.global-nav \{.*?(?=    </style>)', re.DOTALL)
    content = css_pattern.sub(css_new + '\n', content)

    # Replace HTML
    html_pattern = re.compile(r'    <div class="global-nav">.*?(?=    <script>)', re.DOTALL)
    content = html_pattern.sub(html_new + '\n', content)

    with open(file, 'w', encoding='utf-8') as f:
        f.write(content)

print('Done replacing in ' + ', '.join(files))
