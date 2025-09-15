import React from 'react';

interface HallucinationMarkerProps {
  type: 'MissingFact' | 'WrongAssumption' | 'Speculation';
  snippet: string;
  confidence?: number;
  onHover?: () => void;
  onLeave?: () => void;
}

const HallucinationMarker: React.FC<HallucinationMarkerProps> = ({ 
  type, 
  snippet, 
  confidence = 0,
  onHover,
  onLeave
}) => {
  // Map types to display information
  const typeInfo = {
    MissingFact: {
      label: 'Missing Fact',
      color: 'text-orange-600',
      bgColor: 'bg-orange-100',
      icon: '❓'
    },
    WrongAssumption: {
      label: 'Wrong Assumption',
      color: 'text-red-600',
      bgColor: 'bg-red-100',
      icon: '⚠️'
    },
    Speculation: {
      label: 'Speculation',
      color: 'text-yellow-600',
      bgColor: 'bg-yellow-100',
      icon: '💭'
    }
  };
  
  const info = typeInfo[type] || typeInfo.WrongAssumption;
  
  return (
    <span 
      className={`inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium ${info.bgColor} ${info.color} cursor-help`}
      onMouseEnter={onHover}
      onMouseLeave={onLeave}
      title={`${info.label} (${Math.round(confidence * 100)}% confidence): ${snippet}`}
    >
      <span className="mr-1">{info.icon}</span>
      {info.label}
    </span>
  );
};

export default HallucinationMarker;
