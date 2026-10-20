import React from 'react';

import { person, brand, bio } from '../data/site';

// Used from each page's Gatsby Head export.
const Seo = ({ title, description, path = '/' }) => {
  const fullTitle = title
    ? `${title} | ${person.name}`
    : `${person.name} | ${brand.coreBelief}`;
  const desc = description || bio.short;
  return (
    <>
      <html lang="en" />
      <title>{fullTitle}</title>
      <meta name="description" content={desc} />
      <meta property="og:title" content={fullTitle} />
      <meta property="og:description" content={desc} />
      <meta property="og:type" content="website" />
      <meta property="og:url" content={path} />
      <meta name="twitter:card" content="summary" />
      <meta name="theme-color" content="#1c2433" />
      <link rel="icon" href="/favicon.svg" type="image/svg+xml" />
      <link rel="preconnect" href="https://fonts.googleapis.com" />
      <link
        rel="preconnect"
        href="https://fonts.gstatic.com"
        crossOrigin="anonymous"
      />
      <link
        rel="stylesheet"
        href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,400..600;1,9..144,400..600&family=Inter:wght@400;600&display=swap"
      />
    </>
  );
};

export default Seo;
