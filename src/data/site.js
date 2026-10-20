// All site copy and links live here so the brand can be tuned without touching layout code.
// Anything marked TODO needs a real value from Denise before launch.

export const person = {
  name: 'Dr. Denise Turley',
  shortName: 'Denise Turley',
  roles: ['Executive', 'Educator', 'Author'],
  // TODO: add a professional headshot to /static (e.g. /static/denise-turley.jpg) and set the path here.
  portrait: '',
};

export const brand = {
  coreBelief: "Technology should expand what's possible for people.",
  valueProp:
    'I bring ideas and technology to life in ways that help people create opportunities, make choices, and pursue the lives they envision.',
  // Signature name is still an open decision. See brand/BRAND_GUIDE.md. Change it here and it updates everywhere.
  signature: 'More Possible',
  signatureLine:
    'A recurring series on using technology to create more choice in work, business, and life.',
  keynoteTitle: 'The Power of Options',
  keynoteSubtitle:
    'Building choice for people and organizations in the age of AI',
};

export const links = {
  linkedin: 'https://www.linkedin.com/in/TODO', // TODO: Denise's LinkedIn profile URL
  linkedinNewsletter: '', // TODO: add once the newsletter is live
  youtube: '', // TODO: optional, leave empty to hide
  email: '', // TODO: public contact address, leave empty to rely on the form
};

export const nav = [
  { label: 'About', to: '/about/' },
  { label: 'Ideas', to: '/ideas/' },
  { label: 'Speaking', to: '/speaking/' },
  { label: 'Media', to: '/media/' },
  { label: 'Connect', to: '/connect/' },
];

// Finalized biography, October 2026. Keep wording in sync with brand/BRAND_GUIDE.md.
export const bio = {
  full: [
    "Dr. Denise Turley believes technology should expand what's possible for people. For more than 20 years, she has turned curiosity into action, bringing new ideas and technologies to life in ways that create meaningful opportunities. Her work is driven by a belief that innovation should empower people to make choices, pursue their ambitions, and shape the futures they envision for themselves.",
    'A senior executive, educator, and author, Denise has spent her career anticipating change and translating possibilities into practical impact. Today, she brings that same perspective to artificial intelligence, helping people and organizations harness its potential to rethink how they work, live, and pursue success on their own terms.',
    'Her experience spans executive leadership, entrepreneurship, and higher education. She has developed educational content for CNBC and LinkedIn Learning, appeared on PBS, and teaches graduate-level business and technology courses.',
    "At the heart of her work is a simple conviction: Progress is meaningful when it improves people's lives and gives them more options for their future.",
  ],
  medium:
    "Dr. Denise Turley is a senior executive, educator, and author who believes technology should expand what's possible for people. For more than 20 years she has led business and technology transformation, turning new ideas into practical results. Today she applies that experience to AI, helping people and organizations use it to create opportunities and more choice in how they work and live. She has developed educational content for CNBC and LinkedIn Learning, appeared on PBS, and teaches graduate-level business and technology courses.",
  short:
    'Dr. Denise Turley is an executive, educator, and author who helps people and organizations use technology, today AI, to create more options in work and life.',
};

export const pillars = [
  {
    id: 'possibility',
    title: 'Possibility in Practice',
    summary:
      'Real demonstrations of what technology makes possible. Experiments, creative projects, and practical builds you can try yourself.',
  },
  {
    id: 'opportunity',
    title: 'Opportunity and Choice',
    summary:
      'Career resilience, new skills, entrepreneurship, financial decisions, and personal agency. How people create more options for themselves.',
  },
  {
    id: 'leadership',
    title: 'Leadership and Human Impact',
    summary:
      'What it takes to lead change well. Hard decisions, redesigned organizations, and what technology means for the people living with it.',
  },
];

export const roles = [
  {
    title: 'Executive',
    text: 'More than two decades leading business and technology transformation, from idea to operating reality.',
  },
  {
    title: 'Educator',
    text: 'Graduate-level business and technology courses, plus educational content for national audiences.',
  },
  {
    title: 'Entrepreneur',
    text: 'Building things from scratch and living with the decisions that come with it.',
  },
  {
    title: 'Creative experimenter',
    text: 'Trying new tools on creative and practical projects to see what they can really do.',
  },
  {
    title: 'Wife, mother, grandmother',
    text: 'Family shapes the choices I make and the future I care about building.',
  },
];

export const audiences = [
  {
    title: 'Professionals navigating growth and change',
    text: 'Staying adaptable, building resilience, and creating options when the ground keeps shifting.',
  },
  {
    title: 'Graduates and early-career professionals',
    text: 'Using technology to become more capable, more confident, and more employable.',
  },
  {
    title: 'Business leaders',
    text: 'Adopting technology responsibly so it creates value for the organization and its people.',
  },
  {
    title: 'Anyone pursuing a fuller life',
    text: 'Practical ways technology can give back time, support creativity, and help you make better decisions.',
  },
];

// Past work and appearances. CNBC and LinkedIn Learning are described as past engagements.
export const credentials = [
  { label: 'CNBC', detail: 'Developed educational content' },
  { label: 'LinkedIn Learning', detail: 'Developed educational content' },
  { label: 'PBS', detail: 'Featured appearance' },
  { label: 'Graduate faculty', detail: 'Business and technology courses' },
];

// Writing and video. Add entries as they publish: { title, pillar, date, url, type: 'Article' | 'Video' | 'Post' }
export const writing = [];

// Media appearances. Add url/date once confirmed.
export const media = [
  {
    outlet: 'PBS',
    title: 'Television appearance',
    note: 'TODO: episode or segment name, date, and link',
    url: '',
  },
  {
    outlet: 'CNBC',
    title: 'Educational content (past engagement)',
    note: 'TODO: series or topic name and a link if available',
    url: '',
  },
  {
    outlet: 'LinkedIn Learning',
    title: 'Educational content (past engagement)',
    note: 'TODO: course title(s) and link',
    url: '',
  },
];

export const talks = [
  {
    title: brand.keynoteTitle,
    kind: 'Signature keynote',
    audience: 'Conferences, leadership teams, professional associations',
    text: 'People are anxious about AI and their work. Fair enough. This talk moves the room from worry to agency. It shows what the technology can actually do, how individuals build more options for themselves, and what leaders owe the people going through the change.',
    points: [
      'See what is possible: live demonstrations on real tasks',
      'Build your options: skills, resilience, and personal agency',
      'Lead so others have options: adoption that works for people',
    ],
  },
  {
    title: 'Making technology work for organizations and their people',
    kind: 'Leadership session',
    audience: 'Executives and boards',
    text: 'Responsible adoption, organizational change, and business value, from someone who has led transformation through several generations of technology.',
  },
  {
    title: 'Career resilience when the skills keep changing',
    kind: 'Talk or fireside chat',
    audience: 'Professionals, graduates, alumni groups',
    text: 'How to stay capable and employable as AI changes the work, and how to turn uncertainty into choices you control.',
  },
];
