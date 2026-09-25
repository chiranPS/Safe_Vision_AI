import React from 'react';
import { cn } from '../../utils/cn';

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: 'default' | 'primary' | 'success' | 'warning' | 'danger' | 'critical' | 'Low' | 'Medium' | 'High' | 'Critical' | string;
}

export const Badge: React.FC<BadgeProps> = ({ 
  className, 
  variant = 'default', 
  children, 
  ...props 
}) => {
  const baseStyles = "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border";
  
  const variants: Record<string, string> = {
    default: "bg-slate-100 text-slate-800 border-slate-200",
    primary: "bg-blue-100 text-blue-800 border-blue-200",
    success: "bg-green-100 text-green-800 border-green-200",
    warning: "bg-yellow-100 text-yellow-800 border-yellow-200",
    danger: "bg-orange-100 text-orange-800 border-orange-200",
    critical: "bg-red-100 text-red-800 border-red-200",
  };

  let mappedVariant = variant;
  if(variant?.toLowerCase() === 'low') mappedVariant = 'success';
  if(variant?.toLowerCase() === 'medium') mappedVariant = 'warning';
  if(variant?.toLowerCase() === 'high') mappedVariant = 'danger';
  if(variant?.toLowerCase() === 'critical') mappedVariant = 'critical';

  return (
    <span
      className={cn(baseStyles, variants[mappedVariant] || variants.default, className)}
      {...props}
    >
      {children}
    </span>
  );
};
