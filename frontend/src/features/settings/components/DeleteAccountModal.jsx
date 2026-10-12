import { useState } from 'react';
import Button from '../../../components/ui/Button.jsx';
import Field from '../../../components/ui/Field.jsx';
import Modal from '../../../components/ui/Modal.jsx';
import { texts } from '../../../texts/en.js';

const t = texts.settings.danger;

// Подтверждение удаления: нужно набрать DELETE. Само удаление подключим позже
// (DELETE /api/me/ с паролем), поэтому после подтверждения вызывается onConfirm → «Coming soon».
export default function DeleteAccountModal({ open, onClose, onConfirm }) {
  const [typed, setTyped] = useState('');

  function close() {
    setTyped('');
    onClose();
  }

  return (
    <Modal
      open={open}
      onClose={close}
      title={t.modalTitle}
      description={t.modalText}
      actions={
        <>
          <Button variant="ghost" size="sm" onClick={close}>
            {t.cancel}
          </Button>
          <Button
            variant="danger"
            size="sm"
            disabled={typed !== t.confirmWord}
            onClick={() => {
              onConfirm();
              close();
            }}
          >
            {t.confirm}
          </Button>
        </>
      }
    >
      <Field
        label={t.confirmLabel}
        value={typed}
        autoComplete="off"
        onChange={(event) => setTyped(event.target.value)}
      />
    </Modal>
  );
}
