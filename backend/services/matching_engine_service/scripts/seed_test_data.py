import asyncio
import asyncpg
import uuid
from datetime import datetime, timedelta

# Database connection
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "user": "talentai_dev",
    "password": "dev_password_123",
    "database": "talentai_matching",
}


async def seed_data():
    conn = await asyncpg.connect(**DB_CONFIG)

    print("Seeding test data...")

    try:
        # Create test job IDs
        job_ids = [uuid.uuid4() for _ in range(3)]
        candidate_ids = [uuid.uuid4() for _ in range(10)]

        print("\nTest Jobs:")
        for i, job_id in enumerate(job_ids, 1):
            print(f"  Job {i}: {job_id}")

        print("\nTest Candidates:")
        for i, cand_id in enumerate(candidate_ids, 1):
            print(f"  Candidate {i}: {cand_id}")

        # Match scores data
        matches = [
            # Job 1 - Senior Python Engineer
            {
                "candidate_id": candidate_ids[0],
                "job_id": job_ids[0],
                "overall_score": 0.92,
                "skill_score": 0.95,
                "exp_score": 0.90,
                "loc_score": 1.0,
                "sal_score": 0.85,
                "tier": "TIER_1",
                "confidence": 0.94,
                "rec": "STRONG_HIRE",
                "explanation": "Exceptional match: 8+ years Python, FastAPI expert, AWS certified",
                "strengths": "Python, FastAPI, PostgreSQL, Docker, Kubernetes, AWS, CI/CD",
                "gaps": "Limited Azure experience",
            },
            {
                "candidate_id": candidate_ids[1],
                "job_id": job_ids[0],
                "overall_score": 0.78,
                "skill_score": 0.82,
                "exp_score": 0.75,
                "loc_score": 0.80,
                "sal_score": 0.75,
                "tier": "TIER_2",
                "confidence": 0.81,
                "rec": "HIRE",
                "explanation": "Strong match: 5 years Python, good system design knowledge",
                "strengths": "Python, Django, REST APIs, MySQL, Redis, Git",
                "gaps": "No FastAPI experience, limited cloud deployment",
            },
            {
                "candidate_id": candidate_ids[2],
                "job_id": job_ids[0],
                "overall_score": 0.65,
                "skill_score": 0.60,
                "exp_score": 0.70,
                "loc_score": 1.0,
                "sal_score": 0.60,
                "tier": "TIER_3",
                "confidence": 0.73,
                "rec": "CONSIDER",
                "explanation": "Moderate match: Junior developer, eager to learn",
                "strengths": "Python basics, Django, PostgreSQL, Linux",
                "gaps": "Limited production experience, no async programming",
            },
            # Job 2 - ML Engineer
            {
                "candidate_id": candidate_ids[3],
                "job_id": job_ids[1],
                "overall_score": 0.88,
                "skill_score": 0.90,
                "exp_score": 0.85,
                "loc_score": 0.90,
                "sal_score": 0.85,
                "tier": "TIER_1",
                "confidence": 0.89,
                "rec": "STRONG_HIRE",
                "explanation": "Excellent ML engineer: PhD in ML, 6 years industry experience",
                "strengths": "TensorFlow, PyTorch, Scikit-learn, MLOps, Python, Ray",
                "gaps": "Limited healthcare domain experience",
            },
            {
                "candidate_id": candidate_ids[4],
                "job_id": job_ids[1],
                "overall_score": 0.72,
                "skill_score": 0.75,
                "exp_score": 0.68,
                "loc_score": 0.75,
                "sal_score": 0.70,
                "tier": "TIER_2",
                "confidence": 0.76,
                "rec": "HIRE",
                "explanation": "Good ML background: Masters degree, 3 years experience",
                "strengths": "Scikit-learn, Pandas, NumPy, Computer Vision",
                "gaps": "Limited deep learning production experience",
            },
            # Job 3 - Full Stack Developer
            {
                "candidate_id": candidate_ids[5],
                "job_id": job_ids[2],
                "overall_score": 0.85,
                "skill_score": 0.88,
                "exp_score": 0.82,
                "loc_score": 1.0,
                "sal_score": 0.80,
                "tier": "TIER_1",
                "confidence": 0.87,
                "rec": "STRONG_HIRE",
                "explanation": "Versatile full-stack developer: 7 years, modern tech stack",
                "strengths": "React, Node.js, Python, AWS, Docker, Microservices",
                "gaps": "No mobile development experience",
            },
        ]

        # Insert match scores
        insert_count = 0
        for match in matches:
            await conn.execute(
                """
                INSERT INTO match_scores (
                    id, candidate_id, job_id, overall_score,
                    skill_score, experience_score, location_score, salary_score,
                    ml_quality_tier, ml_confidence, recommendation,
                    explanation, strengths, gaps,
                    chroma_used, processing_time_ms, created_at, expires_at
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18
                )
            """,
                uuid.uuid4(),
                match["candidate_id"],
                match["job_id"],
                match["overall_score"],
                match["skill_score"],
                match["exp_score"],
                match["loc_score"],
                match["sal_score"],
                match["tier"],
                match["confidence"],
                match["rec"],
                match["explanation"],
                match["strengths"],
                match["gaps"],
                True,  # chroma_used
                int(100 + (match["overall_score"] * 200)),  # processing_time_ms
                datetime.now() - timedelta(days=1),  # created_at
                datetime.now() + timedelta(days=30),  # expires_at
            )
            insert_count += 1

        print(f"\nInserted {insert_count} match scores")

        # Insert ML model (skip if exists)
        model_id = uuid.uuid4()
        try:
            await conn.execute(
                """
                INSERT INTO ml_models (
                    id, model_name, model_version, model_type,
                    accuracy, precision, recall, f1_score,
                    training_date, deployment_date, is_active
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11
                )
                ON CONFLICT (model_name, model_version) DO NOTHING
            """,
                model_id,
                "quality_scorer_rf",
                "1.2.0",
                "random_forest",
                0.82,
                0.79,
                0.85,
                0.82,
                datetime.now() - timedelta(days=30),
                datetime.now() - timedelta(days=7),
                True,
            )
            print(f"\nInserted ML model: {model_id}")
        except Exception:
            print("\nML model already exists, skipping...")

        print("\nTest data seeded successfully!")
        print("\nUse these IDs for testing:")
        print("\nJobs:")
        for i, jid in enumerate(job_ids, 1):
            print(f"    {i}. {jid}")
        print("\nTop Candidates:")
        for i in range(min(5, len(candidate_ids))):
            print(f"    {i+1}. {candidate_ids[i]}")

        # Show what we created
        count = await conn.fetchval("SELECT COUNT(*) FROM match_scores")
        print(f"\nTotal match scores in DB: {count}")

    except Exception as e:
        print(f"\nError: {e}")
        raise
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(seed_data())
