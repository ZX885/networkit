import AboutStep from './AboutStep.jsx';
import BasicInfoStep from './BasicInfoStep.jsx';
import ContactStep from './ContactStep.jsx';
import EducationStep from './EducationStep.jsx';
import GoalsStep from './GoalsStep.jsx';
import InterestsStep from './InterestsStep.jsx';
import LanguagesStep from './LanguagesStep.jsx';
import LocationStep from './LocationStep.jsx';

// Шаги мастера по порядку (индекс 0 = шаг 1)
export const STEPS = [
  BasicInfoStep,
  LocationStep,
  EducationStep,
  InterestsStep,
  LanguagesStep,
  AboutStep,
  GoalsStep,
  ContactStep,
];
