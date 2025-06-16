import json
import re
import random
from typing import Dict, List, Tuple

# ---------- CONFIGURABLE QUESTION TEMPLATES ----------
SECTION_QUESTIONS = {
    "1": [
        "What is the immediate action a driver should take when seeing the '{sign}' sign?",
        "When is the '{sign}' sign typically used?",
        "What safety rule does section {section} enforce in the '{sign}' sign?"
    ],
    "2": [
        "What should a driver do at a '{sign}' when there is no stop line?",
        "How does a driver react to a '{sign}' when there's a pedestrian crossing?",
        "What does section {section} of the '{sign}' sign indicate?"
    ],
    "3": [
        "How should the driver behave in construction zones near a '{sign}'?",
        "What does the '{sign}' indicate at a railway crossing?",
        "What special caution is required in section {section} of the '{sign}' sign?"
    ],
    "4": [
        "When is it prohibited to stop near a '{sign}'?",
        "What are unsafe stopping locations for a driver near a '{sign}'?",
        "Why must a driver be extra careful around section {section} of the '{sign}' sign?"
    ]
}

GENERIC_SECTION_TEMPLATES = [
    "What does section {section} of the '{sign}' sign mean?",
    "Explain the rule under section {section} for the '{sign}' traffic sign.",
    "How should drivers behave according to section {section} of the '{sign}' sign?"
]

KEYWORD_TEMPLATES = [
    "How is '{kw}' handled when a driver encounters the '{sign}' sign?",
    "Explain why '{kw}' is important under the '{sign}' sign.",
    "What is the implication of '{kw}' for drivers near the '{sign}' sign?",
    "In what situation does '{kw}' apply under the '{sign}' sign?"
]

SCENARIO_TEMPLATES = [
    "If a driver is near a '{sign}' sign and sees '{kw}', what should they do?",
    "Describe what action should be taken if '{kw}' occurs near a '{sign}' sign.",
    "Why must a driver be cautious of '{kw}' when the '{sign}' sign is present?",
    "What could happen if a driver ignores the '{kw}' instruction under the '{sign}' sign?"
]

# ---------- CORE FUNCTIONS ----------

def extract_flowchart_sections(gt: str) -> Tuple[str, Dict[str, str]]:
    sections = {}
    sign_name_match = re.search(r'<traffic_sign name="(.+?)">', gt)
    name = sign_name_match.group(1).strip() if sign_name_match else "Unknown"
    matches = re.finditer(r'<section title="(.+?)">(.*?)(?=<section title|KEY WORDS|</traffic_sign>)', gt, re.DOTALL)
    for match in matches:
        title = match.group(1).strip()
        body = re.sub(r'\s+', ' ', match.group(2).strip())
        sections[title] = body
    return name, sections

def extract_keywords(gt: str) -> List[str]:
    try:
        keyword_match = re.search(r'KEY ?WORDS?(.*)', gt, flags=re.IGNORECASE | re.DOTALL)
        if keyword_match:
            kw_section = keyword_match.group(1)
            return re.findall(r'"(.*?)"', kw_section)
    except:
        pass
    return []

def load_handbook(filepath: str) -> List[dict]:
    with open(filepath, "r") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("Handbook data should be a list.")
    for entry in data:
        if "image" not in entry or "ground_truth" not in entry:
            raise ValueError("Each entry must contain 'image' and 'ground_truth'.")
    return data

def generate_qa_pairs(handbook_data: List[dict]) -> List[dict]:
    qa_pairs = []
    for entry in handbook_data:
        img_path = entry["image"]
        gt = entry["ground_truth"]
        try:
            sign_name, sections = extract_flowchart_sections(gt)
            keywords = extract_keywords(gt)
            for section_no, section_text in sections.items():
                templates = SECTION_QUESTIONS.get(section_no, GENERIC_SECTION_TEMPLATES)
                for q_template in templates:
                    question = q_template.format(sign=sign_name, section=section_no)
                    qa_pairs.append({
                        "image": img_path,
                        "question": question,
                        "answer": section_text
                    })

            # Keyword-based Q&A
            sampled_keywords = random.sample(keywords, min(len(keywords), 5))
            for kw in sampled_keywords:
                chosen_section = random.choice(list(sections.values())) if sections else "Refer to sign rules."
                for kw_q_template in KEYWORD_TEMPLATES + SCENARIO_TEMPLATES:
                    question = kw_q_template.format(kw=kw, sign=sign_name)
                    answer = f"In the context of the '{sign_name}' sign, the keyword '{kw}' relates to: {chosen_section}"
                    qa_pairs.append({
                        "image": img_path,
                        "question": question,
                        "answer": answer
                    })

        except Exception as e:
            print(f"❌ Skipped entry due to error: {e}")
            continue

    return qa_pairs

def main():
    try:
        handbook_data = load_handbook("handbook/handbook_dataset.json")
        qa_pairs = generate_qa_pairs(handbook_data)
        with open("handbook/generated_qa_pairs_expanded.json", "w") as out:
            json.dump(qa_pairs, out, indent=2)
        print(f"✅ Generated {len(qa_pairs)} detailed Q&A pairs.")
        print("📁 Saved to: handbook/generated_qa_pairs_expanded.json")
    except Exception as e:
        print(f"❌ Error in processing: {e}")

if __name__ == "__main__":
    main()

