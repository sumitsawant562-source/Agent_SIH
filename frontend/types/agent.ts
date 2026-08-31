export interface RequirementData {
  trip_id: string;
  requirements_complete: boolean;
  missing_information: string[];
  questions: string[];
  start_location?: string | null;
  destination?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  duration_days?: number | null;
  travelers?: number | null;
  adults?: number | null;
  children?: number | null;
  budget?: number | null;
  currency?: string | null;
  transport_mode?: string | null;
  food_preference?: string | null;
  stay_preference?: string | null;
  interests?: string[] | null;
  special_requirements?: string | null;
}

export interface RequirementResponse {
  success: boolean;
  data: RequirementData;
}
