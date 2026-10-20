import React from 'react';
import { Link } from 'gatsby';

import Mark from './Mark';
import { person, brand, links, nav } from '../data/site';

const Layout = ({ children }) => (
  <>
    <a className="skip" href="#main">
      Skip to content
    </a>
    <header className="site-header">
      <div className="wrap">
        <Link to="/" className="logo">
          <span style={{ color: 'var(--clay)' }}>
            <Mark />
          </span>
          <span>
            <small>Dr.</small> {person.shortName}
          </span>
        </Link>
        <nav className="nav" aria-label="Main">
          {nav.map((item) => (
            <Link key={item.to} to={item.to}>
              {item.label}
            </Link>
          ))}
        </nav>
      </div>
    </header>

    <main id="main">{children}</main>

    <footer className="site-footer">
      <div className="wrap">
        <div>
          <p className="belief">{brand.coreBelief}</p>
          <p>
            {person.name} &middot; {person.roles.join(', ')}
          </p>
        </div>
        <nav aria-label="Footer">
          {nav.map((item) => (
            <Link key={item.to} to={item.to}>
              {item.label}
            </Link>
          ))}
        </nav>
        <nav aria-label="Follow">
          <a href={links.linkedin}>LinkedIn</a>
          {links.linkedinNewsletter && (
            <a href={links.linkedinNewsletter}>Newsletter</a>
          )}
          {links.youtube && <a href={links.youtube}>YouTube</a>}
          {links.email && <a href={`mailto:${links.email}`}>Email</a>}
        </nav>
      </div>
      <div className="wrap" style={{ marginTop: 40 }}>
        <p className="meta" style={{ color: '#9aa1ae' }}>
          &copy; {new Date().getFullYear()} {person.name}
        </p>
      </div>
    </footer>
  </>
);

export default Layout;
