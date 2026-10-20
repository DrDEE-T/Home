import React from 'react';

// Brand mark: one starting point opening into several paths. The visual form of "more options."
const Mark = ({ size = 28, title }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 32 32"
    fill="none"
    role={title ? 'img' : undefined}
    aria-hidden={title ? undefined : true}
  >
    {title && <title>{title}</title>}
    <path
      d="M7 16 C15 16 17 7 26 7 M7 16 H26 M7 16 C15 16 17 25 26 25"
      stroke="currentColor"
      strokeWidth="2.2"
      strokeLinecap="round"
    />
    <circle cx="7" cy="16" r="3.4" fill="currentColor" />
    <circle cx="26" cy="7" r="2" fill="currentColor" />
    <circle cx="26" cy="16" r="2" fill="currentColor" />
    <circle cx="26" cy="25" r="2" fill="currentColor" />
  </svg>
);

export default Mark;
