import React, { useEffect, useState } from 'react';

import Layout from '../components/Layout';
import Seo from '../components/Seo';
import ContactForm from '../components/ContactForm';
import { links } from '../data/site';

const ConnectPage = () => {
  const [sent, setSent] = useState(false);

  useEffect(() => {
    setSent(new URLSearchParams(window.location.search).has('sent'));
  }, []);

  return (
    <Layout>
      <section className="hero">
        <div className="wrap split">
          <div>
            <p className="eyebrow">Connect</p>
            <h1>Follow the work.</h1>
            <p className="lede">
              LinkedIn is where I publish most often. New writing, video, and
              experiments show up there first.
            </p>
            <div className="actions">
              <a className="btn" href={links.linkedin}>
                Follow on LinkedIn
              </a>
              {links.linkedinNewsletter && (
                <a className="btn btn--ghost" href={links.linkedinNewsletter}>
                  Subscribe to the newsletter
                </a>
              )}
              {links.youtube && (
                <a className="btn btn--ghost" href={links.youtube}>
                  YouTube
                </a>
              )}
            </div>
          </div>
          <div>
            {sent ? (
              <div className="card">
                <h3>Thank you.</h3>
                <p>Your message is on its way. I'll be in touch.</p>
              </div>
            ) : (
              <>
                <h2>Send a note</h2>
                <ContactForm name="contact" topic="General" />
              </>
            )}
          </div>
        </div>
      </section>
    </Layout>
  );
};

export default ConnectPage;

export const Head = () => (
  <Seo
    title="Connect"
    description="Follow the work or send a note."
    path="/connect/"
  />
);
