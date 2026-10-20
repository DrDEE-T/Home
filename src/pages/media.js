import React from 'react';

import Layout from '../components/Layout';
import Seo from '../components/Seo';
import { person, bio, media } from '../data/site';

const MediaPage = () => (
  <Layout>
    <section className="hero">
      <div className="wrap">
        <p className="eyebrow">Media</p>
        <h1 className="measure">Appearances and media kit.</h1>
        <p className="lede">
          For producers, editors, and event organizers. Bios and details below
          are approved for use.
        </p>
      </div>
    </section>

    <section className="section section--sand">
      <div className="wrap">
        <p className="eyebrow">Appearances and past work</p>
        <ul className="list">
          {media.map((m) => (
            <li key={m.outlet}>
              <p className="meta">{m.outlet}</p>
              <h3>{m.url ? <a href={m.url}>{m.title}</a> : m.title}</h3>
            </li>
          ))}
        </ul>
      </div>
    </section>

    <section className="section">
      <div className="wrap">
        <p className="eyebrow">Bios</p>
        <div className="grid grid--2" style={{ marginTop: 16 }}>
          <div className="card">
            <h3>Short</h3>
            <p>{bio.short}</p>
          </div>
          <div className="card">
            <h3>Medium</h3>
            <p>{bio.medium}</p>
          </div>
        </div>
        <div className="card" style={{ marginTop: 24 }}>
          <h3>Full</h3>
          {bio.full.map((para) => (
            <p key={para.slice(0, 32)}>{para}</p>
          ))}
        </div>
        {person.portrait && (
          <p style={{ marginTop: 24 }}>
            <a className="btn btn--ghost" href={person.portrait} download>
              Download headshot
            </a>
          </p>
        )}
      </div>
    </section>
  </Layout>
);

export default MediaPage;

export const Head = () => (
  <Seo
    title="Media"
    description={`Media kit, bios, and appearances for ${person.name}.`}
    path="/media/"
  />
);
