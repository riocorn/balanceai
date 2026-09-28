import json
import os
import re

from core.config import settings

_CACHE: dict = {"mtime": None, "data": None, "name_index": None}


def _normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (text or "").lower()).strip()


def load_medicines() -> dict:
    path = settings.MEDICINE_DETAILS_PATH
    mtime = os.path.getmtime(path)
    if _CACHE["mtime"] == mtime and _CACHE["data"] is not None:
        return _CACHE["data"]

    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    name_index = []
    for key, v in data.get("medicines", {}).items():
        status = (v.get("research_status") or "").split(" ")[0].split("-")[0].strip()
        if status == "not_found":
            continue
        name_index.append({
            "key": key,
            "name": v.get("name", key),
            "norm": _normalize(v.get("name", key)),
            "category": v.get("category", ""),
            "diseases": v.get("used_for_diseases") or [],
        })

    _CACHE.update({"mtime": mtime, "data": data, "name_index": name_index})
    return data


def _reason(v: dict) -> str:
    for f in ("note", "not_found_reason", "research_note", "partial_note", "_note"):
        val = v.get(f)
        if val and str(val).strip():
            return str(val).strip()
    return ""


def _status(v: dict) -> str:
    s = (v.get("research_status") or "").split(" ")[0].split("-")[0].strip()
    return s if s in ("complete", "partial", "not_found") else "partial"


def _summary(key: str, v: dict) -> dict:
    return {
        "key": key,
        "name": v.get("name", key),
        "category": v.get("category", ""),
        "used_for_diseases": v.get("used_for_diseases") or [],
        "research_status": _status(v),
    }


def search_medicines(query: str, limit: int = 20) -> list:
    load_medicines()
    q = _normalize(query)
    if not q:
        return []
    q_tokens = set(q.split())

    scored = []
    for row in _CACHE["name_index"]:
        if q in row["norm"]:
            score = 100 - abs(len(row["norm"]) - len(q))
        else:
            row_tokens = set(row["norm"].split())
            overlap = len(q_tokens & row_tokens)
            if overlap == 0:
                continue
            score = overlap * 10
        scored.append((score, row))

    scored.sort(key=lambda x: -x[0])
    data = _CACHE["data"]["medicines"]
    return [_summary(r["key"], data[r["key"]]) for _, r in scored[:limit]]


def get_medicine_by_key(key: str) -> dict:
    data = load_medicines()
    v = data["medicines"].get(key)
    if not v:
        return {"found": False}

    status = _status(v)
    result = {
        "found": True,
        "key": key,
        "name": v.get("name", key),
        "category": v.get("category", ""),
        "used_for_diseases": v.get("used_for_diseases") or [],
        "research_status": status,
    }
    if status == "not_found":
        result["not_found_reason"] = _reason(v) or "Not a distinct pharmaceutical compound."
        return result

    result.update({
        "dosage_administration": v.get("dosage_administration"),
        "side_effects": v.get("side_effects"),
        "safety_advice": v.get("safety_advice"),
        "drug_interactions": v.get("drug_interactions"),
        "missed_dose_overdose": v.get("missed_dose_overdose"),
        "fact_box": v.get("fact_box"),
        "storage": v.get("storage"),
        "sources": v.get("sources") or [],
    })
    if status == "partial":
        result["note"] = _reason(v)
    return result


def get_medicines_for_disease(disease_name: str, limit: int = 30) -> list:
    load_medicines()
    q = _normalize(disease_name)
    data = _CACHE["data"]["medicines"]
    matches = []
    for row in _CACHE["name_index"]:
        for d in row["diseases"]:
            if q and q in _normalize(d):
                matches.append(_summary(row["key"], data[row["key"]]))
                break
    return matches[:limit]
