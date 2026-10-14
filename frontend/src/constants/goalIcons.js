import {
  BookOpen,
  Briefcase,
  FileText,
  GraduationCap,
  Handshake,
  Microscope,
  Rocket,
  School,
  TrendingUp,
  Users,
} from 'lucide-react';

// Иконки целей по коду (только оформление: список целей и названия приходят с сервера, /api/meta/).
// Иконки первых восьми — из legacy GLS. Цель без иконки показывается без неё.
export const GOAL_ICONS = {
  friends: Users,
  study_partners: BookOpen,
  project_collaborators: Handshake,
  startup_cofounders: Rocket,
  mentorship: GraduationCap,
  research_collaboration: Microscope,
  internship_opportunities: Briefcase,
  career_networking: TrendingUp,
  cv_portfolio: FileText,
  college_prep: School,
};
