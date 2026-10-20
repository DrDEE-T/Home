import React from 'react';
import { Link } from 'gatsby';

import Layout from '../components/Layout';
import Portrait from '../components/Portrait';
import Seo from '../components/Seo';
import { bio, roles } from '../data/site';

const AboutPage = () => (
  <Layout>
    <section className="hero">
      <div className="wrap hero-grid">
        <div>
          <p className="eyebrow">About</p>
          <h1>Curiosity, turned into something useful.</h1>
          <div className="measure">
            {bio.full.map((para) => (
              <p key={para.slice(0, 32)}>{para}</p>
            ))}
          </div>
        </div>
        <Portrait />
      </div>
    </section>

    <section className="section section--sand">
      <div className="wrap">
        <p className="eyebrow">Many roles, one thread</p>
        <h2>No single title</h2>
        <p className="lede">
          I've never wanted to be defined by one role. Technology is part of
          what makes it possible to pursue several ambitions at once, and that's
          a big part of what I want to show people.
        </p>
        <div className="grid grid--3" style={{ marginTop: 32 }}>
          {roles.map((r) => (
            <div className="card" key={r.title}>
              <h3>{r.title}</h3>
              <p>{r.text}</p>
            </div>
          ))}
        </div>
      </div>
    </section>

    <section className="section">
      <div className="wrap split">
        <p className="pull">
          Progress is meaningful when it improves people's lives and gives them
          more options for their future.
        </p>
        <div className="measure">
          <p>
            AI is the technology I'm working with today. It won't be the last.
            The commitment underneath stays the same: start with people and the
            outcomes they care about, then find the technology that helps.
          </p>
          <div className="actions">
            <Link className="btn" to="/ideas/">
              Read the ideas
            </Link>
            <Link className="btn btn--ghost" to="/media/">
              Media kit
            </Link>
          </div>
        </div>
      </div>
    </section>
  </Layout>
);

export default AboutPage;

export const Head = () => (
  <Seo title="About" description={bio.medium} path="/about/" />
);
