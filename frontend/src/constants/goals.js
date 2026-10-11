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

// Единый список целей (docs/SPEC.md §1.8) вместо двух расходящихся списков legacy.
// Иконки первых восьми — из legacy GLS.
export const GOALS = [
  { code: 'friends', label: 'Looking for friends', icon: Users },
  { code: 'study_partners', label: 'Study partners', icon: BookOpen },
  { code: 'project_collaborators', label: 'Project collaborators', icon: Handshake },
  { code: 'startup_cofounders', label: 'Startup co-founders', icon: Rocket },
  { code: 'mentorship', label: 'Mentorship', icon: GraduationCap },
  { code: 'research_collaboration', label: 'Research collaboration', icon: Microscope },
  { code: 'internship_opportunities', label: 'Internship opportunities', icon: Briefcase },
  { code: 'career_networking', label: 'Career networking', icon: TrendingUp },
  { code: 'cv_portfolio', label: 'Build CV / portfolio', icon: FileText },
  { code: 'college_prep', label: 'College application prep', icon: School },
];
