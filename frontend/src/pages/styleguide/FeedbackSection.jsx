import { useState } from 'react';
import { Bookmark } from 'lucide-react';
import Alert from '../../components/ui/Alert.jsx';
import Button from '../../components/ui/Button.jsx';
import EmptyState from '../../components/ui/EmptyState.jsx';
import Field from '../../components/ui/Field.jsx';
import Modal from '../../components/ui/Modal.jsx';
import Spinner from '../../components/ui/Spinner.jsx';
import useToast from '../../components/ui/useToast.js';
import Section from './Section.jsx';
import layout from './Section.module.css';

// Тосты, модалка, спиннеры и пустое состояние
export default function FeedbackSection() {
  const showToast = useToast();
  const [modalOpen, setModalOpen] = useState(false);

  return (
    <Section title="Toast, Modal, Spinner, EmptyState">
      <p className={layout.caption}>Alert</p>
      <div className={layout.col}>
        <Alert>Incorrect email or password</Alert>
        <Alert tone="success">Password updated</Alert>
      </div>

      <p className={layout.caption}>Toast</p>
      <div className={layout.row}>
        <Button variant="ghost" size="sm" onClick={() => showToast('Welcome back!')}>
          Info
        </Button>
        <Button variant="ghost" size="sm" onClick={() => showToast('Profile saved', 'success')}>
          Success
        </Button>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => showToast('Could not save profile', 'error')}
        >
          Error
        </Button>
      </div>

      <p className={layout.caption}>Modal</p>
      <div className={layout.row}>
        <Button size="sm" onClick={() => setModalOpen(true)}>
          Open modal
        </Button>
      </div>
      <Modal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        title="Reset password"
        description="Enter your email and we'll send a reset link."
        actions={
          <>
            <Button variant="ghost" size="sm" onClick={() => setModalOpen(false)}>
              Cancel
            </Button>
            <Button size="sm" onClick={() => setModalOpen(false)}>
              Send link
            </Button>
          </>
        }
      >
        <Field label="Email" type="email" placeholder="you@email.com" />
      </Modal>

      <p className={layout.caption}>Spinner</p>
      <div className={layout.row}>
        <Spinner size="sm" tone="primary" label="Loading" />
        <Spinner size="md" tone="primary" label="Loading" />
        <Spinner size="lg" tone="primary" label="Loading" />
      </div>

      <p className={layout.caption}>EmptyState</p>
      <EmptyState
        icon={<Bookmark size={36} />}
        title="No saved profiles yet"
        description="Click the bookmark icon on any profile to save it here."
        action={<Button size="sm">Find people</Button>}
      />
    </Section>
  );
}
