import React from 'react';
import { Link } from 'gatsby';

import Layout from '../components/Layout';
import Portrait from '../components/Portrait';
import Seo from '../components/Seo';
import {
  person,
  brand,
  links,
  pillars,
  audiences,
  credentials,
  writing,
} from '../data/site';

const IndexPage = () => (
  <Layout>
    <section className="hero">
      <div className="wrap hero-grid">
        <div>
          <p className="eyebrow">{person.roles.join(' · ')}</p>
          <h1>
            Technology should expand what's <em>possible</em> for people.
          </h1>
          <p className="lede">{brand.valueProp}</p>
          <div className="actions">
            <Link className="btn" to="/ideas/">
              Explore the ideas
            </Link>
            <a className="btn btn--ghost" href={links.linkedin}>
              Follow on LinkedIn
            </a>
          </div>
        </div>
        <Portrait />
      </div>
    </section>

    <section className="section--tight">
      <div className="wrap">
        <p className="eyebrow">Past work and appearances</p>
        <div className="creds">
          {credentials.map((c) => (
            <div key={c.label}>
              <strong>{c.label}</strong>
              <span>{c.detail}</span>
            </div>
          ))}
        </div>
      </div>
    </section>

    <section className="section">
      <div className="wrap split">
        <p className="pull">What if we could do this better?</p>
        <div className="measure">
          <p className="eyebrow">What I believe</p>
          <p>
            That question has followed me through more than 20 years of leading
            business and technology change. The tools have changed many times.
            What I care about hasn't: people, their lives, and the outcomes that
            matter to them.
          </p>
          <p>
            Good technology gives people more room to choose. More ways to build
            skills, earn security, start something new, and spend time on what
            matters. That's the test I apply to every new tool, including AI.
          </p>
          <Link to="/about/">More about me</Link>
        </div>
      </div>
    </section>

    <section className="section section--sand">
      <div className="wrap">
        <p className="eyebrow">What I write and speak about</p>
        <h2>Three threads, one belief</h2>
        <div className="grid grid--3" style={{ marginTop: 32 }}>
          {pillars.map((p, i) => (
            <Link
              key={p.id}
              to={`/ideas/#${p.id}`}
              className="card"
              style={{ textDecoration: 'none' }}
            >
              <span className="num">0{i + 1}</span>
              <h3>{p.title}</h3>
              <p>{p.summary}</p>
            </Link>
          ))}
        </div>
      </div>
    </section>

    <section className="section section--ink">
      <div className="wrap split">
        <div>
          <p className="eyebrow">Signature series</p>
          <h2>{brand.signature}</h2>
        </div>
        <div className="measure">
          <p className="lede">{brand.signatureLine}</p>
          <p>
            Demonstrations, honest experiments, and conversations about how
            people turn new technology into real choices. Some of it will be
            about work. Some of it will be about the rest of life.
          </p>
          <div className="actions">
            <a
              className="btn"
              href={links.linkedinNewsletter || links.linkedin}
            >
              Follow the series
            </a>
          </div>
        </div>
      </div>
    </section>

    <section className="section">
      <div className="wrap">
        <p className="eyebrow">Who this is for</p>
        <h2>People building more options for themselves</h2>
        <div className="grid grid--4" style={{ marginTop: 32 }}>
          {audiences.map((a) => (
            <div key={a.title}>
              <h3>{a.title}</h3>
              <p>{a.text}</p>
            </div>
          ))}
        </div>
      </div>
    </section>

    <section className="section section--sand">
      <div className="wrap">
        <p className="eyebrow">Latest</p>
        <h2>Writing and video</h2>
        {writing.length ? (
          <ul className="list" style={{ marginTop: 24 }}>
            {writing.slice(0, 4).map((w) => (
              <li key={w.url}>
                <p className="meta">
                  {w.type} · {w.date}
                </p>
                <a href={w.url}>
                  <h3>{w.title}</h3>
                </a>
              </li>
            ))}
          </ul>
        ) : (
          <div className="empty" style={{ marginTop: 24 }}>
            New writing and video will appear here. For now, the best place to
            follow along is <a href={links.linkedin}>LinkedIn</a>.
          </div>
        )}
      </div>
    </section>

    <section className="section">
      <div className="wrap split">
        <div>
          <p className="eyebrow">Speaking</p>
          <h2>{brand.keynoteTitle}</h2>
        </div>
        <div className="measure">
          <p className="lede">{brand.keynoteSubtitle}.</p>
          <p>
            Keynotes, fireside chats, and leadership sessions for audiences who
            want to understand what technology makes possible and how to make it
            work for people.
          </p>
          <div className="actions">
            <Link className="btn" to="/speaking/">
              Invite me to speak
            </Link>
          </div>
        </div>
      </div>
    </section>
  </Layout>
);

export default IndexPage;

export const Head = () => <Seo path="/" />;
