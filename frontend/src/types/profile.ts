export type SkillLevel = 'beginner' | 'intermediate' | 'advanced' | 'professional'
export type WeightUnit = 'kg' | 'lb'
export type Role = 'fighter' | 'coach' | 'hobbyist'

export interface ProfileCreate {
  skill_level?: SkillLevel | null
  martial_arts?: string[] | null
  goals?: string | null
  weight_class?: string | null
  training_frequency?: string | null
  injuries?: string[] | null
  role?: Role
  primary_domain?: string | null
  game_style?: string | null
  strategic_leaks?: string[] | null
  language_code?: string
  weight_unit?: WeightUnit
}

export interface ProfileUpdate {
  skill_level?: SkillLevel | null
  martial_arts?: string[] | null
  goals?: string | null
  weight_class?: string | null
  training_frequency?: string | null
  injuries?: string[] | null
  role?: Role
  primary_domain?: string | null
  game_style?: string | null
  strategic_leaks?: string[] | null
  language_code?: string
  weight_unit?: WeightUnit
}

export interface ProfileResponse {
  id: string
  user_id: string
  skill_level: string | null
  martial_arts: string[] | null
  goals: string | null
  weight_class: string | null
  training_frequency: string | null
  injuries: string[] | null
  role: string
  primary_domain: string | null
  game_style: string | null
  strategic_leaks: string[] | null
  conversation_insights: Record<string, unknown> | null
  profile_completeness: number
  language_code: string
  weight_unit: string
  current_streak: number
  longest_streak: number
  last_active_date: string | null
  grace_days_remaining: number
  created_at: string
  updated_at: string | null
}
