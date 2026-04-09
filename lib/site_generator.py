"""Generate portfolio site HTML from parsed LinkedIn data."""
import html


def _esc(text):
    return html.escape(str(text)) if text else ""


def _lang_percent(level):
    """Convert language level to percentage for bar."""
    level_lower = (level or "").lower()
    if "native" in level_lower or "bilingual" in level_lower or "nativ" in level_lower or "bilingue" in level_lower:
        return 100
    if "full professional" in level_lower or "fluent" in level_lower:
        return 90
    if "professional" in level_lower or "profissional" in level_lower:
        return 80
    if "limited working" in level_lower or "intermedi" in level_lower:
        return 50
    if "elementary" in level_lower or "elementar" in level_lower or "básico" in level_lower:
        return 30
    return 50


def _generate_experience_html(experience):
    items = []
    for exp in experience:
        desc_html = ""
        if exp.get("description"):
            desc_html = f'<p class="text-gray-700 dark:text-gray-300 text-sm">{_esc(exp["description"])}</p>'
        loc_html = ""
        if exp.get("location"):
            loc_html = f'<p class="text-sm text-gray-500 dark:text-gray-400 mb-3">{_esc(exp["location"])}</p>'
        items.append(f"""
                <div class="relative mb-8 fade-in-section">
                    <div class="timeline-dot"></div>
                    <div class="bg-white dark:bg-gray-800 rounded-2xl p-6 shadow-sm interactive-card">
                        <div class="flex flex-col sm:flex-row sm:justify-between sm:items-start mb-2">
                            <div>
                                <h3 class="text-lg font-bold text-gray-900 dark:text-white">{_esc(exp["role"])}</h3>
                                <p class="text-primary-500 font-semibold">{_esc(exp["company"])}</p>
                            </div>
                            <span class="text-sm text-gray-500 dark:text-gray-400 mt-1 sm:mt-0 whitespace-nowrap">{_esc(exp["date"])}</span>
                        </div>
                        {loc_html}
                        {desc_html}
                    </div>
                </div>""")
    return "\n".join(items)


def _generate_education_html(education):
    icons = ["🎓", "🏫", "📚", "🎓", "🏫"]
    items = []
    for i, edu in enumerate(education):
        icon = icons[i % len(icons)]
        date_html = ""
        if edu.get("date"):
            date_html = f'<p class="text-sm text-gray-500 dark:text-gray-400">{_esc(edu["date"])}</p>'
        course_html = ""
        if edu.get("course"):
            course_html = f'<p class="text-primary-500 font-medium">{_esc(edu["course"])}</p>'
        items.append(f"""
                <div class="bg-white dark:bg-gray-800 rounded-2xl p-6 shadow-sm interactive-card">
                    <div class="flex items-start">
                        <span class="text-2xl mr-4 mt-1">{icon}</span>
                        <div>
                            <h3 class="font-bold text-gray-900 dark:text-white">{_esc(edu["school"])}</h3>
                            {course_html}
                            {date_html}
                        </div>
                    </div>
                </div>""")
    return "\n".join(items)


def _generate_languages_html(languages):
    flags = {
        "português": "🇵🇹", "portuguese": "🇵🇹", "portugheză": "🇵🇹",
        "inglês": "🇬🇧", "english": "🇬🇧", "engleză": "🇬🇧",
        "espanhol": "🇪🇸", "spanish": "🇪🇸", "spaniolă": "🇪🇸",
        "francês": "🇫🇷", "french": "🇫🇷", "franceză": "🇫🇷",
        "alemão": "🇩🇪", "german": "🇩🇪", "germană": "🇩🇪",
        "italiano": "🇮🇹", "italian": "🇮🇹",
        "romeno": "🇷🇴", "romanian": "🇷🇴", "română": "🇷🇴",
        "russo": "🇷🇺", "russian": "🇷🇺", "rusă": "🇷🇺",
        "ucraniano": "🇺🇦", "ukrainian": "🇺🇦", "ucraineană": "🇺🇦",
        "chinês": "🇨🇳", "chinese": "🇨🇳", "mandarim": "🇨🇳", "mandarin": "🇨🇳",
        "japonês": "🇯🇵", "japanese": "🇯🇵",
        "coreano": "🇰🇷", "korean": "🇰🇷",
        "árabe": "🇸🇦", "arabic": "🇸🇦",
        "hindi": "🇮🇳",
        "holandês": "🇳🇱", "dutch": "🇳🇱",
        "polaco": "🇵🇱", "polish": "🇵🇱",
        "turco": "🇹🇷", "turkish": "🇹🇷",
        "sueco": "🇸🇪", "swedish": "🇸🇪",
    }
    items = []
    for lang in languages:
        name = lang["name"]
        level = lang.get("level", "")
        flag = flags.get(name.lower(), "🌐")
        pct = _lang_percent(level)
        items.append(f"""
                    <div>
                        <div class="flex justify-between mb-1">
                            <span class="font-medium">{flag} {_esc(name)}</span>
                            <span class="text-sm text-gray-500 dark:text-gray-400">{_esc(level)}</span>
                        </div>
                        <div class="lang-bar"><div class="lang-fill" style="width: {pct}%"></div></div>
                    </div>""")
    return "\n".join(items)


def _generate_skills_html(skills):
    colors = [
        ("primary-100", "primary-700", "primary-900/30", "primary-300"),
        ("accent-100", "accent-700", "accent-900/30", "accent-300"),
        ("purple-100", "purple-700", "purple-900/30", "purple-300"),
        ("amber-100", "amber-700", "amber-900/30", "amber-300"),
    ]
    items = []
    for i, skill in enumerate(skills):
        bg, text, dbg, dt = colors[i % len(colors)]
        items.append(
            f'<span class="skill-tag bg-{bg} text-{text} dark:bg-{dbg} dark:text-{dt}">{_esc(skill)}</span>'
        )
    return "\n                        ".join(items)


def _generate_certifications_html(certifications):
    items = []
    for cert in certifications:
        items.append(f"""
                <div class="bg-white dark:bg-gray-800 rounded-2xl p-6 shadow-sm interactive-card">
                    <div class="flex items-center">
                        <span class="text-2xl mr-4">📜</span>
                        <h3 class="font-bold text-gray-900 dark:text-white">{_esc(cert)}</h3>
                    </div>
                </div>""")
    return "\n".join(items)


def generate_portfolio_html(data, photo_filename="photo.png", cv_filename="cv.pdf"):
    """Generate complete portfolio HTML from parsed data."""
    name = _esc(data.get("name", ""))
    title = _esc(data.get("title", ""))
    location = _esc(data.get("location", ""))
    email = _esc(data.get("email", ""))
    linkedin = data.get("linkedin", "")
    summary = _esc(data.get("summary", ""))
    domain = data.get("domain", "")

    experience_html = _generate_experience_html(data.get("experience", []))
    education_html = _generate_education_html(data.get("education", []))
    languages_html = _generate_languages_html(data.get("languages", []))
    skills_html = _generate_skills_html(data.get("skills", []))
    certifications = data.get("certifications", [])
    certs_html = _generate_certifications_html(certifications)

    # Build sections conditionally
    certs_section = ""
    if certifications:
        certs_section = f"""
        <section class="fade-in-section mb-12">
            <h2 class="text-2xl font-bold mb-6 flex items-center">
                <span class="w-8 h-1 bg-gradient-to-r from-primary-500 to-accent-500 rounded-full mr-3"></span>
                <span>Certificações</span>
            </h2>
            <div class="space-y-4">
                {certs_html}
            </div>
        </section>"""

    summary_section = ""
    if summary:
        summary_section = f"""
        <section id="about" class="fade-in-section mb-12">
            <h2 class="text-2xl font-bold mb-6 flex items-center">
                <span class="w-8 h-1 bg-gradient-to-r from-primary-500 to-accent-500 rounded-full mr-3"></span>
                <span>Sobre Mim</span>
            </h2>
            <div class="bg-white dark:bg-gray-800 rounded-2xl p-6 sm:p-8 shadow-sm interactive-card">
                <p class="text-gray-700 dark:text-gray-300 leading-relaxed text-justify">{summary}</p>
            </div>
        </section>"""

    skills_section = ""
    if data.get("skills"):
        skills_section = f"""
        <section id="skills" class="fade-in-section mb-12">
            <h2 class="text-2xl font-bold mb-6 flex items-center">
                <span class="w-8 h-1 bg-gradient-to-r from-primary-500 to-accent-500 rounded-full mr-3"></span>
                <span>Competências</span>
            </h2>
            <div class="bg-white dark:bg-gray-800 rounded-2xl p-6 shadow-sm interactive-card">
                <div class="flex flex-wrap gap-2">
                    {skills_html}
                </div>
            </div>
        </section>"""

    languages_section = ""
    if data.get("languages"):
        languages_section = f"""
        <section id="languages" class="fade-in-section mb-12">
            <h2 class="text-2xl font-bold mb-6 flex items-center">
                <span class="w-8 h-1 bg-gradient-to-r from-primary-500 to-accent-500 rounded-full mr-3"></span>
                <span>Idiomas</span>
            </h2>
            <div class="bg-white dark:bg-gray-800 rounded-2xl p-6 sm:p-8 shadow-sm interactive-card">
                <div class="space-y-5">
                    {languages_html}
                </div>
            </div>
        </section>"""

    experience_section = ""
    if data.get("experience"):
        experience_section = f"""
        <section id="experience" class="fade-in-section mb-12">
            <h2 class="text-2xl font-bold mb-6 flex items-center">
                <span class="w-8 h-1 bg-gradient-to-r from-primary-500 to-accent-500 rounded-full mr-3"></span>
                <span>Experiência Profissional</span>
            </h2>
            <div class="relative pl-10">
                <div class="timeline-line"></div>
                {experience_html}
            </div>
        </section>"""

    education_section = ""
    if data.get("education"):
        education_section = f"""
        <section id="education" class="fade-in-section mb-12">
            <h2 class="text-2xl font-bold mb-6 flex items-center">
                <span class="w-8 h-1 bg-gradient-to-r from-primary-500 to-accent-500 rounded-full mr-3"></span>
                <span>Formação Académica</span>
            </h2>
            <div class="space-y-4">
                {education_html}
            </div>
        </section>"""

    # Contact section
    linkedin_btn = ""
    if linkedin:
        linkedin_btn = f"""
                    <a href="{_esc(linkedin)}" target="_blank" rel="noopener noreferrer"
                       class="inline-flex items-center px-6 py-3 bg-[#0077B5] text-white rounded-full font-medium hover:bg-[#005f8d] transition-colors">
                        <svg class="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 24 24"><path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/></svg>
                        LinkedIn
                    </a>"""

    email_btn = ""
    if email:
        email_btn = f"""
                    <a href="mailto:{email}"
                       class="inline-flex items-center px-6 py-3 bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-gray-200 rounded-full font-medium hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors">
                        <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/></svg>
                        {email}
                    </a>"""

    cv_btn = f"""
                    <a href="{_esc(cv_filename)}" download
                       class="inline-flex items-center px-6 py-3 bg-gradient-to-r from-primary-500 to-accent-500 text-white rounded-full font-medium hover:from-primary-600 hover:to-accent-600 transition-all">
                        <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
                        Download CV
                    </a>"""

    # Navigation links
    nav_links = []
    if summary:
        nav_links.append('<a href="#about" class="text-sm font-medium hover:text-primary-500 transition-colors">Sobre</a>')
    if data.get("experience"):
        nav_links.append('<a href="#experience" class="text-sm font-medium hover:text-primary-500 transition-colors">Experiência</a>')
    if data.get("skills"):
        nav_links.append('<a href="#skills" class="text-sm font-medium hover:text-primary-500 transition-colors">Competências</a>')
    if data.get("education"):
        nav_links.append('<a href="#education" class="text-sm font-medium hover:text-primary-500 transition-colors">Formação</a>')
    if data.get("languages"):
        nav_links.append('<a href="#languages" class="text-sm font-medium hover:text-primary-500 transition-colors">Idiomas</a>')
    nav_links.append('<a href="#contact" class="text-sm font-medium hover:text-primary-500 transition-colors">Contacto</a>')
    nav_html = "\n                    ".join(nav_links)

    return f"""<!DOCTYPE html>
<html lang="pt" class="">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{name} | Portfolio</title>
    <meta name="description" content="{name} - {title}">
    <link rel="icon" href="{_esc(photo_filename)}" type="image/png">
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <script>
        tailwind.config = {{
            darkMode: 'class',
            theme: {{
                extend: {{
                    fontFamily: {{ sans: ['Inter', 'sans-serif'] }},
                    colors: {{
                        primary: {{ 50:'#f0f4ff',100:'#e0e7ff',200:'#c7d2fe',300:'#a5b4fc',400:'#818cf8',500:'#4f63d2',600:'#3b4fb8',700:'#2e3f8f',800:'#1e2a6e',900:'#1a2255' }},
                        accent: {{ 50:'#f0f9ff',100:'#e0f2fe',200:'#bae6fd',300:'#7dd3fc',400:'#38bdf8',500:'#0ea5e9',600:'#0284c7',700:'#0369a1',800:'#075985',900:'#0c4a6e' }}
                    }}
                }}
            }}
        }}
    </script>
    <style>
        body {{ font-family:'Inter',sans-serif; background-color:#f0f4ff; transition:background-color .3s,color .3s; }}
        html.dark body {{ background-color:#1a1a2e; }}
        .sticky-nav {{ position:sticky;top:0;z-index:50;backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px); }}
        .interactive-card {{ transition:transform .3s,box-shadow .3s; }}
        .interactive-card:hover {{ transform:translateY(-5px);box-shadow:0 20px 40px rgba(0,0,0,.1); }}
        html.dark .interactive-card:hover {{ box-shadow:0 20px 40px rgba(0,0,0,.3); }}
        .fade-in-section {{ opacity:0;transform:translateY(20px);transition:opacity .6s ease-out,transform .6s ease-out; }}
        .fade-in-section.is-visible {{ opacity:1;transform:translateY(0); }}
        .timeline-line {{ position:absolute;left:1.25rem;top:0;bottom:0;width:2px;background:linear-gradient(to bottom,#4f63d2,#0ea5e9); }}
        html.dark .timeline-line {{ background:linear-gradient(to bottom,#3b4fb8,#0284c7); }}
        .timeline-dot {{ width:12px;height:12px;border-radius:50%;background:linear-gradient(135deg,#4f63d2,#0ea5e9);position:absolute;left:calc(1.25rem - 5px);top:.5rem;z-index:1; }}
        .skill-tag {{ display:inline-block;padding:.375rem .875rem;border-radius:9999px;font-size:.8125rem;font-weight:500;transition:all .2s; }}
        .skill-tag:hover {{ transform:scale(1.05); }}
        .lang-bar {{ height:8px;border-radius:4px;background:#e5e7eb;overflow:hidden; }}
        html.dark .lang-bar {{ background:#374151; }}
        .lang-fill {{ height:100%;border-radius:4px;background:linear-gradient(90deg,#4f63d2,#0ea5e9);transition:width 1s; }}
        @media print {{ .no-print{{display:none!important}} .fade-in-section{{opacity:1;transform:none}} }}
    </style>
</head>
<body class="text-gray-800 dark:text-gray-200 min-h-screen">
    <nav class="sticky-nav bg-white/80 dark:bg-gray-900/80 shadow-sm no-print">
        <div class="max-w-6xl mx-auto px-4 sm:px-6">
            <div class="flex justify-between items-center h-16">
                <a href="#" class="text-lg font-bold bg-gradient-to-r from-primary-500 to-accent-500 bg-clip-text text-transparent">{name}</a>
                <div class="hidden md:flex items-center space-x-6">
                    {nav_html}
                    <button id="darkToggle" onclick="toggleDarkMode()" class="p-2 rounded-full hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors">
                        <svg id="sunIcon" class="w-5 h-5 hidden" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"/></svg>
                        <svg id="moonIcon" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"/></svg>
                    </button>
                </div>
                <button class="md:hidden p-2 rounded-md hover:bg-gray-200 dark:hover:bg-gray-700" onclick="document.getElementById('mobileMenu').classList.toggle('hidden')">
                    <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"/></svg>
                </button>
            </div>
            <div id="mobileMenu" class="hidden md:hidden pb-4 space-y-2">
                {nav_html}
                <button onclick="toggleDarkMode()" class="p-2 rounded-full hover:bg-gray-200 dark:hover:bg-gray-700">
                    <svg class="w-5 h-5 dark:hidden" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"/></svg>
                    <svg class="w-5 h-5 hidden dark:block" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"/></svg>
                </button>
            </div>
        </div>
    </nav>
    <main class="max-w-6xl mx-auto px-4 sm:px-6 py-8">
        <section class="fade-in-section text-center py-12">
            <div class="mx-auto mb-6 rounded-full overflow-hidden" style="width:220px;height:220px;border:4px solid #4f63d2;box-shadow:0 0 30px rgba(79,99,210,0.3)">
                <img src="{_esc(photo_filename)}" alt="{name}" style="width:100%;height:100%;object-fit:cover;object-position:center 15%;transform:scale(1.35)">
            </div>
            <h1 class="text-4xl sm:text-5xl font-bold mb-3 bg-gradient-to-r from-primary-600 to-accent-500 bg-clip-text text-transparent">{name}</h1>
            <p class="text-xl text-gray-600 dark:text-gray-400 mb-2">{title}</p>
            <p class="text-sm text-gray-500 dark:text-gray-500">{location}</p>
        </section>
        {summary_section}
        {experience_section}
        {skills_section}
        {certs_section}
        {education_section}
        {languages_section}
        <section id="contact" class="fade-in-section mb-12">
            <h2 class="text-2xl font-bold mb-6 flex items-center">
                <span class="w-8 h-1 bg-gradient-to-r from-primary-500 to-accent-500 rounded-full mr-3"></span>
                <span>Contacto</span>
            </h2>
            <div class="bg-white dark:bg-gray-800 rounded-2xl p-6 sm:p-8 shadow-sm interactive-card text-center">
                <p class="text-lg text-gray-700 dark:text-gray-300 mb-6">Interessado em entrar em contacto?</p>
                <div class="flex flex-col sm:flex-row items-center justify-center gap-4">
                    {linkedin_btn}
                    {cv_btn}
                    {email_btn}
                </div>
            </div>
        </section>
    </main>
    <footer class="text-center py-6 text-sm text-gray-500 dark:text-gray-400 border-t border-gray-200 dark:border-gray-800">
        <p>&copy; 2026 {name}. Todos os direitos reservados.</p>
    </footer>
    <script>
        function toggleDarkMode(){{const d=document.documentElement.classList.toggle('dark');localStorage.setItem('theme',d?'dark':'light');const s=document.getElementById('sunIcon'),m=document.getElementById('moonIcon');if(s&&m){{s.classList.toggle('hidden',!d);m.classList.toggle('hidden',d)}}}}
        (function(){{const s=localStorage.getItem('theme'),p=window.matchMedia('(prefers-color-scheme:dark)').matches,d=s==='dark'||(!s&&p);if(d)document.documentElement.classList.add('dark');const sun=document.getElementById('sunIcon'),moon=document.getElementById('moonIcon');if(sun&&moon){{sun.classList.toggle('hidden',!d);moon.classList.toggle('hidden',d)}}
        const o=new IntersectionObserver(e=>{{e.forEach(e=>{{if(e.isIntersecting)e.target.classList.add('is-visible')}});}},{{threshold:.1}});document.querySelectorAll('.fade-in-section').forEach(el=>o.observe(el));
        document.querySelectorAll('a[href^="#"]').forEach(a=>{{a.addEventListener('click',function(e){{e.preventDefault();const t=document.querySelector(this.getAttribute('href'));if(t)t.scrollIntoView({{behavior:'smooth',block:'start'}})}});}});}})();
    </script>
</body>
</html>"""
