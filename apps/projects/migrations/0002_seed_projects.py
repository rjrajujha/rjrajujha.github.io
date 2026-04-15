from django.db import migrations


def seed_projects(apps, schema_editor):
    Project = apps.get_model("projects", "Project")

    seed_data = [
        {
            "title": "Influencer Marketing Platform",
            "slug": "influencer-marketing-platform",
            "headline": "Full-stack campaign operations suite with analytics and creator workflow automation.",
            "description": (
                "Designed and delivered a production platform for influencer campaign planning, creator management, "
                "performance tracking, and reporting. The backend architecture focused on extensible APIs, reliable "
                "data models, and scalable processing pipelines for campaign intelligence."
            ),
            "tech_stack": "Python, FastAPI, Next.js, MongoDB, GraphQL",
            "impact": "Production platform",
            "is_featured": True,
            "display_order": 1,
        },
        {
            "title": "WhatsApp Automation Server",
            "slug": "whatsapp-automation-server",
            "headline": "Real-time messaging automation backend with scheduling and event-based triggers.",
            "description": (
                "Built an automation service for WhatsApp workflows including scheduled messaging, delivery events, "
                "and operational controls. Emphasis was placed on reliability, queue-safe operations, and operator "
                "visibility through real-time updates."
            ),
            "tech_stack": "Node.js, WebSockets, Express.js, Automation",
            "impact": "Workflow acceleration",
            "is_featured": True,
            "display_order": 2,
        },
        {
            "title": "Custom DNS Security Deployment",
            "slug": "custom-dns-security-deployment",
            "headline": "DoH/DoT-ready DNS stack with observability and secure zone management.",
            "description": (
                "Engineered a custom DNS setup on Ubuntu using BIND9 and Pi-hole to support secure DNS operations, "
                "encrypted resolution paths, and practical monitoring. The implementation improved control over "
                "network traffic and diagnostics for security-focused use cases."
            ),
            "tech_stack": "BIND9, Pi-hole, Ubuntu, DNS, DoH, DoT",
            "impact": "Security focused",
            "is_featured": True,
            "display_order": 3,
        },
        {
            "title": "LLM Text Generation Pipeline",
            "slug": "llm-text-generation-pipeline",
            "headline": "Experimental model training and fine-tuning workflow optimized for local serving.",
            "description": (
                "Created an end-to-end LLM experimentation pipeline including dataset preparation, fine-tuning runs, "
                "model evaluation, and export to .gguf for local deployment with Ollama. The project emphasized "
                "practical AI adoption with reproducible engineering practices."
            ),
            "tech_stack": "Python, LLM Fine-tuning, GGUF, Ollama",
            "impact": "AI enablement",
            "is_featured": True,
            "display_order": 4,
        },
    ]

    for row in seed_data:
        Project.objects.update_or_create(slug=row["slug"], defaults=row)


def unseed_projects(apps, schema_editor):
    Project = apps.get_model("projects", "Project")
    Project.objects.filter(
        slug__in=[
            "influencer-marketing-platform",
            "whatsapp-automation-server",
            "custom-dns-security-deployment",
            "llm-text-generation-pipeline",
        ]
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("projects", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_projects, unseed_projects),
    ]
