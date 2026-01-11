/**
 * Error message component
 */

interface ErrorMessageProps {
  message: string;
  onClose?: () => void;
}

const ErrorMessage = ({ message, onClose }: ErrorMessageProps) => {
  return (
    <div
      style={{
        padding: '1rem',
        margin: '1rem 0',
        backgroundColor: '#fee',
        border: '1px solid #fcc',
        borderRadius: '4px',
        color: '#c00',
      }}
    >
      <p style={{ margin: 0 }}>{message}</p>
      {onClose && (
        <button
          onClick={onClose}
          style={{
            marginTop: '0.5rem',
            padding: '0.25rem 0.5rem',
            cursor: 'pointer',
          }}
        >
          閉じる
        </button>
      )}
    </div>
  );
};

export default ErrorMessage;
