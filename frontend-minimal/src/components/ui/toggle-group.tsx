import React from 'react';
import { motion } from 'framer-motion';

interface ToggleGroupProps {
  type?: 'single' | 'multiple';
  value?: string | string[];
  onValueChange?: (value: string | string[]) => void;
  className?: string;
  children: React.ReactNode;
}

export const ToggleGroup = ({
  type = 'single',
  value,
  onValueChange,
  className = '',
  children,
}: ToggleGroupProps) => {
  // Use type prop to determine behavior for single vs multiple selection
  const isMultiple = type === 'multiple';
  
  const handleItemClick = (itemValue: string) => {
    if (isMultiple) {
      // Handle multiple selection
      const currentValues = Array.isArray(value) ? value : [];
      const newValues = currentValues.includes(itemValue)
        ? currentValues.filter(v => v !== itemValue)
        : [...currentValues, itemValue];
      onValueChange?.(newValues);
    } else {
      // Handle single selection
      onValueChange?.(itemValue);
    }
  };
  
  return (
    <div className={`inline-flex items-center rounded-md bg-gray-100 p-1 ${className}`}>
      {React.Children.map(children, (child) => {
        if (React.isValidElement(child)) {
          const childValue = child.props.value;
          const isSelected = isMultiple 
            ? Array.isArray(value) && value.includes(childValue)
            : value === childValue;
            
          return React.cloneElement(child, {
            ...child.props,
            selected: isSelected,
            onClick: () => handleItemClick(childValue),
          });
        }
        return child;
      })}
    </div>
  );
};

interface ToggleGroupItemProps {
  value: string;
  selected?: boolean;
  onClick?: () => void;
  className?: string;
  children: React.ReactNode;
}

export const ToggleGroupItem = ({
  value,
  selected = false,
  onClick,
  className = '',
  children,
}: ToggleGroupItemProps) => {
  // Use value prop for identification
  return (
    <motion.button
      type="button"
      className={`inline-flex items-center justify-center rounded-sm px-3 py-1 text-xs font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 ${selected ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-700 hover:bg-gray-200'} ${className}`}
      onClick={onClick}
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
      transition={{ type: "spring", stiffness: 400, damping: 17 }}
      data-value={value}
    >
      {children}
    </motion.button>
  );
};
