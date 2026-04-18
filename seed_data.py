import random
from datetime import date, timedelta
from django.utils import timezone
from django.db import transaction

from apps.authentication.models import User
from apps.projects.models import (
    Category, Tag, Project, Image,
    ProjectRating, Comment, CommentReport, ProjectReport,
)
from apps.donations.models import Donation


# ─── Helpers ──────────────────────────────────────────────────────────────────

def rand_date_past(days_back=365):
    """Random date in the past."""
    return date.today() - timedelta(days=random.randint(1, days_back))

def rand_date_future(days_ahead=365):
    """Random date in the future."""
    return date.today() + timedelta(days=random.randint(1, days_ahead))


# ─── Data Pools ───────────────────────────────────────────────────────────────

CATEGORIES_DATA = [
    "Technology",
    "Education",
    "Healthcare",
    "Environment",
    "Arts & Culture",
    "Community",
    "Food & Agriculture",
    "Sports & Fitness",
    "Social Impact",
    "Science & Research",
]

TAGS_DATA = [
    "ai", "machine-learning", "open-source", "mobile", "web",
    "sustainability", "renewable-energy", "solar", "wildlife", "ocean",
    "youth", "women", "rural", "urban", "egypt",
    "africa", "startup", "nonprofit", "research", "innovation",
    "education", "health", "mental-health", "food", "water",
    "blockchain", "iot", "robotics", "3d-printing", "vr",
]

FIRST_NAMES = [
    "Ahmed", "Mohamed", "Sara", "Nour", "Omar",
    "Layla", "Hassan", "Yasmin", "Karim", "Dina",
    "Tarek", "Rania", "Khaled", "Mona", "Amir",
    "Hana", "Youssef", "Iman", "Sherif", "Nadia",
]

LAST_NAMES = [
    "Ibrahim", "Hassan", "Ali", "Mostafa", "Khalil",
    "Mansour", "Farouk", "Nasser", "Salah", "Abdel",
    "Zaki", "Rizk", "Samir", "Fawzy", "Gaber",
    "Ramadan", "Othman", "Bakr", "Hafez", "Younis",
]

COUNTRIES = ["Egypt", "Saudi Arabia", "UAE", "Jordan", "Kuwait", "Qatar", "Lebanon"]

PROJECT_TITLES = [
    "Solar Panels for Rural Schools in Upper Egypt",
    "AI-Powered Crop Disease Detection for Small Farmers",
    "Clean Water Initiative for Sinai Villages",
    "Open Source Arabic NLP Library",
    "Mobile Clinic for Remote Communities",
    "Urban Rooftop Garden Network",
    "Inclusive Sports Academy for Disabled Youth",
    "Women Coding Bootcamp - Free Tuition",
    "Ocean Plastic Cleanup — Red Sea Campaign",
    "Mental Health Hotline for University Students",
    "3D-Printed Prosthetic Limbs at Zero Cost",
    "Digital Library for Underserved Schools",
    "Beekeeping Cooperative in Fayoum",
    "Blockchain-Based Land Registry Pilot",
    "Community Makerspace — Cairo East",
    "Reforestation of Wadi Al-Rayan",
    "Street Art Festival — Alexandria 2025",
    "Free STEM Workshops for Girls Age 10–16",
    "Aquaponics Farm — Sustainable Protein Source",
    "Refugee Children Education Program",
    "IoT Smart Irrigation System for Smallholders",
    "Low-Cost Diagnostic Kit for Malaria",
    "Podcast Network for Arabic Science Content",
    "VR History Tour — Ancient Egyptian Sites",
    "Wheelchair Accessibility Ramps — City Center",
    "Youth Orchestra — Marginalized Communities",
    "Compost-to-Biogas Plant — Garbage Crisis Solution",
    "Free Legal Aid Clinic — Online Platform",
    "Microfinance App for Informal Workers",
    "Community Kitchen — Food Waste Reduction",
    "Drone Delivery for Remote Pharmacy Needs",
    "Autism Sensory Room — Public Library",
    "Elderly Care Robot Companion — Prototype",
    "Local Artisan E-Commerce Platform",
    "Zero-Emission Felucca — Nile Tourism",
    "Coding Club for Prison Rehabilitation",
    "Oral History Archive — Egyptian Oral Traditions",
    "Anti-Bullying App for Middle Schools",
    "Seed Library — Preserving Heirloom Varieties",
    "Night School for Working Adults",
    "Smart Bin Network — Waste Segregation",
    "Fencing Academy for Low-Income Athletes",
    "Arabic Braille Publishing Initiative",
    "Renewable Energy Cooperative — Delta Region",
    "Community Mental Health Garden",
    "Free Dental Clinic — Mobile Unit",
    "Women Safety Alert App",
    "Cultural Exchange Program — Egypt & Africa",
    "Pediatric Cancer Support Group Platform",
    "AI Tutoring Bot for Arabic Students",
]

PROJECT_DETAILS_TEMPLATES = [
    (
        "We are building {title} to address a critical gap in our community. "
        "Over the last three years, we have seen a growing need for this type of initiative. "
        "Your donation will directly fund equipment, training, and operational costs for the first year. "
        "We have partnered with local government bodies and NGOs to ensure sustainability. "
        "Every pound donated brings us one step closer to launching."
    ),
    (
        "{title} is a grassroots movement started by a team of passionate volunteers. "
        "We believe that access to resources should not depend on where you were born. "
        "This campaign funds our first operational phase — reaching 500 beneficiaries directly. "
        "We are fully transparent: 80%% of funds go directly to the program, 20%% to operational costs. "
        "Join us in making change happen."
    ),
    (
        "The story behind {title} started with a simple question: why is this problem still unsolved? "
        "After six months of research and community consultation, we designed a scalable solution. "
        "This crowdfunding campaign is our first step. With your support, we will pilot in 3 governorates "
        "and publish all results openly. Success means replication across the country."
    ),
]

COMMENT_POOL = [
    "This is exactly what our community needs. Thank you for starting this!",
    "I donated and I'm proud. Please keep us updated on milestones.",
    "How can I volunteer? I have relevant skills to offer.",
    "Been waiting for something like this. Shared with all my contacts.",
    "The team behind this is incredibly dedicated. Full support from me.",
    "Any updates on when the pilot phase starts?",
    "Is there a way to follow progress after the campaign ends?",
    "I work in this field and I can confirm this approach is sound.",
    "Small donation from me — hope it helps. Keep going!",
    "Would love to see a partnership with universities on this.",
    "This solves a problem I see every day at work. Well done.",
    "Just shared this on LinkedIn. Let's get this funded!",
    "Excellent concept. The execution plan seems realistic too.",
    "When will you release the detailed budget breakdown?",
    "Can organizations donate on behalf of a company?",
]


# ─── Main Seed Function ────────────────────────────────────────────────────────

@transaction.atomic
def run_seed():
    print("=" * 60)
    print("🌱  Starting Crowdfund Seed Script")
    print("=" * 60)

    # ── 1. Users ──────────────────────────────────────────────────
    print("\n[1/7] Creating users...")

    all_users = []

    # Admin users
    for i in range(1, 4):
        email = f"admin{i}@crowdfund.dev"
        if not User.objects.filter(email=email).exists():
            user = User.objects.create_superuser(
                email=email,
                password="Admin@1234",
                first_name=f"Admin{i}",
                last_name="User",
                mobile_number=f"0100000000{i}",
                is_activated=True,
            )
            user.joined_at = timezone.now()
            user.save(update_fields=["joined_at"])
            print(f"  ✓ Admin: {email}")
        else:
            user = User.objects.get(email=email)
        all_users.append(user)

    # Regular users
    used_phones = set(User.objects.values_list("mobile_number", flat=True))
    phone_counter = 10
    for i in range(1, 21):
        email = f"user{i}@crowdfund.dev"
        if not User.objects.filter(email=email).exists():
            # Generate unique phone
            while True:
                phone = f"010{str(phone_counter).zfill(8)}"
                if phone not in used_phones:
                    used_phones.add(phone)
                    break
                phone_counter += 1

            user = User.objects.create_user(
                email=email,
                password="User@1234",
                first_name=random.choice(FIRST_NAMES),
                last_name=random.choice(LAST_NAMES),
                mobile_number=phone,
                country=random.choice(COUNTRIES),
                is_activated=True,
                role="user",
            )
            user.joined_at = timezone.now() - timedelta(days=random.randint(10, 400))
            user.save(update_fields=["joined_at"])
            phone_counter += 1
        else:
            user = User.objects.get(email=email)
        all_users.append(user)

    print(f"  → Total users: {len(all_users)}")

    # ── 2. Categories ─────────────────────────────────────────────
    print("\n[2/7] Creating categories...")
    categories = []
    for name in CATEGORIES_DATA:
        cat, created = Category.objects.get_or_create(name=name)
        categories.append(cat)
        if created:
            print(f"  ✓ Category: {name}")
    print(f"  → Total categories: {len(categories)}")

    # ── 3. Tags ───────────────────────────────────────────────────
    print("\n[3/7] Creating tags...")
    tags = []
    for name in TAGS_DATA:
        tag, created = Tag.objects.get_or_create(name=name)
        tags.append(tag)
    print(f"  → Total tags: {len(tags)}")

    # ── 4. Projects ───────────────────────────────────────────────
    print("\n[4/7] Creating projects...")
    projects = []
    statuses = ["pending"] * 35 + ["finished"] * 7 + ["canceled"] * 5 + ["banned"] * 3

    for i, title in enumerate(PROJECT_TITLES):
        if Project.objects.filter(title=title).exists():
            projects.append(Project.objects.get(title=title))
            continue

        project_status = statuses[i % len(statuses)]
        target = round(random.uniform(5000, 200000), 2)

        # current_money based on status
        if project_status == "finished":
            current_money = target + round(random.uniform(0, 5000), 2)
        elif project_status == "canceled":
            current_money = round(random.uniform(0, target * 0.24), 2)
        elif project_status == "banned":
            current_money = round(random.uniform(0, target * 0.5), 2)
        else:  # pending
            current_money = round(random.uniform(0, target * 0.9), 2)

        start = rand_date_past(180)
        end = start + timedelta(days=random.randint(30, 365))

        details = random.choice(PROJECT_DETAILS_TEMPLATES).format(title=title)

        project = Project.objects.create(
            title=title,
            details=details,
            target=target,
            current_money=current_money,
            start_date=start,
            end_date=end,
            status=project_status,
            category=random.choice(categories),
            user=random.choice(all_users[3:]),   # regular users only as owners
            is_featured=(i % 7 == 0),           # every 7th project is featured
        )

        # Assign 2–5 random tags
        project_tags = random.sample(tags, k=random.randint(2, 5))
        project.tags.set(project_tags)

        projects.append(project)

    print(f"  → Total projects: {len(projects)}")

    # ── 5. Ratings ────────────────────────────────────────────────
    print("\n[5/7] Creating ratings and comments...")
    rating_count = 0
    comment_count = 0

    for project in projects:
        # Between 3 and 12 raters per project
        raters = random.sample(all_users, k=random.randint(3, min(12, len(all_users))))
        for rater in raters:
            if rater != project.user:  # owner shouldn't rate own project
                ProjectRating.objects.get_or_create(
                    project=project,
                    user=rater,
                    defaults={"stars": random.randint(1, 5)},
                )
                rating_count += 1

        # Between 2 and 8 comments per project
        commenters = random.sample(all_users, k=random.randint(2, min(8, len(all_users))))
        top_level_comments = []

        for commenter in commenters:
            comment = Comment.objects.create(
                project=project,
                user=commenter,
                content=random.choice(COMMENT_POOL),
                parent=None,
            )
            top_level_comments.append(comment)
            comment_count += 1

        # Add a few replies to some top-level comments
        for top_comment in random.sample(top_level_comments, k=min(2, len(top_level_comments))):
            replier = random.choice(all_users)
            Comment.objects.create(
                project=project,
                user=replier,
                content=random.choice(COMMENT_POOL),
                parent=top_comment,
            )
            comment_count += 1

    print(f"  → Total ratings: {rating_count}")
    print(f"  → Total comments: {comment_count}")

    # ── 6. Donations ──────────────────────────────────────────────
    print("\n[6/7] Creating donations...")
    donation_count = 0

    pending_projects = [p for p in projects if p.status == "pending"]
    finished_projects = [p for p in projects if p.status == "finished"]

    for project in pending_projects + finished_projects:
        donors = random.sample(all_users, k=random.randint(3, 10))
        for donor in donors:
            if donor != project.user:
                amount = round(random.uniform(50, 2000), 2)
                Donation.objects.create(
                    project=project,
                    user=donor,
                    amount=amount,
                )
                donation_count += 1

    print(f"  → Total donations: {donation_count}")

    # ── 7. Reports ────────────────────────────────────────────────
    print("\n[7/7] Creating reports (for moderation testing)...")
    report_count = 0

    # Report a few projects
    reportable_projects = random.sample(projects, k=min(8, len(projects)))
    for project in reportable_projects:
        reporters = random.sample(all_users, k=random.randint(1, 3))
        for reporter in reporters:
            if reporter != project.user:
                ProjectReport.objects.get_or_create(
                    project=project,
                    user=reporter,
                )
                report_count += 1

    # Report a few comments
    all_comments = list(Comment.objects.filter(parent=None)[:30])
    for comment in random.sample(all_comments, k=min(10, len(all_comments))):
        reporters = random.sample(all_users, k=random.randint(1, 2))
        for reporter in reporters:
            if reporter != comment.user:
                CommentReport.objects.get_or_create(
                    comment=comment,
                    user=reporter,
                )
                report_count += 1

    print(f"  → Total reports: {report_count}")

    # ── Summary ───────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("✅  Seed complete! Summary:")
    print(f"   Users      : {User.objects.count()}")
    print(f"   Categories : {Category.objects.count()}")
    print(f"   Tags       : {Tag.objects.count()}")
    print(f"   Projects   : {Project.objects.count()}")
    print(f"   Ratings    : {ProjectRating.objects.count()}")
    print(f"   Comments   : {Comment.objects.count()}")
    print(f"   Donations  : {Donation.objects.count()}")
    print(f"   Reports    : {ProjectReport.objects.count() + CommentReport.objects.count()}")
    print("=" * 60)
    print("\n🔑  Login credentials:")
    print("   Admin  → admin1@crowdfund.dev / Admin@1234")
    print("   User   → user1@crowdfund.dev  / User@1234")
    print("=" * 60)


# ─── Entry Point ──────────────────────────────────────────────────────────────
run_seed() 
