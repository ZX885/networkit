// Все тексты интерфейса в одном месте (подготовка к i18n). Сгруппированы по страницам и фичам.
// Тексты лендинга и форм взяты из legacy index.html / app.js; изменённые утверждения помечены
// комментарием «ИЗМЕНЕНО».
export const texts = {
  common: {
    loading: 'Loading',
    optional: '(optional)',
    showPassword: 'Show password',
    hidePassword: 'Hide password',
  },

  // Индикатор силы пароля (components/ui/PasswordStrength.jsx); формула — lib/passwordStrength.js
  passwordStrength: {
    prefix: 'Password strength:',
    levels: { weak: 'Weak', medium: 'Medium', strong: 'Strong' },
    hints: {
      minLength: 'Use at least 8 characters',
      addClass: 'Add a number, a capital letter or a symbol',
      moreVariety: 'Use at least 4 different characters',
      addSymbolOrNumber: 'Add a capital letter, a number or a symbol to make it stronger',
      moreLength: 'Use 12 or more characters to make it stronger',
    },
  },

  nav: {
    label: 'Main navigation',
    features: 'Features',
    how: 'How it works',
    faq: 'FAQ',
    logIn: 'Log in',
    joinNow: 'Join now',
    openApp: 'Open app',
    logOut: 'Log out',
    loggedOut: "You've been logged out",
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
          // ИЗМЕНЕНО: legacy «…field, city, university, goals, and languages…» (фильтра по вузу в MVP нет)
          text: "Filter by field, city, status, goals, and languages. Find exactly who you're looking for.",
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
    email: 'Email',
    emailPlaceholder: 'you@example.com',
    password: 'Password',
    passwordPlaceholder: 'Your password',
    submit: 'Sign in',
    noAccount: 'No account?',
    createOne: 'Create one',
    errors: {
      emailRequired: 'Enter your email',
      emailInvalid: 'Please enter a valid email',
      passwordRequired: 'Enter your password',
    },
    welcome: (name) => `Welcome back, ${name}!`,
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
      { title: 'Your interests', subtitle: (limits) => `Pick up to ${limits.interests_max}.` },
      { title: 'Languages you speak', subtitle: 'Help find people you can talk to.' },
      { title: 'About you', subtitle: 'Write a short bio. The first thing people see.' },
      { title: 'What are your goals?', subtitle: (limits) => `Select up to ${limits.goals_max}.` },
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
      usernameUnknown: "Couldn't check availability right now. We'll check it when you finish.",
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
      yearLevel: 'Year / Level',
      yearLevelPlaceholder: 'e.g. 2nd Year, Masters',
      interests: 'Interests',
      languages: 'Languages',
      goals: 'Goals',
      bio: (max) => `Bio (max ${max} characters)`,
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

  // Повторная отправка письма с подтверждением (экран «Check your email», вход, отдельная страница)
  resend: {
    button: 'Resend email',
    // Одинаковый текст для любого адреса: так нельзя узнать, зарегистрирован ли email
    sent: 'If the email is registered, we sent a link.',
    wait: (seconds) => `Resend email (${seconds}s)`,
  },

  verifyEmail: {
    checking: 'Confirming your email…',
    successTitle: 'Email confirmed',
    successText: 'Your account is active. You can log in now.',
    logIn: 'Log in',
    errorTitle: "We couldn't confirm your email",
    invalidText: 'This link is invalid or has expired. Request a new one.',
    requestNew: 'Request a new link',
    retry: 'Try again',
  },

  // Сброс пароля (страницы /forgot-password и /reset-password/:uid/:token)
  passwordReset: {
    forgotLink: 'Forgot password?',
    forgot: {
      title: 'Reset your password',
      subtitle: 'Enter your email and we will send you a link to choose a new password.',
      email: 'Email',
      emailPlaceholder: 'you@example.com',
      emailRequired: 'Enter your email',
      emailInvalid: 'Please enter a valid email',
      submit: 'Send reset link',
      again: 'Send again',
      wait: (seconds) => `Send again in ${seconds}s`,
      sent: 'If the email is registered, we sent a link',
      back: 'Back to login',
    },
    reset: {
      title: 'Choose a new password',
      subtitle: 'Pick a password of at least Medium strength.',
      newPassword: 'New password',
      newPasswordPlaceholder: 'Your new password',
      submit: 'Change password',
      successTitle: 'Password changed',
      successText: 'You can log in with your new password now.',
      logIn: 'Log in',
      invalidTitle: "This link doesn't work",
      invalidText: 'The link is invalid, has expired or was already used. Request a new one.',
      requestNew: 'Request a new link',
    },
  },

  // Подтверждение новой почты по ссылке (/confirm-email-change/:token)
  confirmEmailChange: {
    checking: 'Confirming your new email…',
    successTitle: 'Email changed',
    successText: 'Your new email address is confirmed.',
    goSettings: 'Go to settings',
    logIn: 'Log in',
    errorTitle: "We couldn't confirm your new email",
    invalidText:
      'This link is invalid, has expired or was already used. Request the change again in Settings.',
    retry: 'Try again',
  },

  resendPage: {
    title: 'Request a new link',
    subtitle: 'Enter your email and we will send a new confirmation link.',
    email: 'Email',
    emailPlaceholder: 'you@example.com',
    emailRequired: 'Enter your email',
    back: 'Back to login',
  },

  // Временная страница профиля (TEMP, заменим в шаге F3)
  // Оболочка приложения после входа (сайдбар, общие тексты)
  app: {
    nav: {
      label: 'App navigation',
      discover: 'Discover',
      myProfile: 'My profile',
      messages: 'Messages',
      saved: 'Saved profiles',
      settings: 'Settings',
      logOut: 'Log out',
      openMenu: 'Open menu',
      closeMenu: 'Close menu',
      themeLabel: 'Theme',
      themeSystem: 'System',
      themeLight: 'Light',
      themeDark: 'Dark',
      unread: (count) => `${count} new`,
    },
    notFoundTitle: 'Page not found',
    notFoundText: "This page doesn't exist.",
    notFoundAction: 'Back to Discover',
    back: 'Back',
    loading: 'Loading',
    errorTitle: 'Something went wrong',
    metaErrorTitle: "Couldn't load the form data",
    metaIncomplete: 'The server sent incomplete data. Please try again in a moment',
    errorText: 'The page could not be shown. Reloading usually helps.',
    reload: 'Reload',
    supportHint: 'If this keeps happening, please contact support',
    retry: 'Try again',
    saved: 'Saved',
  },

  // Discover (данные — GET /api/profiles/)
  discover: {
    title: 'Discover people',
    searchLabel: 'Search people',
    searchPlaceholder: 'Name, field, university…',
    filtersShow: 'Filters',
    filtersLabel: 'Filters',
    country: 'Country',
    allCountries: 'All countries',
    city: 'City',
    allCities: 'All cities',
    field: 'Field',
    allFields: 'All fields',
    status: 'Status',
    allStatuses: 'All',
    goal: 'Goal',
    anyGoal: 'Any goal',
    language: 'Language',
    anyLanguage: 'Any language',
    clearAll: 'Clear all',
    found: (count) => (count === 1 ? '1 person found' : `${count} people found`),
    loadingList: 'Loading people',
    emptyTitle: 'No people found',
    emptyText: 'Try a different search or clear the filters.',
    pagination: {
      label: 'Pagination',
      prev: 'Previous page',
      next: 'Next page',
      page: (number) => `Page ${number}`,
    },
  },

  // Карточка человека (Discover и Saved)
  card: {
    viewProfile: 'View profile',
    save: (name) => `Save ${name}`,
    unsave: (name) => `Remove ${name} from saved`,
    savedToast: 'Profile saved',
    unsavedToast: 'Removed from saved',
  },

  // Saved
  saved: {
    title: 'Saved profiles',
    emptyTitle: 'No saved profiles yet',
    emptyText: 'Tap the bookmark on a profile in Discover to keep it here.',
    emptyAction: 'Go to Discover',
    limitReached: (max) =>
      max ? `You can save up to ${max} profiles` : 'You have reached the limit of saved profiles',
  },

  // Страница профиля (/me и /u/:username)
  profile: {
    myTitle: 'My profile',
    edit: 'Edit profile',
    share: 'Share profile',
    shareDone: 'Profile link copied',
    shareFailed: "Couldn't copy the link",
    save: 'Save',
    saved: 'Saved',
    joined: (date) => `Joined ${date}`,
    about: 'About',
    goals: 'Goals',
    interests: 'Interests',
    details: 'Details',
    languages: 'Languages',
    noBio: 'No bio yet.',
    noBioAction: 'Add one',
    labels: {
      status: 'Status',
      year: 'Year',
      region: 'Region',
      country: 'Country',
      joined: 'Joined',
    },
    contactLabels: {
      telegram: 'Telegram',
      instagram: 'Instagram',
      whatsapp: 'WhatsApp',
      linkedin: 'LinkedIn',
      public_email: 'Email',
    },
    notFoundTitle: 'Profile not found',
    notFoundText: "This profile doesn't exist or isn't available.",
    loading: 'Loading profile',
  },

  // Редактирование профиля (форма без отправки до шага B4)
  editProfile: {
    title: 'Edit profile',
    basic: 'Basic information',
    firstName: 'First name',
    lastName: 'Last name',
    username: 'Username',
    usernameHint: "Username can't be changed",
    field: 'Field / Major',
    university: 'University',
    country: 'Country',
    city: 'City',
    yearLevel: 'Year / Level',
    yearLevelPlaceholder: 'e.g. Grade 11, Gap Year, 2nd Year, Senior Dev',
    bio: 'Bio',
    bioLimit: (max) => `(max ${max} chars)`,
    bioCount: (length, max) => `${length}/${max}`,
    contacts: 'Social links',
    contactsMinor: 'Contacts are not available for users under 18.',
    contactPlaceholders: {
      telegram: '@username',
      instagram: '@username',
      whatsapp: 'Phone number',
      linkedin: 'linkedin.com/in/…',
      public_email: 'contact@you.com',
    },
    interests: 'Interests',
    languages: 'Languages',
    goals: 'Goals',
    save: 'Save changes',
    cancel: 'Cancel',
    saved: 'Profile saved',
    noChanges: 'No changes to save',
    generalError: 'Some fields need attention',
  },

  // Настройки (UI; сохранение подключим позже)
  settings: {
    title: 'Settings',
    navLabel: 'Settings sections',
    tabs: { account: 'Account', privacy: 'Privacy', security: 'Security', danger: 'Danger' },
    account: {
      title: 'Account settings',
      subtitle: 'Your display name and username.',
      displayName: 'Display name',
      username: 'Username',
      readOnly: "Can't be changed in this version",
    },
    security: {
      title: 'Security',
      subtitle: 'Change your password or your email address.',
      password: {
        title: 'Change password',
        old: 'Current password',
        new: 'New password',
        repeat: 'Repeat new password',
        submit: 'Change password',
        mismatch: 'The passwords do not match',
        success: 'Password changed. Other sessions were signed out.',
      },
      email: {
        title: 'Change email',
        current: (email) => `Current email: ${email}`,
        newEmail: 'New email',
        newEmailPlaceholder: 'new@example.com',
        newEmailRequired: 'Enter the new email',
        newEmailInvalid: 'Please enter a valid email',
        password: 'Your password',
        submit: 'Change email',
        sent: 'Check your new email to confirm',
        note: 'Your email changes only after you open the link we send to the new address.',
      },
    },
    danger: {
      title: 'Danger zone',
      subtitle: 'Actions here cannot be undone.',
      deleteTitle: 'Delete account',
      deleteText: 'Your profile, saved profiles and conversations will be deleted for good.',
      deleteButton: 'Delete my account',
      modalTitle: 'Delete your account?',
      modalIntro: 'This will permanently delete:',
      willDelete: [
        'Your profile and everything on it',
        'Your saved profiles',
        'Your conversations and messages (they disappear for the other people too)',
      ],
      password: 'Your password',
      confirmLabel: 'Type DELETE to confirm',
      confirmWord: 'DELETE',
      cancel: 'Cancel',
      confirm: 'Delete account',
      deletedToast: 'Your account was deleted',
    },
    privacy: {
      title: 'Privacy settings',
      subtitle: 'Control what others can see on your profile.',
      showLocation: 'Show location',
      showLocationHint: 'Display your city and country',
      showUniversity: 'Show university',
      showUniversityHint: 'Display your university',
      showContacts: 'Show contacts',
      showContactsHint: 'Make Telegram, LinkedIn, etc. visible',
      showContactsMinor: 'Not available for users under 18.',
      showInSearch: 'Appear in search',
      showInSearchHint: 'Let others find you in Discover',
      showJoinDate: 'Show join date',
      showJoinDateHint: 'Display when you joined',
    },
  },

  // Выбор города в формах (регистрация, редактирование профиля)
  location: {
    select: 'Select city',
    other: 'Other',
    otherLabel: 'Your city',
    otherPlaceholder: 'Type your city',
  },

  // Сообщения (шаг B7): пока заглушка
  messages: {
    title: 'Messages',
    tabsLabel: 'Conversation folders',
    tabs: { chats: 'Chats', requests: 'Requests', sent: 'Sent' },
    listLabel: 'Conversations',
    searchPlaceholder: 'Search conversations…',
    searchLabel: 'Search conversations',
    empty: {
      chats: {
        title: 'No chats yet',
        text: 'Accepted conversations appear here. Find someone in Discover and send a message request.',
      },
      requests: {
        title: 'No message requests',
        text: 'When someone asks to chat with you, their request will appear here.',
      },
      sent: {
        title: 'No sent requests',
        text: 'Requests you send wait here until the person replies.',
      },
      noMatches: 'No conversations match your search.',
    },
    noSelectionTitle: 'Your messages',
    noSelectionText: 'Pick a conversation to read it and reply.',
    viewProfile: 'View profile',
    back: 'Back to conversations',
    you: 'You: ',
    unread: (count) => `${count} unread messages`,
    newCount: 'new',
    sentPreview: 'Request sent',
    seen: 'Seen',
    sent: 'Sent',
    loading: 'Loading',
    loadEarlier: 'Load earlier messages',
    noMessages: 'No messages yet.',
    inputLabel: 'Message',
    inputPlaceholder: 'Type a message…',
    send: 'Send message',
    chatLabel: (name) => `Conversation with ${name}`,
    messagesLabel: 'Messages',
    notFoundTitle: 'Conversation not found',
    notFoundText: "This conversation doesn't exist or isn't available.",
    // Безопасность и приватность (формулировку подтверждает заказчик)
    safety:
      "Don't share your phone number, address or other personal contacts with people you don't know. Report anything that makes you uncomfortable.",
    notEncrypted:
      'Messages are not end-to-end encrypted and may be reviewed by NetworkIt administrators.',
    requestBar: {
      title: (name) => `${name} wants to chat`,
      text: 'Accept to start chatting, or decline to ignore this request.',
      accept: 'Accept',
      decline: 'Decline',
      accepted: 'Request accepted',
      declined: 'Request declined',
      sentTitle: 'Request sent',
      sentText: 'You can write more once the person accepts your request.',
      closedText: 'This conversation is closed.',
    },
    request: {
      title: 'Send a message request',
      intro: (name) =>
        `Say hello to ${name}. They can accept or decline. You can keep writing once they accept.`,
      label: 'Your message',
      placeholder: 'Write your first message…',
      counter: (length, max) => `${length}/${max}`,
      send: 'Send request',
      cancel: 'Cancel',
      sentToast: 'Message request sent',
      open: 'Open the conversation',
      message: 'Message',
      messageLabel: (name) => `Send a message request to ${name}`,
    },
    errors: {
      empty: 'Write a message first',
      tooLong: (max) => `Use at most ${max} characters`,
      notAvailable: "This person isn't available",
      generic: "Couldn't send the message. Please try again",
      loadFailed: "Couldn't load the conversation",
    },
  },

  // Состояние входа и общие тексты сети
  auth: {
    throttled: (seconds) => {
      const wait =
        seconds < 90
          ? `${seconds} seconds`
          : seconds < 5400
            ? `${Math.ceil(seconds / 60)} minutes`
            : `${Math.ceil(seconds / 3600)} hours`;
      return `Too many attempts. Try again in ${wait}.`;
    },
    unavailableTitle: "Can't reach the server",
    tryAgain: 'Try again',
  },

  // Тексты ошибок по коду, который вернул сервер. Если кода здесь нет — показываем message сервера.
  apiErrors: {
    // Ошибки полей
    required: 'This field is required',
    too_long: 'This is too long',
    too_short: 'This is too short',
    invalid: 'Please check this value',
    invalid_choice: 'Please choose a value from the list',
    invalid_characters: 'Some characters are not allowed here',
    invalid_format: 'Use 3–30 characters: lowercase letters, digits and _, starting with a letter',
    reserved: 'This username is not available',
    taken: 'This username is already taken',
    too_young: (limits) => `You must be at least ${limits.min_age} years old to join`,
    too_old: 'Please check the year of birth',
    future: 'Date of birth cannot be in the future',
    too_many: 'You selected too many items',
    duplicate: 'Duplicate values are not allowed',
    conversation_exists: 'You already have a conversation with this person',
    request_pending: 'Your message request is waiting for a reply',
    incoming_request_exists:
      'This person has already sent you a request. Accept it to start chatting',
    invalid_state: 'This request has already been handled',
    pending_requests_limit_reached:
      'You have too many requests waiting for a reply. Try again after some of them are answered',
    accept_required: 'Accept the message request first',
    conversation_closed: "You can't send messages to this person",
    cannot_target_self: "You can't do this with your own profile",
    saved_limit_reached: 'You have reached the limit of saved profiles',
    not_allowed_for_minors: 'Contact links are available from age 18',
    too_common: 'This password is too common',
    entirely_numeric: "Password can't be only digits",
    too_similar: 'This password is too similar to your email or name',
    too_weak: 'This password is too weak. Make it at least Medium (see the hint below)',
    same_as_old: 'The new password must be different from the current one',
    incorrect: 'Incorrect password',
    read_only_field: 'This field cannot be changed',
    // Общие ошибки запроса
    invalid_credentials: 'Incorrect email or password',
    invalid_token: 'This link is invalid or has expired',
    email_not_verified:
      'Please confirm your email address first. We sent you a link when you signed up.',
    account_banned: 'This account has been suspended. Please contact support.',
    already_authenticated: "You're already signed in",
    permission_denied: "This account can't be used on the website",
    not_authenticated: 'Please log in to continue',
    csrf_failed: 'Your session expired. Please reload the page and try again',
    not_found: 'Not found',
    server_error: 'Something went wrong on our side. Try again later',
    network_error: "Can't reach the server. Check your connection and try again",
    unknown: 'Something went wrong. Please try again',
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
    passwordWeak: 'This password is too weak. Make it at least Medium (see the hint below)',
    passwordLong: 'Password is too long',
    dateRequired: 'Please enter your date of birth (day, month, year)',
    dateInvalid: 'This date does not exist',
    dateFuture: 'Date of birth cannot be in the future',
    dateTooOld: 'Please check the year of birth',
    tooYoung: (limits) => `You must be at least ${limits.min_age} years old to join`,
    tooLong: 'This is too long',
    tooManyInterests: (limits) => `Choose up to ${limits.interests_max} interests`,
    tooManyLanguages: (limits) => `Choose up to ${limits.languages_max} languages`,
    tooManyGoals: (limits) => `Choose up to ${limits.goals_max} goals`,
    telegramInvalid: 'Telegram: 5–32 letters, digits or _',
    instagramInvalid: 'Instagram: up to 30 letters, digits, dots or _',
    whatsappInvalid: 'WhatsApp: international format, e.g. +998901234567',
    linkedinInvalid: 'LinkedIn: use a link like linkedin.com/in/your-name',
    termsRequired: 'You need to accept the Terms and Privacy Policy to continue',
  },
};
