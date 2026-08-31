"""
Requirement Agent for Travel Intelligence Platform.

Responsible for:
1. Parsing natural language user input via Gemini AI.
2. Extracting structured travel parameters (dates, travelers, budget, preferences).
3. Analyzing requirements completeness.
4. Formulating clear, targeted clarification questions for missing data.
"""

import json
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.graph.state import TravelState
from app.services.gemini import get_gemini_client

# Mapping of common word numbers to integers for robust fallback parsing
WORD_TO_NUM = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "single": 1, "couple": 2, "solo": 1,
}

QUESTION_TEMPLATES = {
    "destination": "Where would you like to travel to?",
    "start_location": "Where will you be starting your journey from?",
    "travel_dates": "What dates would you like to travel (start and return dates or duration)?",
    "travelers": "How many people (adults and children) are travelling?",
    "budget": "What is your estimated total budget for this trip?",
    "transport_mode": "What is your preferred mode of transport (e.g. flight, train, car, bus)?",
    "food_preference": "Do you have any dietary or food preferences (e.g. vegetarian, vegan, non-vegetarian)?",
    "stay_preference": "What type of accommodation do you prefer (e.g. hotel, resort, homestay, hostel)?",
}


class RequirementAgent:
    """
    Requirement Agent handles extracting travel details and evaluating completeness.
    """

    @classmethod
    def evaluate_state(cls, state: TravelState) -> Dict[str, Any]:
        """
        Analyzes the current TravelState to check if mandatory travel requirements are met.
        Returns missing information list, targeted questions, and completeness boolean.
        """
        missing_fields: List[str] = []

        # 1. Starting Location
        start_loc = state.get("start_location")
        if not start_loc or not str(start_loc).strip():
            missing_fields.append("start_location")

        # 2. Destination
        dest = state.get("destination")
        if not dest or not str(dest).strip():
            missing_fields.append("destination")

        # 3. Travel Dates / Duration
        start_date = state.get("start_date")
        end_date = state.get("end_date")
        duration_days = state.get("duration_days")
        has_dates = bool(start_date and (end_date or (duration_days and duration_days > 0)))
        if not has_dates:
            missing_fields.append("travel_dates")

        # 4. Number of Travelers
        travelers = state.get("travelers")
        adults = state.get("adults")
        has_travelers = (travelers is not None and travelers > 0) or (adults is not None and adults > 0)
        if not has_travelers:
            missing_fields.append("travelers")

        # 5. Budget
        budget = state.get("budget")
        has_budget = budget is not None and float(budget) > 0
        if not has_budget:
            missing_fields.append("budget")

        is_complete = len(missing_fields) == 0

        # Generate targeted questions for missing fields
        questions = []
        if not is_complete:
            for field in missing_fields:
                if field in QUESTION_TEMPLATES:
                    questions.append(QUESTION_TEMPLATES[field])

        return {
            "requirements_complete": is_complete,
            "missing_information": missing_fields,
            "questions": questions,
            "agent_status": "requirements_collected" if is_complete else "awaiting_user_input",
        }

    @classmethod
    def extract_from_user_text(cls, user_text: str, current_state: Optional[TravelState] = None) -> Dict[str, Any]:
        """
        Extracts structured travel parameters from natural language input.
        Uses Gemini when available and configured, with robust deterministic fallback.
        """
        if not user_text or not user_text.strip():
            return {}

        extracted: Dict[str, Any] = {}
        gemini_success = False

        client = get_gemini_client()
        if client:
            try:
                prompt = cls._build_extraction_prompt(user_text, current_state)
                response = client.models.generate_content(
                    model=settings.GEMINI_MODEL,
                    contents=prompt,
                )
                response_text = getattr(response, "text", "") or ""
                extracted = cls._parse_gemini_json_response(response_text)
                if extracted:
                    gemini_success = True
            except Exception as e:
                print(f"[RequirementAgent] Gemini extraction encountered an error: {e}")

        # Fallback or augment with deterministic regex/rule parser
        if not gemini_success or not extracted:
            extracted = cls._fallback_extract_updates(user_text)
        else:
            # Reconcile / backfill any fields fallback reliably captures
            fallback_data = cls._fallback_extract_updates(user_text)
            for k, v in fallback_data.items():
                if k not in extracted or extracted[k] is None:
                    extracted[k] = v

        return cls._sanitize_extracted_updates(extracted)

    @classmethod
    def _build_extraction_prompt(cls, user_text: str, current_state: Optional[TravelState] = None) -> str:
        """
        Constructs a structured JSON extraction prompt for Gemini.
        """
        state_context = ""
        if current_state:
            state_context = f"""
Existing Trip Context:
- Origin: {current_state.get('start_location') or 'Not specified'}
- Destination: {current_state.get('destination') or 'Not specified'}
- Dates: {current_state.get('start_date')} to {current_state.get('end_date')}
- Travelers: {current_state.get('travelers') or current_state.get('adults')}
- Budget: {current_state.get('budget')} {current_state.get('currency')}
- Transport: {current_state.get('transport_mode')}
- Food: {current_state.get('food_preference')}
- Stay: {current_state.get('stay_preference')}
- Interests: {current_state.get('interests')}
"""

        return f"""
You are the Travel Requirement Agent for an intelligent travel platform.
Extract structured travel parameters from the user's message.

{state_context}

User Message:
"{user_text}"

Return ONLY a valid JSON object (no markdown, no explanations) containing only the fields mentioned or implied by the user:
{{
  "start_location": string or null,
  "destination": string or null,
  "start_date": "YYYY-MM-DD" or null,
  "end_date": "YYYY-MM-DD" or null,
  "duration_days": integer or null,
  "travelers": integer or null,
  "adults": integer or null,
  "children": integer or null,
  "budget": number or null,
  "currency": string or null,
  "transport_mode": "flight" | "train" | "car" | "bus" | "bike" | null,
  "food_preference": "vegetarian" | "non-vegetarian" | "vegan" | "no preference" | null,
  "stay_preference": "hotel" | "resort" | "homestay" | "hostel" | null,
  "interests": list of strings or null,
  "special_requirements": string or null
}}
"""

    @classmethod
    def _parse_gemini_json_response(cls, response_text: str) -> Dict[str, Any]:
        """
        Safely parses Gemini raw text into a JSON dictionary.
        Strips markdown code fences (```json ... ```) if present.
        """
        if not response_text:
            return {}

        clean_text = response_text.strip()
        if "```json" in clean_text:
            clean_text = clean_text.split("```json", 1)[1].split("```", 1)[0].strip()
        elif "```" in clean_text:
            clean_text = clean_text.split("```", 1)[1].split("```", 1)[0].strip()

        try:
            parsed = json.loads(clean_text)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            # Attempt regex search for JSON object within text
            match = re.search(r"\{.*\}", clean_text, re.DOTALL)
            if match:
                try:
                    parsed = json.loads(match.group(0))
                    if isinstance(parsed, dict):
                        return parsed
                except Exception:
                    pass
        return {}

    @classmethod
    def _fallback_extract_updates(cls, text: str) -> Dict[str, Any]:
        """
        Deterministic, robust fallback parser using regex heuristics.
        Handles dates, adult/traveler counts, budgets, preferences, and locations.
        """
        data: Dict[str, Any] = {}
        lower = text.lower()

        # 1. Budget extraction (e.g. "budget 30000", "budget is 30,000", "Rs 30000", "30000 INR")
        budget_match = re.search(r'(?:budget\s*(?:is|of|:)?\s*|inr\s*|rs\.?\s*|₹\s*)(\d[\d,]+)', lower)
        if not budget_match:
            # Standalone 4-7 digit number likely to be budget if not date
            budget_match = re.search(r'\b(\d{4,7})\b', lower)
        if budget_match:
            try:
                clean_num = budget_match.group(1).replace(",", "")
                data["budget"] = float(clean_num)
            except Exception:
                pass

        # 2. Travelers / Adults / Children
        # e.g., "2 adults", "two adults", "family of 4", "3 travelers", "1 kid", "2 children"
        adults_match = re.search(r'(\d+|one|two|three|four|five|six|seven|eight|nine|ten|couple|solo|single)\s*(?:adults?|people|persons?|pax)', lower)
        if adults_match:
            val = adults_match.group(1)
            num = WORD_TO_NUM.get(val, None)
            if num is None:
                try:
                    num = int(val)
                except ValueError:
                    num = 1
            data["adults"] = num
            data["travelers"] = num

        children_match = re.search(r'(\d+|one|two|three|four|five)\s*(?:children|kids?|child)', lower)
        if children_match:
            val = children_match.group(1)
            num = WORD_TO_NUM.get(val, None)
            if num is None:
                try:
                    num = int(val)
                except ValueError:
                    num = 0
            data["children"] = num
            if "travelers" in data:
                data["travelers"] = data["adults"] + num

        # If simply "X travelers"
        travelers_match = re.search(r'(\d+|one|two|three|four|five|six|seven|eight|nine|ten)\s*travelers?', lower)
        if travelers_match and "travelers" not in data:
            val = travelers_match.group(1)
            num = WORD_TO_NUM.get(val, None)
            if num is None:
                try:
                    num = int(val)
                except ValueError:
                    num = 1
            data["travelers"] = num
            data["adults"] = num

        # 3. Dates extraction
        # e.g. "from 10 September to 14 September", "10 Sep - 14 Sep", "2026-09-10 to 2026-09-14"
        months = ["january", "february", "march", "april", "may", "june",
                  "july", "august", "september", "october", "november", "december",
                  "jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
        months_pattern = "|".join(months)

        # Pattern: (from )?(\d{1,2}(?:st|nd|rd|th)?\s+(?:months)) (?:to|-|until) (\d{1,2}(?:st|nd|rd|th)?\s+(?:months))
        date_range_match = re.search(
            rf'(?:from\s+)?(\d{{1,2}}(?:st|nd|rd|th)?\s+(?:{months_pattern})(?:\s+\d{{4}})?)\s*(?:to|-|until)\s*(\d{{1,2}}(?:st|nd|rd|th)?\s+(?:{months_pattern})(?:\s+\d{{4}})?)',
            lower
        )
        if date_range_match:
            d1 = date_range_match.group(1).strip()
            d2 = date_range_match.group(2).strip()
            data["start_date"] = cls._normalize_date_str(d1)
            data["end_date"] = cls._normalize_date_str(d2)
        else:
            # ISO date pattern YYYY-MM-DD
            iso_dates = re.findall(r'\b(\d{4}-\d{2}-\d{2})\b', text)
            if len(iso_dates) >= 2:
                data["start_date"] = iso_dates[0]
                data["end_date"] = iso_dates[1]
            elif len(iso_dates) == 1:
                data["start_date"] = iso_dates[0]

        # 4. Duration in days
        duration_match = re.search(r'(\d+)\s*(?:days?|nights?)', lower)
        if duration_match and "duration_days" not in data:
            try:
                data["duration_days"] = int(duration_match.group(1))
            except ValueError:
                pass

        # 5. Food preference
        if "vegan" in lower:
            data["food_preference"] = "vegan"
        elif "vegetarian" in lower or "veg" in lower:
            data["food_preference"] = "vegetarian"
        elif "non-vegetarian" in lower or "non-veg" in lower:
            data["food_preference"] = "non-vegetarian"

        # 6. Stay preference
        if "resort" in lower:
            data["stay_preference"] = "resort"
        elif "homestay" in lower:
            data["stay_preference"] = "homestay"
        elif "hostel" in lower:
            data["stay_preference"] = "hostel"
        elif "hotel" in lower:
            data["stay_preference"] = "hotel"

        # 7. Transport mode
        if "flight" in lower or "air" in lower:
            data["transport_mode"] = "flight"
        elif "train" in lower or "railway" in lower:
            data["transport_mode"] = "train"
        elif "car" in lower or "drive" in lower or "road trip" in lower:
            data["transport_mode"] = "car"
        elif "bus" in lower:
            data["transport_mode"] = "bus"
        elif "bike" in lower:
            data["transport_mode"] = "bike"

        return data

    @classmethod
    def _normalize_date_str(cls, date_str: str) -> str:
        """
        Normalizes human date string (e.g. '10 September', '10th Sep 2026') into 'YYYY-MM-DD'.
        Defaults year to current or upcoming year if omitted.
        """
        clean = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', date_str).strip()
        current_year = datetime.now().year
        
        # Try different date formats
        formats = [
            "%d %B %Y", "%d %b %Y",
            "%d %B", "%d %b",
            "%B %d %Y", "%b %d %Y",
            "%B %d", "%b %d",
            "%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y"
        ]

        for fmt in formats:
            try:
                parsed = datetime.strptime(clean, fmt)
                # If format did not include year (%Y), set current_year
                if "%Y" not in fmt:
                    parsed = parsed.replace(year=current_year)
                return parsed.strftime("%Y-%m-%d")
            except ValueError:
                continue

        return date_str

    @classmethod
    def _sanitize_extracted_updates(cls, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitizes and casts extracted fields to valid types matching TravelState schema.
        """
        sanitized: Dict[str, Any] = {}

        if not isinstance(updates, dict):
            return {}

        for k, v in updates.items():
            if v is None:
                continue

            if k == "budget":
                try:
                    val = float(str(v).replace(",", ""))
                    if val > 0:
                        sanitized["budget"] = val
                except (ValueError, TypeError):
                    pass
            elif k in ("travelers", "adults", "children", "duration_days"):
                try:
                    val = int(v)
                    if val >= 0:
                        sanitized[k] = val
                except (ValueError, TypeError):
                    pass
            elif k in ("start_date", "end_date"):
                str_val = str(v).strip()
                if str_val:
                    sanitized[k] = cls._normalize_date_str(str_val)
            elif k in ("start_location", "destination", "title", "currency", "transport_mode", "food_preference", "stay_preference", "special_requirements"):
                str_val = str(v).strip()
                if str_val:
                    sanitized[k] = str_val
            elif k == "interests":
                if isinstance(v, list):
                    sanitized[k] = [str(item).strip() for item in v if str(item).strip()]
                elif isinstance(v, str):
                    sanitized[k] = [item.strip() for item in v.split(",") if item.strip()]

        # Ensure travelers / adults consistency
        if "adults" in sanitized and "travelers" not in sanitized:
            kids = sanitized.get("children", 0)
            sanitized["travelers"] = sanitized["adults"] + kids
        elif "travelers" in sanitized and "adults" not in sanitized:
            sanitized["adults"] = sanitized["travelers"]

        return sanitized
