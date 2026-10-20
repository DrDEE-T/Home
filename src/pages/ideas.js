import React from 'react';

import Layout from '../components/Layout';
import Seo from '../components/Seo';
import { brand, links, pillars, writing } from '../data/site';

const IdeasPage = () => (
  <Layout>
    <section className="hero">
      <div className="wrap">
        <p className="eyebrow">Ideas</p>
        <h1 className="measure">Writing, video, and experiments.</h1>
        <p className="lede">
          Everything here comes back to one belief:{' '}
          {brand.coreBelief.toLowerCase()} Pick a thread.
        </p>
      </div>
    </section>

    {pillars.map((p, i) => {
      const entries = writing.filter((w) => w.pillar === p.id);
      return (
        <section
          key={p.id}
          id={p.id}
          className={`section ${i % 2 === 0 ? 'section--sand' : ''}`}
        >
          <div className="wrap split">
            <div>
              <span
                className="num"
                style={{
                  fontFamily: 'var(--font-display)',
                  color: 'var(--clay)',
                }}
              >
                0{i + 1}
              </span>
              <h2>{p.title}</h2>
              <p>{p.summary}</p>
            </div>
            <div>
              {entries.length ? (
                <ul className="list">
                  {entries.map((w) => (
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
                <div className="empty">
                  First pieces in this thread are on the way. Follow on{' '}
                  <a href={links.linkedin}>LinkedIn</a> to catch them as they
                  publish.
                </div>
              )}
            </div>
          </div>
        </section>
      );
    })}
  </Layout>
);

export default IdeasPage;

export const Head = () => (
  <Seo
    title="Ideas"
    description="Writing, video, and experiments on technology, opportunity, choice, and leading change."
    path="/ideas/"
  />
);
