import { useState } from 'react';
import { BookOpen, Rocket } from 'lucide-react';
import Checkbox from '../../components/ui/Checkbox.jsx';
import ChipSelect from '../../components/ui/ChipSelect.jsx';
import FieldGroup from '../../components/ui/FieldGroup.jsx';
import Field from '../../components/ui/Field.jsx';
import Toggle from '../../components/ui/Toggle.jsx';
import Section from './Section.jsx';
import layout from './Section.module.css';

const INTERESTS = ['Business', 'Design', 'Finance', 'Law', 'Music', 'Physics'].map((label) => ({
  code: label,
  label,
}));
const GOALS = [
  { code: 'study', label: 'Study partners', icon: BookOpen },
  { code: 'startup', label: 'Startup co-founders', icon: Rocket },
  { code: 'friends', label: 'Looking for friends' },
];
const STATUS = [
  { code: 'student', label: 'Student' },
  { code: 'professional', label: 'Professional' },
];

// Поля формы, переключатель и чипы
export default function FormsSection() {
  const [interests, setInterests] = useState(['Design']);
  const [status, setStatus] = useState(['student']);
  const [showCity, setShowCity] = useState(true);
  const [showContacts, setShowContacts] = useState(false);
  const [goals, setGoals] = useState(['study']);
  const [agreed, setAgreed] = useState(false);

  return (
    <Section title="Field, Toggle, ChipSelect">
      <div className={layout.col}>
        <Field label="First name" required placeholder="Jane" />
        <Field
          label="Username"
          hint="3–30 characters, letters, digits and _"
          placeholder="janedoe"
        />
        <Field
          label="Email"
          type="email"
          defaultValue="not-an-email"
          error="Please enter a valid email."
        />
        <Field label="Country" as="select" optionalText="(optional)" defaultValue="">
          <option value="">Select country</option>
          <option value="UZ">Uzbekistan</option>
          <option value="KZ">Kazakhstan</option>
        </Field>
        <Field label="Bio" as="textarea" hint="Up to 300 characters" rows={4} maxLength={300} />
        <Field label="Disabled field" disabled defaultValue="Can't edit" />
      </div>

      <p className={layout.caption}>Toggle</p>
      <div className={layout.row}>
        <Toggle checked={showCity} onChange={setShowCity} label="Show city" />
        <span>Show city: {showCity ? 'on' : 'off'}</span>
        <Toggle checked={showContacts} onChange={setShowContacts} label="Show contacts" />
        <span>Show contacts: {showContacts ? 'on' : 'off'}</span>
        <Toggle checked disabled onChange={() => {}} label="Disabled toggle" />
      </div>

      <p className={layout.caption}>ChipSelect — chips (multiple)</p>
      <ChipSelect label="Interests" options={INTERESTS} value={interests} onChange={setInterests} />
      <p className={layout.caption}>ChipSelect — pills (single)</p>
      <ChipSelect
        label="Status"
        variant="pill"
        multiple={false}
        options={STATUS}
        value={status}
        onChange={setStatus}
      />
      <p className={layout.caption}>ChipSelect — list with icons, max 2</p>
      <FieldGroup legend="Goals" hint={`${goals.length}/2`}>
        <ChipSelect variant="list" options={GOALS} value={goals} max={2} onChange={setGoals} />
      </FieldGroup>

      <p className={layout.caption}>Checkbox</p>
      <Checkbox
        checked={agreed}
        onChange={setAgreed}
        error={agreed ? undefined : 'You need to accept to continue'}
      >
        I agree to the Terms and Privacy Policy
      </Checkbox>
    </Section>
  );
}
