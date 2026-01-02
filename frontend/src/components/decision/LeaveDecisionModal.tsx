import React from 'react';

interface LeaveDecisionModalProps {
  open: boolean;
  onStay: () => void;
  onLeave: () => void;
}

export const LeaveDecisionModal: React.FC<LeaveDecisionModalProps> = ({ open, onStay, onLeave }) => {
  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
      <div className="bg-[#0f1419] border border-[#2a3441] rounded-2xl shadow-xl max-w-md w-full p-6">
        <h2 className="text-lg font-semibold text-white mb-3">
          You are leaving a decision contour
        </h2>
        <p className="text-sm text-slate-300 mb-4">
          A director decision has not been recorded. Leaving now will break the responsibility chain.
        </p>
        <div className="flex justify-end gap-3 mt-4">
          <button
            type="button"
            onClick={onStay}
            className="px-4 py-2 rounded-lg bg-[#111827] text-slate-200 border border-[#374151] text-sm"
          >
            Return to Decision
          </button>
          <button
            type="button"
            onClick={onLeave}
            className="px-4 py-2 rounded-lg bg-red-600 text-white text-sm font-semibold hover:bg-red-500"
          >
            Leave without recording
          </button>
        </div>
      </div>
    </div>
  );
};

export default LeaveDecisionModal;









































