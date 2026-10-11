import { BIO_MAX, GOALS_MAX, INTERESTS_MAX, LANGUAGES_MAX, MIN_AGE } from '../constants/rules.js';

// Все тексты интерфейса в одном месте (подготовка к i18n). Сгруппированы по страницам и фичам.
// Тексты лендинга и форм взяты из legacy index.html / app.js; изменённые утверждения помечены
// комментарием «ИЗМЕНЕНО».
export const texts = {
  common: {
    loading: 'Loading',
    optional: '(optional)',
  },

  nav: {
    label: 'Main navigation',
    features: 'Features',
    how: 'How it works',
    faq: 'FAQ',
    logIn: 'Log in',
    joinNow: 'Join now',
    openMenu: 'Open menu',
    closeMenu: 'Close menu',
    toDark: 'Switch to dark theme',
    toLight: 'Switch to light theme',
  },

  footer: {
    description:
      'For high school students, university students, graduates, and professionals. Find collaborators, co-founders, mentors, and study partners.',
    platform: 'Platform',
    signUp: 'Sign up',
    logIn: 'Log in',
    company: 'Company',
    about: 'About',
    blog: 'Blog',
    careers: 'Careers',
    legal: 'Legal',
    privacy: 'Privacy Policy',
    terms: 'Terms of Service',
    copyright: (year) => `© ${year} NetworkIt. All rights reserved.`,
    tagline: 'Built for curious minds',
  },

  legal: {
    comingSoon: 'Coming soon',
    termsTitle: 'Terms of Service',
    privacyTitle: 'Privacy Policy',
    text: 'This page is being prepared.',
    back: 'Back to home',
  },

  landing: {
    hero: {
      eyebrow: 'Connect. Build. Grow.',
      titleBefore: 'Find the right people',
      titleMiddle: 'to ',
      titleAccent: 'build with.',
      subtitle:
        "Whether you're in high school, university, or working — find collaborators, co-founders, and mentors who share your goals.",
      primaryCta: "Get started — it's free",
      secondaryCta: 'Sign in',
      statsLabel: 'Platform statistics',
      members: 'Members',
      fields: 'Fields',
      countries: 'Countries',
      statsEmpty: 'Be first!',
    },
    features: {
      eyebrow: 'Why NetworkIt',
      title: 'Everything you need to find your people',
      subtitle:
        'Built for students and professionals who want real, meaningful connections in their field.',
      items: [
        {
          icon: 'search',
          title: 'Smart search & filters',
          text: "Filter by field, city, university, goals, and languages. Find exactly who you're looking for.",
        },
        {
          icon: 'globe',
          title: 'Global & local',
          text: 'Connect with people in your city or anywhere in the world. Your reach, your choice.',
        },
        {
          icon: 'target',
          title: 'Goal-aligned',
          text: 'Looking for a study partner, co-founder, or mentor? Specify your goal and find the right match.',
        },
        {
          icon: 'message',
          title: 'Built-in messaging',
          text: "Chat directly on NetworkIt. No need to share personal contacts before you're comfortable.",
        },
        {
          icon: 'lock',
          title: 'Privacy first',
          // ИЗМЕНЕНО: legacy «Your phone number is never shown. Control exactly what appears on your public profile.»
          text: 'We never ask for your phone number. Your contacts stay hidden until you choose to share them.',
        },
        {
          icon: 'cap',
          title: 'Student & professional',
          text: "Whether you're a freshman or a seasoned expert, NetworkIt works for you.",
        },
      ],
    },
    how: {
      eyebrow: 'How it works',
      title: 'From sign-up to your first collaboration',
      steps: [
        {
          title: 'Create your profile',
          text: 'Set your status, field, goals, and what you want to build. Takes under 3 minutes.',
        },
        {
          title: 'Discover people',
          text: 'Filter by field, location, status, or goal. Find exactly who you need.',
        },
        {
          title: 'Check their profile',
          text: 'Read their bio, goals, interests, and what they want to collaborate on.',
        },
        {
          title: 'Start building together',
          text: 'Message directly on NetworkIt — no need to exchange contacts first.',
        },
      ],
    },
    faq: {
      eyebrow: 'FAQ',
      title: 'Common questions',
      items: [
        {
          q: 'Who is NetworkIt for?',
          a: 'Anyone who wants to build something — high school students, gap year students, university students, graduates, self-taught builders, and professionals. If you have goals and ambition, you belong here.',
        },
        {
          q: 'Do I need to be in university to join?',
          a: 'No. NetworkIt is open to everyone — high schoolers looking for project partners, gap year students building their CV, self-taught coders, and working professionals alike.',
        },
        {
          q: 'Is NetworkIt free to use?',
          a: 'Yes — creating a profile, discovering people, and messaging is completely free.',
        },
        {
          q: 'What can I use NetworkIt for?',
          a: 'Finding a co-founder for your startup idea, building projects for your CV or college application, finding study partners, getting mentorship, research collaboration, or simply networking in your field.',
        },
        {
          q: 'Is my personal information safe?',
          // ИЗМЕНЕНО: legacy «Yes. Your phone number is never shown publicly. You control exactly what
          // appears on your profile — location, university, and social links can all be hidden in Privacy Settings.»
          a: 'Yes. We never ask for your phone number, and your email and date of birth are never shown to other users. Your contacts stay hidden until you choose to share them, and you can hide your location and university in Privacy Settings.',
        },
        {
          q: 'Can I control what others can see on my profile?',
          a: 'Yes. In Settings → Privacy you choose which fields are visible: location, university, social links, join date, and whether you appear in search results at all.',
        },
        {
          q: 'How does NetworkIt prevent fake accounts?',
          // ИЗМЕНЕНО: legacy «Registration requires a verified email address. Users can report…»
          a: 'You must confirm your email address with a link we send you before your account becomes active. Users can report suspicious profiles for our team to review.',
        },
        {
          q: 'Can I delete my account?',
          // ИЗМЕНЕНО: legacy «…This permanently removes your profile and all your data.»
          a: 'Yes. Go to Settings → Danger zone → Delete account. This permanently removes your profile, your photo, your saved profiles, and your conversations.',
        },
      ],
    },
    cta: {
      title: 'Ready to start building?',
      text: 'Join high schoolers, students, graduates, and professionals already finding collaborators on NetworkIt.',
      button: "Get started — it's free",
    },
  },

  login: {
    title: 'Welcome back',
    subtitle: 'Sign in to your account',
    google: 'Continue with Google',
    googleSoon: 'Google sign-in is coming soon',
    divider: 'or continue with email',
    email: 'Email',
    emailPlaceholder: 'you@example.com',
    password: 'Password',
    passwordPlaceholder: 'Your password',
    forgot: 'Forgot password?',
    submit: 'Sign in',
    noAccount: 'No account?',
    createOne: 'Create one',
    errors: {
      emailRequired: 'Enter your email',
      emailInvalid: 'Please enter a valid email',
      passwordRequired: 'Enter your password',
      invalidCredentials: 'Incorrect email or password',
      network: 'Something went wrong. Please try again.',
    },
    welcome: (name) => `Welcome back, ${name}!`,
  },

  forgot: {
    title: 'Reset password',
    description: "Enter your email and we'll send a reset link.",
    email: 'Email',
    emailPlaceholder: 'you@email.com',
    cancel: 'Cancel',
    send: 'Send link',
    emailRequired: 'Enter your email',
    // Одинаковый текст в любом случае — защита от перебора адресов (как в legacy)
    sent: "If that email has an account, we've sent a reset link.",
    failed: 'Something went wrong. Please try again.',
  },

  register: {
    stepOf: (step, total) => `Step ${step} of ${total}`,
    progress: 'Registration progress',
    back: 'Back',
    home: 'Home',
    next: 'Continue',
    submit: 'Create account',
    submitFailed: 'Something went wrong. Please try again.',
    stepNames: [
      'Basic info',
      'Location',
      'Education',
      'Interests',
      'Languages',
      'About',
      'Goals',
      'Contact',
    ],
    steps: [
      { title: 'Basic information', subtitle: 'Tell us a little about yourself.' },
      { title: 'Where are you based?', subtitle: 'Help others find people near them.' },
      { title: 'Education & career', subtitle: 'Help others find people at the same stage.' },
      { title: 'Your interests', subtitle: `Pick up to ${INTERESTS_MAX}.` },
      { title: 'Languages you speak', subtitle: 'Help find people you can talk to.' },
      { title: 'About you', subtitle: 'Write a short bio. The first thing people see.' },
      { title: 'What are your goals?', subtitle: `Select up to ${GOALS_MAX}.` },
      {
        title: 'Contact details',
        // ИЗМЕНЕНО: legacy «Your phone number is private and only for verification. Optional links appear as buttons on your profile.»
        subtitle:
          'All optional. Your contacts stay hidden until you choose to show them in Privacy Settings.',
      },
    ],
    fields: {
      firstName: 'First name',
      firstNamePlaceholder: 'Jane',
      lastName: 'Last name',
      lastNamePlaceholder: 'Doe',
      username: 'Username',
      usernamePlaceholder: 'janedoe99',
      usernameHint: '3–30 characters: lowercase letters, digits and _, starting with a letter.',
      usernameChecking: 'Checking availability…',
      usernameAvailable: 'This username is available',
      email: 'Email',
      emailPlaceholder: 'you@example.com',
      password: 'Password',
      passwordPlaceholder: 'At least 8 characters',
      birthDate: 'Date of birth',
      day: 'Day',
      month: 'Month',
      year: 'Year',
      birthHint: 'Day · Month · Year',
      gender: 'Gender',
      country: 'Country',
      countryPlaceholder: 'Select country',
      region: 'Region / State',
      regionPlaceholder: 'e.g. Bavaria',
      city: 'City',
      cityPlaceholder: 'e.g. Munich',
      status: 'Status',
      school: 'School',
      university: 'University',
      universityPlaceholder: 'e.g. MIT, Oxford',
      field: 'Field / Major',
      fieldPlaceholder: 'Select field',
      fieldOther: 'Your field',
      fieldOtherPlaceholder: 'e.g. Archaeology',
      yearLevel: 'Year / Level',
      yearLevelPlaceholder: 'e.g. 2nd Year, Masters',
      interests: 'Interests',
      languages: 'Languages',
      goals: 'Goals',
      bio: `Bio (max ${BIO_MAX} characters)`,
      bioPlaceholder: "Tell others who you are, what you study, and what you're passionate about…",
      telegram: 'Telegram',
      telegramPlaceholder: '@username',
      instagram: 'Instagram',
      instagramPlaceholder: '@username',
      whatsapp: 'WhatsApp',
      whatsappPlaceholder: '+1 555 000 0000',
      linkedin: 'LinkedIn',
      linkedinPlaceholder: 'linkedin.com/in/…',
      publicEmail: 'Public email',
      publicEmailPlaceholder: 'contact@you.com',
    },
    contactsMinor:
      'Contact links are available from age 18. You can finish registration without them.',
    terms: {
      before: 'I agree to the ',
      terms: 'Terms',
      and: ' and ',
      privacy: 'Privacy Policy',
      newTab: '(opens in a new tab)',
    },
    checkEmail: {
      title: 'Check your email',
      text: (email) =>
        `We sent a confirmation link to ${email}. Open it to activate your account, then log in.`,
      back: 'Back to login',
    },
  },

  // Тексты ошибок валидации (коды возвращает features/auth/validation.js)
  validation: {
    required: 'This field is required',
    nameInvalid: 'Use letters, spaces, hyphens, apostrophes or dots only (up to 60 characters)',
    usernameFormat: 'Use 3–30 characters: lowercase letters, digits and _, starting with a letter',
    usernameReserved: 'This username is not available',
    usernameTaken: 'This username is already taken',
    usernameChecking: 'Please wait, checking the username…',
    emailInvalid: 'Please enter a valid email',
    passwordShort: 'Password must be at least 8 characters',
    passwordLong: 'Password is too long',
    dateRequired: 'Please enter your date of birth (day, month, year)',
    dateInvalid: 'This date does not exist',
    dateFuture: 'Date of birth cannot be in the future',
    dateTooOld: 'Please check the year of birth',
    tooYoung: `You must be at least ${MIN_AGE} years old to join`,
    tooLong: 'This is too long',
    tooManyInterests: `Choose up to ${INTERESTS_MAX} interests`,
    tooManyLanguages: `Choose up to ${LANGUAGES_MAX} languages`,
    tooManyGoals: `Choose up to ${GOALS_MAX} goals`,
    telegramInvalid: 'Telegram: 5–32 letters, digits or _',
    instagramInvalid: 'Instagram: up to 30 letters, digits, dots or _',
    whatsappInvalid: 'WhatsApp: international format, e.g. +998901234567',
    linkedinInvalid: 'LinkedIn: use a link like linkedin.com/in/your-name',
    termsRequired: 'You need to accept the Terms and Privacy Policy to continue',
  },
};
