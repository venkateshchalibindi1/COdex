from __future__ import annotations

from jobpipeline.core.models import CanonicalJob, SearchProfile
from jobpipeline.utils.text import extract_years_requirement


class FitScorer:
    def score(self, job: CanonicalJob, profile: SearchProfile, seniority_mode: str = "downrank") -> CanonicalJob:
        text = f"{job.title} {job.description_raw}".lower()
        must = [k.lower() for k in profile.must_have_keywords]
        nice = [k.lower() for k in profile.nice_to_have_keywords]

        missing = [k for k in must if k not in text]
        flags: list[str] = []
        score = 0

        must_matches = len(must) - len(missing)
        score += int((must_matches / max(1, len(must))) * 40)

        nice_matches = sum(1 for k in nice if k in text)
        score += int((nice_matches / max(1, len(nice))) * 20)

        title_match = any(t.lower() in job.title.lower() for t in profile.target_titles + profile.adjacent_titles)
        score += 20 if title_match else 5

        if profile.location_mode.lower() == "remote":
            score += 10 if job.remote_flag == "Y" else 4
        else:
            score += 6

        years = extract_years_requirement(text)
        if years is None:
            score += 6
        elif years <= profile.experience_max_years:
            score += 10
        else:
            score += 1
            flags.append("experience_mismatch")

        if "clearance" in text:
            flags.append("clearance")
            score = 0

        if any(k in text for k in ["senior", "principal", "staff"]):
            flags.append("seniority")
            if seniority_mode == "reject":
                score = 0
            else:
                score = max(0, score - 25)

        if missing:
            flags.append("missing_must_have")

        score = max(0, min(100, score))
        grade = "A" if score >= 85 else "B" if score >= 70 else "C" if score >= 55 else "D"
        notes = f"must matched {must_matches}/{len(must)}; nice matched {nice_matches}/{len(nice)}; flags={','.join(flags) or 'none'}"

        job.fit_score = score
        job.fit_grade = grade
        job.fit_notes = notes
        job.missing_must_have = missing
        job.flags = flags
        return job
