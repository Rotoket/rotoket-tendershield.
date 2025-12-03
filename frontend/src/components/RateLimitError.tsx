import React from 'react';
import { AlertCircle, Crown, ArrowRight } from 'lucide-react';
import { APIError } from '../utils/apiErrorHandler';

interface RateLimitErrorProps {
  error: APIError;
  onUpgrade?: () => void;
}

const RateLimitError: React.FC<RateLimitErrorProps> = ({ error, onUpgrade }) => {
  return (
    <div className="bg-[#1a1f2e] border border-red-500/50 rounded-xl p-6 mb-6">
      <div className="flex items-start gap-4">
        <div className="flex-shrink-0">
          <div className="w-12 h-12 bg-red-500/10 rounded-xl flex items-center justify-center">
            <AlertCircle className="text-red-500" size={24} />
          </div>
        </div>
        <div className="flex-1">
          <h3 className="text-lg font-bold text-white mb-2">Превышен лимит использования</h3>
          <p className="text-[#a8b5cc] mb-4">{error.message}</p>
          {onUpgrade && (
            <button
              onClick={onUpgrade}
              className="inline-flex items-center gap-2 bg-gradient-to-r from-[#00d4ff] to-[#0099cc] text-[#0f1419] font-semibold px-6 py-3 rounded-xl hover:shadow-[0_0_20px_rgba(0,212,255,0.4)] transition-all"
            >
              <Crown size={20} />
              Обновить тариф
              <ArrowRight size={20} />
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default RateLimitError;


