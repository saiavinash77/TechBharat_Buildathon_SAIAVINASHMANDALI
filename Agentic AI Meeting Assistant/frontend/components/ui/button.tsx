import { cn } from "@/lib/utils"

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'success' | 'error' | 'outline' | 'ghost'
  size?: 'default' | 'sm' | 'lg' | 'icon'
}

export function Button({ className, variant = 'primary', size = 'default', ...props }: ButtonProps) {
  const variantStyles = {
    primary: 'bg-primary text-white hover:opacity-90',
    success: 'bg-success text-white hover:opacity-90',
    error: 'bg-error text-white hover:opacity-90',
    outline: 'border border-border bg-surface text-text-primary hover:bg-background',
    ghost: 'hover:bg-background/80 text-text-primary',
  }

  const sizeStyles = {
    default: 'px-5 py-2.5 text-sm',
    sm: 'px-4 py-2 text-xs',
    lg: 'px-8 py-3 text-base',
    icon: 'p-2',
  }

  return (
    <button
      className={cn(
        "inline-flex items-center justify-center rounded-md font-medium transition-all active:scale-95 disabled:opacity-50 disabled:pointer-events-none",
        variantStyles[variant],
        sizeStyles[size],
        className
      )}
      {...props}
    />
  )
}
