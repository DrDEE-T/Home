import React from 'react';

import Mark from './Mark';
import { person } from '../data/site';

const Portrait = () =>
  person.portrait ? (
    <div className="portrait">
      <img src={person.portrait} alt={`Portrait of ${person.name}`} />
    </div>
  ) : (
    <div className="portrait portrait--placeholder" aria-hidden="true">
      <Mark size={160} />
    </div>
  );

export default Portrait;
