import React from 'react';
import { Link } from 'gatsby';

import Layout from '../components/Layout';
import Seo from '../components/Seo';

const NotFoundPage = () => (
  <Layout>
    <section className="hero">
      <div className="wrap measure">
        <p className="eyebrow">404</p>
        <h1>This page isn't here.</h1>
        <p className="lede">Plenty of other paths are, though.</p>
        <div className="actions">
          <Link className="btn" to="/">
            Go home
          </Link>
        </div>
      </div>
    </section>
  </Layout>
);

export default NotFoundPage;

export const Head = () => <Seo title="Page not found" />;
