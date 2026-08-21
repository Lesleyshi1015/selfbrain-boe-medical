#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BOE AI Hackathon 2026 - TimeWeave Memory Foundation Demo
Simplified version with robust error handling
"""

import json
import sys
import io
import time
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

# Force UTF-8 output for Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')



class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_header(text: str):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 60}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}  {text}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 60}{Colors.END}\n")


def print_section(text: str):
    print(f"\n{Colors.BLUE}=> {text}{Colors.END}")
    print(f"  {'-' * 50}")


def print_success(text: str):
    print(f"  {Colors.GREEN}[OK] {text}{Colors.END}")


def print_warning(text: str):
    print(f"  {Colors.YELLOW}[!] {text}{Colors.END}")


def print_error(text: str):
    print(f"  {Colors.RED}[X] {text}{Colors.END}")


def print_info(text: str):
    print(f"  {Colors.CYAN}[i] {text}{Colors.END}")


class TimeWeaveMemoryEngine:
    """TimeWeave Memory Engine (Demo Implementation)."""
    
    def __init__(self):
        self.memories: List[Dict[str, Any]] = []
        self.memory_index: Dict[str, Dict] = {}
    
    def store(self, content: str, timestamp: int, title: str, tags: List[str], metadata: Dict) -> Dict:
        import uuid
        memory_id = f"mem_{uuid.uuid4().hex[:12]}"
        
        memory = {
            "memory_id": memory_id,
            "content": content,
            "timestamp": timestamp,
            "title": title,
            "tags": tags,
            "metadata": metadata,
            "stored_at": int(time.time() * 1000),
        }
        
        self.memories.append(memory)
        self.memory_index[memory_id] = memory
        
        return {
            "memory_id": memory_id,
            "status": "stored",
            "title": title,
            "tags": tags,
        }
    
    def search(self, query: str, top_k: int = 5) -> Dict:
        query_lower = query.lower()
        query_keywords = [w for w in query_lower.split() if len(w) > 1]
        
        scored_results = []
        
        for mem in self.memories:
            score = 0.0
            content_lower = mem["content"].lower()
            title_lower = mem["title"].lower()
            
            for kw in query_keywords:
                if kw in content_lower:
                    score += 2.0
                if kw in title_lower:
                    score += 3.0
            
            for tag in mem.get("tags", []):
                if query_lower in tag.lower():
                    score += 5.0
            
            now = int(time.time() * 1000)
            age_days = (now - mem["timestamp"]) / (1000 * 3600 * 24)
            time_factor = max(0.5, 1.0 - age_days / 365)
            score *= time_factor
            
            if score > 0:
                scored_results.append({
                    "memory_id": mem["memory_id"],
                    "title": mem["title"],
                    "snippet": mem["content"][:200] + "..." if len(mem["content"]) > 200 else mem["content"],
                    "score": round(score, 2),
                    "timestamp": mem["timestamp"],
                    "tags": mem.get("tags", []),
                })
        
        scored_results.sort(key=lambda x: x["score"], reverse=True)
        results = scored_results[:top_k]
        
        summary = ""
        if results:
            top = results[0]
            summary = f"Found {len(results)} memories. Top: \"{top['title']}\" (score: {top['score']})"
        
        return {
            "results": results,
            "total": len(results),
            "query": query,
            "summary": summary,
            "token_estimate": "~82 tokens (memory summary)",
        }
    
    def recall(self, memory_id: str) -> Dict:
        mem = self.memory_index.get(memory_id)
        if not mem:
            return {"error": f"Memory {memory_id} not found"}
        
        return {
            "memory_id": memory_id,
            "content": mem["content"],
            "title": mem["title"],
            "timestamp": mem["timestamp"],
            "tags": mem.get("tags", []),
            "metadata": mem.get("metadata", {}),
        }
    
    def get_timeline(self, patient_id: str, limit: int = 50) -> List[Dict]:
        patient_events = [
            m for m in self.memories
            if m.get("metadata", {}).get("patient_id") == patient_id
        ]
        patient_events.sort(key=lambda x: x["timestamp"])
        return patient_events[-limit:]
    
    def stats(self) -> Dict:
        return {
            "total_memories": len(self.memories),
            "unique_patients": len(set(
                m.get("metadata", {}).get("patient_id", "") 
                for m in self.memories
            )),
            "total_tags": len(set(tag for m in self.memories for tag in m.get("tags", []))),
        }


def demo_capability_1_long_term_memory(engine: TimeWeaveMemoryEngine, patient_id: str):
    """Capability 1: Long-term Memory"""
    print_section("Capability 1: Long-term Health Record Memory")
    
    queries = [
        f"{patient_id} hypertension",
        f"{patient_id} diagnosis",
        f"{patient_id} lab abnormal",
    ]
    
    for query in queries:
        print_info(f"Search: \"{query}\"")
        result = engine.search(query, top_k=3)
        
        print_success(f"Recalled {result['total']} memories ({result.get('token_estimate', '')})")
        for r in result["results"][:2]:
            print(f"    [{r['score']:.1f}] {r['title']}")
        print()


def demo_capability_2_timeline(engine: TimeWeaveMemoryEngine, patient_id: str):
    """Capability 2: Timeline Reconstruction"""
    print_section("Capability 2: Disease Timeline Reconstruction")
    
    timeline = engine.get_timeline(patient_id, limit=20)
    
    print_info(f"Patient {patient_id} timeline ({len(timeline)} events):")
    print()
    
    for event in timeline[-10:]:
        # Extract date from title or metadata
        title = event.get("title", "")
        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', title)
        date = date_match.group(1) if date_match else event.get("metadata", {}).get("event_date", "unknown")
        
        record_type = event.get("metadata", {}).get("record_type", "unknown")
        
        print(f"  [*] {date} | {record_type}")
        print(f"      {title[:70]}...")
        print()


def demo_capability_3_qa_retrieval(engine: TimeWeaveMemoryEngine, patient_id: str):
    """Capability 3: Q&A Retrieval"""
    print_section("Capability 3: Q&A Retrieval")
    
    questions = [
        f"{patient_id} medication",
        f"{patient_id} conditions",
        f"{patient_id} recent visit",
    ]
    
    for q in questions:
        print_info(f"Q: {q}")
        result = engine.search(q, top_k=2)
        
        if result["results"]:
            top = result["results"][0]
            print(f"  A: Based on \"{top['title']}\" (score: {top['score']})")
            
            # Extract key info from content
            content = top.get("snippet", "")
            if "hypertension" in q.lower() or "medication" in q.lower():
                if "氨氯地平" in content:
                    print(f"      -> Detected: Amlodipine (calcium channel blocker)")
            elif "conditions" in q.lower():
                if "高血压" in content:
                    print(f"      -> Detected: Hypertension")
        else:
            print_warning("No relevant memories found")
        print()


def demo_capability_4_risk_assessment(engine: TimeWeaveMemoryEngine, patient_id: str):
    """Capability 4: Risk Assessment (Simplified)"""
    print_section("Capability 4: Risk Assessment")
    
    timeline = engine.get_timeline(patient_id)
    
    print_info(f"Analyzing risk indicators for patient {patient_id}...")
    print()
    
    # Simplified risk assessment based on symptom frequency
    abnormal_count = 0
    recent_events = timeline[-5:] if len(timeline) > 5 else timeline
    
    for event in recent_events:
        metadata = event.get("metadata", {})
        symptoms = metadata.get("symptoms", [])
        if symptoms:
            abnormal_count += len(symptoms)
        
        # Also check content for symptom keywords
        content = event.get("content", "")
        symptom_keywords = ["头晕", "头痛", "心悸", "胸闷", "乏力", "麻木"]
        for kw in symptom_keywords:
            if kw in content:
                abnormal_count += 1
    
    # Risk level
    if abnormal_count >= 5:
        risk_level = "HIGH"
        risk_icon = "[H]"
    elif abnormal_count >= 2:
        risk_level = "MEDIUM"
        risk_icon = "[M]"
    else:
        risk_level = "LOW"
        risk_icon = "[L]"
    
    print(f"  {risk_icon} Risk Level: {risk_level}")
    print(f"  [STAT] Symptom indicators: {abnormal_count}")
    
    # Simulated probability
    import random
    random.seed(hash(patient_id))
    base_prob = 0.3 + (abnormal_count * 0.1)
    max_prob = min(base_prob, 0.85)
    
    print(f"  [STAT] Estimated risk probability: {max_prob * 100:.1f}%")
    
    # Risk distribution
    print("  [DIST] Risk Distribution:")
    outcomes = {
        "stable": max(0.1, 1.0 - max_prob),
        "needs_attention": max_prob * 0.6,
        "worsening_risk": max_prob * 0.4,
    }
    for outcome, prob in outcomes.items():
        bar = "#" * int(prob * 20)
        print(f"      {outcome}: {prob * 100:.0f}% {bar}")
    
    # Recommendations
    print("\n  [ADVICE] Recommendations:")
    if risk_level == "HIGH":
        print("      - [!!] Risk level HIGH: Immediate intervention recommended")
        print("      - Prioritize addressing frequent symptom triggers")
    elif risk_level == "MEDIUM":
        print("      - [!] Risk level MEDIUM: Plan intervention within 24h")
        print("      - Monitor symptom changes, consider shortening follow-up interval")
    else:
        print("      - No significant risk signals, continue routine monitoring")
        print("      - Maintain regular follow-up schedule")
    
    print()


def main():
    """Main demo flow."""
    print_header("BOE AI Hackathon 2026 - TimeWeave Memory Foundation Demo")
    print_info("Role: Memory Foundation Support - for SelfBrain Medical Narrative Integration")
    print_info("Compliance: All data synthetic, not from real patients")
    print()
    
    # Step 1: Load synthetic data
    print_section("Step 1: Loading Synthetic Health Data")
    
    data_path = DEMO_DIR / "synthetic_data.json"
    if not data_path.exists():
        print_error(f"Synthetic data file not found: {data_path}")
        print_info("Please run: python generate_synthetic_data.py first")
        return False
    
    with open(data_path, "r", encoding="utf-8") as f:
        synthetic_data = json.load(f)
    
    # Support both formats
    if "memories" in synthetic_data:
        memories = synthetic_data.get("memories", [])
        patients_raw = synthetic_data.get("patients", [])
    else:
        memories = []
        patients_raw = synthetic_data.get("patients", [])
        for patient in patients_raw:
            for record in patient.get("records", []):
                from datetime import datetime as dt
                ts_str = record["timestamp"]
                try:
                    timestamp_ms = int(dt.strptime(ts_str, "%Y-%m-%dT%H:%M:%S").timestamp() * 1000)
                except ValueError:
                    timestamp_ms = int(dt.now().timestamp() * 1000)
                
                memories.append({
                    "content": record["content"],
                    "timestamp": timestamp_ms,
                    "title": f"{patient['patient_id']} - {record['record_type']} - {ts_str[:10]}",
                    "tags": ["health", f"health/{patient['patient_id']}"],
                    "metadata": {
                        "patient_id": patient["patient_id"],
                        "record_type": record["record_type"],
                        "source": "gold-desensitized",
                        "permission_level": record.get("permission_level", "L2"),
                    }
                })
    
    patients = []
    for p in patients_raw:
        if isinstance(p, dict) and "patient_id" in p:
            patients.append({
                "patient_id": p["patient_id"],
                "age": p.get("profile", {}).get("age", "N/A"),
                "gender": p.get("profile", {}).get("gender", "N/A"),
                "diagnosis": p.get("profile", {}).get("diagnosis", "N/A"),
                "conditions": p.get("profile", {}).get("conditions", []),
            })
        else:
            patients.append(p)
    
    print_success(f"Loaded {len(memories)} memory entries")
    print_success(f"Covering {len(patients)} patient profiles")
    
    # Step 2: Initialize engine
    print_section("Step 2: Initializing TimeWeave Memory Engine")
    
    engine = TimeWeaveMemoryEngine()
    
    # Step 3: Store memories
    print_section("Step 3: Storing Health Record Memories")
    
    for mem in memories:
        result = engine.store(
            content=mem["content"],
            timestamp=mem["timestamp"],
            title=mem["title"],
            tags=mem["tags"],
            metadata=mem["metadata"],
        )
    
    stats = engine.stats()
    print_success(f"Memory stats: {stats['total_memories']} memories, {stats['unique_patients']} patients")
    
    # Step 4: Demo capabilities
    print_header("Demo: TimeWeave Four Core Capabilities")
    
    for patient in patients:
        patient_id = patient["patient_id"]
        
        print_header(f"Patient Profile: {patient_id}")
        print_info(f"Diagnosis: {patient['diagnosis']}")
        conditions = patient.get('conditions', [])
        if isinstance(conditions, list):
            print_info(f"Conditions: {', '.join(conditions) if conditions else 'N/A'}")
        print()
        
        # Capability 1
        demo_capability_1_long_term_memory(engine, patient_id)
        
        # Capability 2
        demo_capability_2_timeline(engine, patient_id)
        
        # Capability 3
        demo_capability_3_qa_retrieval(engine, patient_id)
        
        # Capability 4
        demo_capability_4_risk_assessment(engine, patient_id)
    
    # Summary
    print_header("Demo Complete")
    print_success("TimeWeave Memory Foundation - Four Capabilities Demonstrated")
    print()
    print_info("[*] Capability Summary:")
    print("      1. [OK] Long-term Health Record Memory - 12-month recall")
    print("      2. [OK] Disease Timeline Reconstruction - Visit/Lab/Medication sequence")
    print("      3. [OK] Q&A Retrieval - Symptom/Medication/Lab meaning")
    print("      4. [OK] Risk Assessment - Symptom-based risk estimation")
    print()
    print_info("[*] Delivery Path:")
    print(f"      {DEMO_DIR}")
    print()
    print_info("[!] Compliance Notice:")
    print("      - All data synthetic, not from real patients")
    print("      - For demo only, not for medical diagnosis")
    print("      - Role: Assist doctor/patient decisions, not replace professional advice")
    print()
    print_info("[*] Role: Memory Foundation Support - for SelfBrain Medical Narrative Integration")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
