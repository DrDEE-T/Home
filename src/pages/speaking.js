import React from 'react';

import Layout from '../components/Layout';
import Seo from '../components/Seo';
import ContactForm from '../components/ContactForm';
import { brand, talks } from '../data/site';

const SpeakingPage = () => {
  const [keynote, ...others] = talks;
  return (
    <Layout>
      <section className="hero">
        <div className="wrap">
          <p className="eyebrow">Speaking</p>
          <h1 className="measure">
            Talks that leave people with more options.
          </h1>
          <p className="lede">
            I speak to conferences, leadership teams, universities, and
            professional groups about what technology makes possible and how to
            make it work for people.
          </p>
        </div>
      </section>

      <section className="section section--ink">
        <div className="wrap split">
          <div>
            <p className="eyebrow">{keynote.kind}</p>
            <h2>{keynote.title}</h2>
            <p className="lede">{brand.keynoteSubtitle}</p>
          </div>
          <div className="measure">
            <p>{keynote.text}</p>
            <ul className="ticks">
              {keynote.points.map((pt) => (
                <li key={pt}>{pt}</li>
              ))}
            </ul>
            <p className="meta" style={{ color: '#c9ced8', marginTop: 20 }}>
              Best for: {keynote.audience}
            </p>
          </div>
        </div>
      </section>

      <section className="section">
        <div className="wrap">
          <p className="eyebrow">Other sessions</p>
          <div className="grid grid--2" style={{ marginTop: 16 }}>
            {others.map((t) => (
              <div className="card" key={t.title}>
                <p className="meta">{t.kind}</p>
                <h3>{t.title}</h3>
                <p>{t.text}</p>
                <p className="meta">Best for: {t.audience}</p>
              </div>
            ))}
          </div>
          <p className="meta" style={{ marginTop: 24 }}>
            Formats: keynote, fireside chat, panel, guest lecture. In person or
            virtual.
          </p>
        </div>
      </section>

      <section className="section section--sand" id="invite">
        <div className="wrap split">
          <div>
            <p className="eyebrow">Invite me</p>
            <h2>Tell me about your event</h2>
            <p>
              Share the audience, date, and what you hope people walk away with.
              I read every request.
            </p>
          </div>
          <ContactForm name="speaking" topic="Speaking request" />
        </div>
      </section>
    </Layout>
  );
};

export default SpeakingPage;

export const Head = () => (
  <Seo
    title="Speaking"
    description={`Keynotes and leadership sessions, including ${brand.keynoteTitle}.`}
    path="/speaking/"
  />
);
