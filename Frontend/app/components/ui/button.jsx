import * as React from "react"
import { Slot } from "@radix-ui/react-slot"

export const Button = React.forwardRef(({ className, variant, asChild = false, ...props }, ref) => {
  const Comp = asChild ? Slot : "button"
  
  // Define variant styles based on tailwind config theme
  let variantClass = "bg-ink text-white hover:bg-ink/90"
  if (variant === "outline") {
    variantClass = "border border-line bg-card hover:bg-secondary text-ink"
  } else if (variant === "ghost") {
    variantClass = "hover:bg-secondary text-ink-muted hover:text-ink"
  } else if (variant === "link") {
    variantClass = "text-brand underline-offset-4 hover:underline"
  }
  
  return (
    <Comp
      ref={ref}
      className={`inline-flex items-center justify-center font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand/40 disabled:pointer-events-none disabled:opacity-50 ${variantClass} ${className || ""}`}
      {...props}
    />
  )
})
Button.displayName = "Button"
