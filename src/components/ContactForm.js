import React from 'react';

// Netlify Forms: the static form is detected at build time, no backend needed.
const ContactForm = ({ name, topic }) => (
  <form
    className="form"
    name={name}
    method="POST"
    data-netlify="true"
    netlify-honeypot="company-website"
    action="/connect/?sent=1"
  >
    <input type="hidden" name="form-name" value={name} />
    <input type="hidden" name="topic" value={topic} />
    <p className="hidden">
      <label>
        Leave this empty <input name="company-website" />
      </label>
    </p>
    <label>
      Name
      <input name="name" autoComplete="name" required />
    </label>
    <label>
      Email
      <input name="email" type="email" autoComplete="email" required />
    </label>
    {name === 'speaking' && (
      <label>
        Event and date
        <input name="event" />
      </label>
    )}
    <label>
      Message
      <textarea name="message" required />
    </label>
    <div>
      <button className="btn" type="submit">
        Send
      </button>
    </div>
  </form>
);

export default ContactForm;
