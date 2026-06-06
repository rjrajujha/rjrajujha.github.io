PROFILE = {
    "name": "Raju Jha",
    "headline": "Software Engineer building scalable backend-first products with Python, Django, and AI integrations.",
    "subheadline": (
        "I design reliable APIs, automation systems, and developer-focused platforms with a strong blend "
        "of system design, product thinking, and execution speed."
    ),
    "location": "Bihar, India",
    "core_stack": "Python, Django, FastAPI, Java/Spring Boot, React/Next.js, Tailwind CSS",
    "domain": "rjrajujha.github.io",
    "domain_url": "https://rjrajujha.github.io",
    "social_links": [
        {"label": "GitHub", "url": "https://github.com/rjrajujha"},
        {"label": "LinkedIn", "url": "https://linkedin.com/in/rjrajujha"},
    ],
}

ABOUT_POINTS = [
    "I focus on backend-heavy web architecture where performance, maintainability, and product clarity matter.",
    "My day-to-day work spans Django/FastAPI services, API design, automation workflows, and production delivery.",
    "I enjoy pairing practical AI workflows with traditional software engineering to solve real business bottlenecks.",
]

SKILL_GROUPS = [
    {
        "title": "Backend & APIs",
        "items": [
            "Python",
            "Django",
            "FastAPI",
            "Java",
            "Spring Boot",
            "Node.js",
            "Express.js",
            "REST",
            "GraphQL",
        ],
    },
    {
        "title": "Frontend & UX",
        "items": [
            "TailwindCSS",
            "HTML5",
            "CSS3",
            "React.js",
            "Next.js",
        ],
    },
    {
        "title": "Data & Infrastructure",
        "items": [
            "PostgreSQL",
            "MongoDB",
            "MySQL",
            "Docker",
            "Nginx",
            "CI/CD",
            "DNS Operations",
        ],
    },
    {
        "title": "AI & Engineering Fundamentals",
        "items": [
            "LLM Fine-tuning",
            "Ollama Workflows",
            "Prompt Design",
            "Data Structures & Algorithms",
            "Agile Delivery",
        ],
    },
]

EXPERIENCE_ITEMS = [
    {
        "company": "Devout Growth",
        "role": "Software Engineer",
        "period": "Jul 2023 - Present",
        "summary": "Owning full-stack features and platform reliability for influencer marketing products.",
        "highlights": [
            "Built and shipped an influencer marketing platform with campaign operations and analytics workflows.",
            "Implemented REST and GraphQL APIs across Next.js and FastAPI services.",
            "Improved backend throughput by 30% through algorithm and query optimization.",
        ],
    },
    {
        "company": "Internshala",
        "role": "Software Engineering Intern",
        "period": "Jan 2023 - Jun 2023",
        "summary": "Delivered practical product features in a fast feedback environment.",
        "highlights": [
            "Developed a contact management app with robust CRUD operations.",
            "Implemented structured import/export routines for better user workflows.",
        ],
    },
]

OPEN_SOURCE_PROJECTS = [
    {
        "title": "SyncWave",
        "slug": "syncwave",
        "headline": "Local-first synchronized audio rooms with LAN/WAN hosting and browser listeners.",
        "description": (
            "Open-source Flutter + FastAPI system for synchronized 48 kHz PCM audio streaming. "
            "Hosts create rooms over LAN or internet; listeners join via browser with Web Audio sync, "
            "optional WAN relay, room PINs, and binary PCM WebSocket frames."
        ),
        "stack_items": ["Dart", "Flutter", "FastAPI", "WebSockets", "Docker"],
        "impact": "Open-source · MIT · real-time audio",
        "source_url": "https://github.com/OpenCodeQuark/syncwave",
        "demo_url": "https://syncwave.rajujha.dev",
        "is_featured": True,
        "display_order": 1,
    },
    {
        "title": "spa-config-gen",
        "slug": "spa-config-gen",
        "headline": "CLI tool that generates SPA routing configs for Apache, Nginx, Caddy, Traefik, and HAProxy.",
        "description": (
            "Published npm package that outputs production-ready reverse-proxy configuration for single-page "
            "applications, including .htaccess and nginx.conf with try_files fallbacks to index.html."
        ),
        "stack_items": ["TypeScript", "Node.js", "CLI", "Nginx", "Apache"],
        "impact": "npm package · developer tooling",
        "source_url": "https://github.com/rjrajujha/spa-config-gen",
        "demo_url": "https://www.npmjs.com/package/spa-config-gen",
        "is_featured": True,
        "display_order": 2,
    },
    {
        "title": "react-native-modal-fix",
        "slug": "react-native-modal-fix",
        "headline": "Maintained drop-in fork of react-native-modal with production stability fixes.",
        "description": (
            "npm library extending React Native Modal with enter/exit animations, swipe-to-dismiss, "
            "keyboard avoidance, and compatibility fixes across React Native versions for teams blocked on upstream gaps."
        ),
        "stack_items": ["TypeScript", "React Native", "npm"],
        "impact": "Open-source library · MIT",
        "source_url": "https://github.com/rjrajujha/react-native-modal-fix",
        "demo_url": "https://www.npmjs.com/package/react-native-modal-fix",
        "is_featured": True,
        "display_order": 3,
    },
]

FALLBACK_FEATURED_PROJECTS = [
    {
        "title": "Influencer Marketing Platform",
        "slug": "influencer-marketing-platform",
        "headline": "Campaign operations and analytics workflow platform for creator-led growth teams.",
        "description": (
            "Built full-stack campaign lifecycle management with performance insights and API-first integrations "
            "for influencer campaign planning, creator management, and reporting."
        ),
        "stack_items": ["Python", "FastAPI", "Next.js", "MongoDB", "GraphQL"],
        "impact": "Production platform",
        "source_url": "",
        "demo_url": "",
        "is_featured": True,
        "display_order": 4,
    },
    {
        "title": "WhatsApp Automation Server",
        "slug": "whatsapp-automation-server",
        "headline": "Reliable messaging automation service with scheduling and event-driven delivery workflows.",
        "description": (
            "Implemented queue-safe automation flows with operational controls and real-time update patterns "
            "for scheduled messaging and delivery events."
        ),
        "stack_items": ["Node.js", "Express.js", "WebSockets", "Automation"],
        "impact": "Workflow acceleration",
        "source_url": "",
        "demo_url": "",
        "is_featured": True,
        "display_order": 5,
    },
    {
        "title": "Custom DNS Security Deployment",
        "slug": "custom-dns-security-deployment",
        "headline": "DoH/DoT-ready DNS deployment with observability and secure zone management.",
        "description": (
            "Configured secure DNS infrastructure on Ubuntu for encrypted resolution and practical network diagnostics."
        ),
        "stack_items": ["BIND9", "Pi-hole", "Ubuntu", "DoH", "DoT"],
        "impact": "Security focused",
        "source_url": "",
        "demo_url": "",
        "is_featured": False,
        "display_order": 6,
    },
    {
        "title": "LLM Text Generation Pipeline",
        "slug": "llm-text-generation-pipeline",
        "headline": "Experimental model training and fine-tuning workflow optimized for local serving.",
        "description": (
            "Created a practical experimentation pipeline for dataset prep, fine-tuning, evaluation, "
            "and export to GGUF for local deployment with Ollama."
        ),
        "stack_items": ["Python", "LLM Fine-tuning", "GGUF", "Ollama"],
        "impact": "AI enablement",
        "source_url": "",
        "demo_url": "",
        "is_featured": False,
        "display_order": 7,
    },
]

ALL_PROJECTS = OPEN_SOURCE_PROJECTS + FALLBACK_FEATURED_PROJECTS
