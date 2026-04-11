interface Props {
  open: boolean;
  onClose: () => void;
}

export const MobileDrawer = ({ open, onClose }: Props) => {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 md:hidden" onClick={onClose}>
      <div className="absolute inset-0 bg-slate-900/40 backdrop-blur-sm" />
      <div className="absolute inset-y-0 left-0 w-64 bg-white shadow-xl" />
    </div>
  );
};
